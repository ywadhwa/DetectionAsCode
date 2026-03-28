#!/usr/bin/env python3
"""Optional advanced KQL validation using Kusto.Language.dll via pythonnet."""
from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import time
from collections import UserDict
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.schemas.results import build_result
from dac.services.artifacts import write_result_artifact
from dac.services.paths import artifacts_dir, repo_root


LOGGER = logging.getLogger("validate_kql_advanced")


class CaseInsensitiveDict(UserDict):
    """Dictionary that normalizes nested mapping keys to lower case."""

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(str(key).lower(), self.to_case_insensitive(value))

    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(str(key).lower())

    def __contains__(self, key: object) -> bool:
        return super().__contains__(str(key).lower())

    def get(self, key: str, default: Any = None) -> Any:
        return super().get(str(key).lower(), default)

    def update(self, other: Any = None, **kwargs: Any) -> None:
        if other:
            if hasattr(other, "keys"):
                for k in other:
                    self[k] = other[k]
            else:
                for k, v in other:
                    self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    @staticmethod
    def to_case_insensitive(obj: Any) -> Any:
        if isinstance(obj, dict) and not isinstance(obj, CaseInsensitiveDict):
            return CaseInsensitiveDict(obj)
        if isinstance(obj, list):
            return [CaseInsensitiveDict.to_case_insensitive(item) for item in obj]
        return obj


def normalize_type(type_name: str) -> str:
    """Normalize manifest scalar type names to Kusto.Language symbols."""
    return str(type_name).lower().replace("bigint", "long").replace("uri", "string").replace(" ", "")


def load_clr_runtime() -> Tuple[Any, Any]:
    """Load pythonnet and initialize .NET Core runtime lazily."""
    try:
        import pythonnet  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "pythonnet is not installed. Install it separately to use advanced KQL validation."
        ) from exc

    pythonnet.set_runtime("coreclr")
    import clr  # type: ignore
    from System import Reflection  # type: ignore

    clr.AddReference("System.Collections")
    return clr, Reflection


def extract_manifests(reflection: Any, services_dll_path: Path, output_folder: Path) -> None:
    """Extract embedded JSON schema resources from the services DLL."""
    LOGGER.info("Extracting manifests from %s", services_dll_path)
    assembly = reflection.Assembly.LoadFile(str(services_dll_path.resolve()))
    resource_names = assembly.GetManifestResourceNames()

    for resource_name in resource_names:
        if not str(resource_name).endswith(".json"):
            continue

        stream = assembly.GetManifestResourceStream(resource_name)
        if stream is None:
            continue

        try:
            from System.IO import StreamReader  # type: ignore

            reader = StreamReader(stream)
            try:
                content = reader.ReadToEnd()
            finally:
                reader.Close()
        finally:
            stream.Close()

        parts = str(resource_name).split(".")
        if len(parts) < 6:
            LOGGER.warning("Skipping resource with unexpected name: %s", resource_name)
            continue

        parent_folder = parts[4]
        filename = ".".join(parts[5:])
        manifest_folder = output_folder / parent_folder
        manifest_folder.mkdir(parents=True, exist_ok=True)
        (manifest_folder / filename).write_text(content, encoding="utf-8")


def to_column_symbol(column: Dict[str, Any], scalar_types: Any) -> Any:
    """Map one manifest column into a Kusto column symbol."""
    from Kusto.Language.Symbols import ColumnSymbol  # type: ignore

    scalar_type = scalar_types.GetSymbol(normalize_type(column["Type"])) or scalar_types.Unknown
    return ColumnSymbol(column["Name"], scalar_type, column.get("description", None))


def add_common_columns(schema: Dict[str, Any]) -> None:
    """Inject columns that are assumed by many Sentinel manifests."""
    properties = schema.setdefault("Properties", [])
    properties.append({"Name": "Type", "Type": "String"})
    if schema.get("IsResourceCentric", False) and not any(p.get("Name") == "_ResourceId" for p in properties):
        properties.append({"Name": "_ResourceId", "Type": "String"})


def create_table_symbol(schema: Dict[str, Any], scalar_types: Any) -> Any:
    """Create a TableSymbol from one table manifest schema."""
    from Kusto.Language.Symbols import ColumnSymbol, TableSymbol  # type: ignore
    from System.Collections.Generic import List  # type: ignore

    columns = List[ColumnSymbol]()
    for column in schema["Properties"]:
        columns.Add(to_column_symbol(column, scalar_types))
    return TableSymbol(schema["Name"], columns, schema.get("description", None))


def create_function_symbol(schema: Dict[str, Any], scalar_types: Any) -> Any:
    """Create a FunctionSymbol from one function manifest schema."""
    from Kusto.Language.Symbols import ArgumentKind, ColumnSymbol, FunctionSymbol, Parameter, TableSymbol  # type: ignore
    from System.Collections.Generic import List  # type: ignore

    parameters = List[Parameter]()
    result_columns = List[ColumnSymbol]()

    for param in schema.get("FunctionParameters", []):
        scalar_type = scalar_types.GetSymbol(normalize_type(param["Type"])) or scalar_types.Unknown
        parameters.Add(Parameter(param["Name"], scalar_type, ArgumentKind.Literal, param.get("description", None)))

    if not schema.get("FunctionResultColumns") and schema.get("Query"):
        return FunctionSymbol(schema["FunctionName"], schema["Query"], parameters, None)

    for column in schema.get("FunctionResultColumns", []):
        result_columns.Add(to_column_symbol(column, scalar_types))

    return FunctionSymbol(schema["FunctionName"], TableSymbol(result_columns), parameters, None)


def build_global_state_from_manifests(manifests_dir: Path) -> Any:
    """Construct a Kusto GlobalState from extracted JSON manifests."""
    from Kusto.Language import GlobalState  # type: ignore
    from Kusto.Language.Symbols import DatabaseSymbol, ScalarTypes, Symbol  # type: ignore
    from System.Collections.Generic import List  # type: ignore

    symbols = List[Symbol]()
    for file_path in sorted(manifests_dir.rglob("*.json")):
        try:
            schema = CaseInsensitiveDict(json.loads(file_path.read_text(encoding="utf-8")))
            if "properties" in schema:
                add_common_columns(schema)
                symbols.Add(create_table_symbol(schema, ScalarTypes))
            elif "functionparameters" in schema:
                symbols.Add(create_function_symbol(schema, ScalarTypes))
        except Exception as exc:
            LOGGER.warning("Skipping manifest %s: %s", file_path, exc)

    database_symbol = DatabaseSymbol("default", symbols)
    return GlobalState.Default.WithDatabase(database_symbol)


def collect_query_files(*, directory: str, query: str | None = None) -> List[Path]:
    """Return `.kql` files from a directory or one explicit query file."""
    rr = repo_root()
    if query:
        path = (rr / query).resolve() if not Path(query).is_absolute() else Path(query).resolve()
        return [path]
    query_dir = (rr / directory).resolve()
    return sorted(query_dir.rglob("*.kql"))


def validate_queries_advanced(
    *,
    kusto_dll: str,
    services_dll: str,
    directory: str = "output/kql",
    query: str | None = None,
    manifests_dir: str | None = None,
    artifact_output: str | None = None,
    keep_manifests: bool = False,
) -> Dict[str, Any]:
    """Validate KQL queries with Kusto.Language and emit a structured result."""
    start = time.monotonic()
    rr = repo_root()

    try:
        clr, reflection = load_clr_runtime()
    except RuntimeError as exc:
        result = build_result(status="failure", stage="validation", backend="kql", errors=[str(exc)])
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "validation-kql-advanced.json"
        write_result_artifact(result, out)
        return result

    kusto_dll_path = Path(kusto_dll).expanduser().resolve()
    services_dll_path = Path(services_dll).expanduser().resolve()
    for dll_path, label in ((kusto_dll_path, "Kusto.Language.dll"), (services_dll_path, "services DLL")):
        if not dll_path.exists():
            result = build_result(
                status="failure",
                stage="validation",
                backend="kql",
                errors=[f"{label} not found: {dll_path}"],
            )
            out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "validation-kql-advanced.json"
            write_result_artifact(result, out)
            return result

    temp_dir_obj = None
    if manifests_dir:
        manifest_root = Path(manifests_dir).expanduser().resolve()
        manifest_root.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="dac-kql-manifests-")
        manifest_root = Path(temp_dir_obj.name)

    failures: List[Dict[str, Any]] = []
    warnings: List[str] = []
    query_files = collect_query_files(directory=directory, query=query)
    if not query_files:
        result = build_result(
            status="success",
            stage="validation",
            backend="kql",
            warnings=["No KQL query files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "files_checked": 0},
            context={"directory": directory, "query": query},
        )
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "validation-kql-advanced.json"
        write_result_artifact(result, out)
        return result

    try:
        clr.AddReference(str(kusto_dll_path))
        reflection.Assembly.LoadFile(str(kusto_dll_path))
        extract_manifests(reflection, services_dll_path, manifest_root)
        global_state = build_global_state_from_manifests(manifest_root)
        from Kusto.Language import KustoCode  # type: ignore

        diagnostics_total = 0
        for file_path in query_files:
            try:
                query_text = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                failures.append({"file": str(file_path), "errors": [f"Failed to read file: {exc}"]})
                continue

            if not query_text.strip():
                failures.append({"file": str(file_path), "errors": ["Query is empty"]})
                continue

            code = KustoCode.ParseAndAnalyze(query_text, global_state)
            diagnostics = code.GetDiagnostics()
            file_errors: List[str] = []
            file_warnings: List[str] = []
            for diagnostic in diagnostics:
                severity = str(diagnostic.Severity)
                snippet_start = max(int(diagnostic.Start) - 15, 0)
                snippet_end = min(int(diagnostic.End) + 15, len(query_text))
                snippet = query_text[snippet_start:snippet_end].replace("\r", " ").replace("\n", " ")
                message = f"{severity}: {diagnostic.Message} [{diagnostic.Start}-{diagnostic.End}] near '{snippet}'"
                diagnostics_total += 1
                if severity.lower() == "error":
                    file_errors.append(message)
                else:
                    file_warnings.append(f"{file_path}: {message}")

            warnings.extend(file_warnings)
            if file_errors:
                failures.append({"file": str(file_path), "errors": file_errors})

        result = build_result(
            status="failure" if failures else "success",
            stage="validation",
            backend="kql",
            errors=[f"{item['file']}: {'; '.join(item['errors'])}" for item in failures],
            warnings=warnings,
            metrics={
                "duration_ms": int((time.monotonic() - start) * 1000),
                "files_checked": len(query_files),
                "failed_files": len(failures),
                "diagnostics_count": diagnostics_total,
            },
            artifacts={"manifests_dir": str(manifest_root)},
            context={
                "directory": str((rr / directory).resolve()) if not query else None,
                "query": str(query) if query else None,
                "kusto_dll": str(kusto_dll_path),
                "services_dll": str(services_dll_path),
            },
        )
    finally:
        if temp_dir_obj is not None and not keep_manifests:
            temp_dir_obj.cleanup()

    out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "validation-kql-advanced.json"
    write_result_artifact(result, out)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional advanced KQL validation using Kusto.Language.dll")
    parser.add_argument("--directory", default="output/kql", help="Directory containing .kql files")
    parser.add_argument("--query", help="Validate a specific .kql file")
    parser.add_argument("--kusto-dll", required=True, help="Path to Kusto.Language.dll")
    parser.add_argument(
        "--services-dll",
        required=True,
        help="Path to Microsoft.Azure.Sentinel.KustoServices.dll or equivalent manifest-bearing DLL",
    )
    parser.add_argument("--manifests-dir", help="Directory to extract schema manifests into")
    parser.add_argument("--keep-manifests", action="store_true", help="Keep extracted manifests when using a temp dir")
    parser.add_argument("--artifact-output", help="Optional path for structured JSON artifact")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    result = validate_queries_advanced(
        kusto_dll=args.kusto_dll,
        services_dll=args.services_dll,
        directory=args.directory,
        query=args.query,
        manifests_dir=args.manifests_dir,
        artifact_output=args.artifact_output,
        keep_manifests=args.keep_manifests,
    )

    print(f"Status       : {result.get('status')}")
    print(f"Files checked: {result.get('metrics', {}).get('files_checked', 0)}")
    print(f"Failed       : {result.get('metrics', {}).get('failed_files', 0)}")
    print(f"Diagnostics  : {result.get('metrics', {}).get('diagnostics_count', 0)}")

    if result.get("warnings"):
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    if result.get("errors"):
        print("\nFailed queries:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()

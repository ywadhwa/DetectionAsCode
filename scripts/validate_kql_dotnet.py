#!/usr/bin/env python3
"""Validate KQL queries using Kusto.Language .NET assemblies via pythonnet."""
import argparse
import json
import logging
import os
import re
import sys
from collections import UserDict
from pathlib import Path
from typing import List

import pythonnet

pythonnet.set_runtime("coreclr")
import clr
from System import Reflection
from System.IO import StreamReader
from System.Collections.Generic import List as DotNetList

clr.AddReference("System.Collections")


class CaseInsensitiveDict(UserDict):
    """Custom dictionary class that handles case-insensitive keys"""

    def __init__(self, data=None, **kwargs):
        super().__init__()
        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def __setitem__(self, key, value):
        key = key.lower()
        super().__setitem__(key, self.to_case_insensitive(value))

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __delitem__(self, key):
        super().__delitem__(key.lower())

    def __contains__(self, key):
        return super().__contains__(key.lower())

    def get(self, key, default=None):
        return super().get(key.lower(), default)

    def update(self, other=None, **kwargs):
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
    def to_case_insensitive(obj):
        """Recursively convert nested dicts/lists to case-insensitive dicts."""
        if isinstance(obj, dict) and not isinstance(obj, CaseInsensitiveDict):
            return CaseInsensitiveDict(obj)
        if isinstance(obj, list):
            return [CaseInsensitiveDict.to_case_insensitive(item) for item in obj]
        return obj


def extract_manifests(kusto_services_dll_path: str, output_folder: str) -> None:
    logging.info(f"Extracting manifests from {kusto_services_dll_path}")

    assembly = Reflection.Assembly.LoadFile(kusto_services_dll_path)
    resource_names = assembly.GetManifestResourceNames()

    for resource_name in resource_names:
        if resource_name.endswith(".json"):
            stream = assembly.GetManifestResourceStream(resource_name)
            reader = StreamReader(stream)
            content = reader.ReadToEnd()
            reader.Close()
            stream.Close()

            parts = resource_name.split(".")
            if len(parts) < 6:
                logging.warning(f"Skipping resource: {resource_name}")
                continue

            parent_folder = parts[4]
            filename = ".".join(parts[5:])
            manifest_folder = os.path.join(output_folder, parent_folder)

            if not os.path.exists(manifest_folder):
                os.makedirs(manifest_folder)

            manifest_path = os.path.join(manifest_folder, filename)
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(content)

    logging.info("Manifest extraction complete.")


def normalize_type(value: str) -> str:
    return value.lower().replace("bigint", "long").replace("uri", "string").replace(" ", "")


def to_column_symbol(column, ScalarTypes):
    from Kusto.Language.Symbols import ColumnSymbol

    scalar_type = ScalarTypes.GetSymbol(normalize_type(column["Type"])) or ScalarTypes.Unknown
    return ColumnSymbol(column["Name"], scalar_type, column.get("description", None))


def create_table_symbol(schema: dict, ScalarTypes):
    from Kusto.Language.Symbols import TableSymbol, ColumnSymbol

    column_symbols = DotNetList[ColumnSymbol]()
    for column in schema["Properties"]:
        column_symbols.Add(to_column_symbol(column, ScalarTypes))
    return TableSymbol(schema["Name"], column_symbols, schema.get("description", None))


def create_function_symbol(schema: dict, ScalarTypes):
    from Kusto.Language.Symbols import Parameter, ArgumentKind, FunctionSymbol, TableSymbol, ColumnSymbol

    parameter_list = DotNetList[Parameter]()
    column_symbols = DotNetList[ColumnSymbol]()

    for param in schema.get("FunctionParameters", []):
        scalar_type = ScalarTypes.GetSymbol(normalize_type(param["Type"])) or ScalarTypes.Unknown
        parameter_list.Add(
            Parameter(
                param["Name"],
                scalar_type,
                ArgumentKind.Literal,
                param.get("description", None),
            )
        )

    if not schema.get("FunctionResultColumns") and schema.get("Query"):
        return FunctionSymbol(schema["FunctionName"], schema["Query"], parameter_list, None)

    for column in schema.get("FunctionResultColumns", []):
        column_symbols.Add(to_column_symbol(column, ScalarTypes))

    return FunctionSymbol(schema["FunctionName"], TableSymbol(column_symbols), parameter_list, None)


def add_common_columns(schema: dict):
    schema["Properties"].append({"Name": "Type", "Type": "String"})
    if schema.get("IsResourceCentric", False):
        has_resource_id = any(p["Name"] == "_ResourceId" for p in schema["Properties"])
        if not has_resource_id:
            schema["Properties"].append({"Name": "_ResourceId", "Type": "String"})


def build_global_state_from_manifests(manifests_dir: str):
    from Kusto.Language import GlobalState
    from Kusto.Language.Symbols import ScalarTypes, Symbol, DatabaseSymbol

    symbols = DotNetList[Symbol]()

    for root, _, files in os.walk(manifests_dir):
        for file in files:
            if file.endswith(".json"):
                try:
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        schema = json.load(f)
                        schema = CaseInsensitiveDict(schema)
                    if "Properties" in schema:
                        add_common_columns(schema)
                        symbols.Add(create_table_symbol(schema, ScalarTypes))
                    elif "FunctionParameters" in schema:
                        symbols.Add(create_function_symbol(schema, ScalarTypes))
                except Exception as exc:
                    logging.error(f"Exception {str(exc)}")

    db_symbol = DatabaseSymbol("default", symbols)
    return GlobalState.Default.WithDatabase(db_symbol)


def load_query(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("properties", {}).get("query", "")
    return path.read_text(encoding="utf-8")


def validate(kusto_dll_path: str, files_dir: str, file_regex: str, manifests_dir: str) -> None:
    logging.info(f"Loading {kusto_dll_path}")
    Reflection.Assembly.LoadFile(kusto_dll_path)

    from Kusto.Language import KustoCode

    logging.info(f"Building GlobalState from manifests at {manifests_dir}")
    global_state = build_global_state_from_manifests(manifests_dir)

    matched_files: List[str] = []
    pattern = re.compile(file_regex)
    for root, _, files in os.walk(files_dir):
        for file in files:
            full_path = os.path.join(root, file)
            if pattern.search(file):
                matched_files.append(full_path)

    if not matched_files:
        logging.error("No files found to validate matching regex.")
        sys.exit(1)

    has_errors = False
    for file_path in matched_files:
        try:
            query = load_query(file_path)
            if not query.strip():
                logging.error(f"No query found in {file_path}")
                has_errors = True
                continue

            code = KustoCode.ParseAndAnalyze(query, global_state)
            diagnostics = code.GetDiagnostics()

            if diagnostics.Count == 0:
                logging.info(f"[PASS] {file_path}")
            else:
                logging.warning(f"[FAIL] {file_path} - {diagnostics.Count} issue(s)")
                for msg in diagnostics:
                    segment_start = max(msg.Start - 15, 0)
                    segment_end = min(msg.End + 15, len(query))
                    segment = "..." + query.replace("\r", "").replace("\n", "")[segment_start:segment_end] + "..."
                    logging.error(
                        f"- {msg.Severity}: {msg.Message} [{msg.Start}-{msg.End}] -> '{segment}'"
                    )
                    if str(msg.Severity) == "Error":
                        has_errors = True

        except Exception as exc:
            has_errors = True
            logging.error(f"{file_path} -> {str(exc)}")

    if has_errors:
        logging.error("Errors while validating KQL queries in files!")
        sys.exit(1)

    logging.info("All files KQL queries validated successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate KQL using Kusto.Language.dll")
    parser.add_argument("--kusto-dll", required=True, help="Path to Kusto.Language.dll")
    parser.add_argument("--services-dll", required=True, help="Path to Microsoft.Azure.Sentinel.KustoServices.dll")
    parser.add_argument("--file-dir", required=True, help="Directory containing files to validate")
    parser.add_argument("--file-regex-filter", required=False, default=r".*\\.(json|kql)$", help="Regex to filter filenames")
    parser.add_argument("--manifests-dir", required=False, default="manifests", help="Where to extract manifests")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    extract_manifests(args.services_dll, args.manifests_dir)
    validate(args.kusto_dll, args.file_dir, args.file_regex_filter, args.manifests_dir)


if __name__ == "__main__":
    main()

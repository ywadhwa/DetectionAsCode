"""Azure Data Explorer backend adapter for KQL compile and execution stages."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


KUSTO_SCOPE = "https://kusto.kusto.windows.net/.default"
KUSTO_RESOURCE = "https://kusto.kusto.windows.net"


@dataclass
class AdxConfig:
    """ADX connection configuration sourced from environment or CLI."""

    cluster_uri: str
    database: str
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token: Optional[str] = None
    use_managed_identity: bool = False
    timeout_seconds: int = 30
    row_limit: int = 1000
    sample_row_limit: int = 5

    @classmethod
    def from_env(cls) -> "AdxConfig":
        """Build config from environment variables for CI-friendly use."""
        return cls(
            cluster_uri=os.getenv("KUSTO_CLUSTER", os.getenv("ADX_CLUSTER_URI", "")),
            database=os.getenv("KUSTO_DATABASE", os.getenv("ADX_DATABASE", "")),
            tenant_id=os.getenv("KUSTO_TENANT_ID", os.getenv("AZURE_TENANT_ID")),
            client_id=os.getenv("KUSTO_CLIENT_ID", os.getenv("AZURE_CLIENT_ID")),
            client_secret=os.getenv("KUSTO_CLIENT_SECRET", os.getenv("AZURE_CLIENT_SECRET")),
            token=os.getenv("KUSTO_TOKEN", os.getenv("ADX_TOKEN")),
            use_managed_identity=os.getenv("KUSTO_USE_MANAGED_IDENTITY", "false").lower() in {"1", "true", "yes"},
            timeout_seconds=int(os.getenv("KUSTO_QUERY_TIMEOUT", "30")),
            row_limit=int(os.getenv("KUSTO_ROW_LIMIT", "1000")),
            sample_row_limit=int(os.getenv("KUSTO_SAMPLE_ROWS", "5")),
        )


class AdxAuthError(RuntimeError):
    """Raised when ADX auth cannot be completed."""


class AdxQueryError(RuntimeError):
    """Raised when ADX query request fails."""


def _request_client_credential_token(config: AdxConfig) -> str:
    if not (config.tenant_id and config.client_id and config.client_secret):
        raise AdxAuthError("tenant_id/client_id/client_secret are required for client credential auth")

    token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
    resp = requests.post(
        token_url,
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "grant_type": "client_credentials",
            "scope": KUSTO_SCOPE,
        },
        timeout=config.timeout_seconds,
    )
    try:
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AdxAuthError(f"Client credential token request failed: {exc}") from exc

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise AdxAuthError("AAD response missing access_token")
    return token


def _request_managed_identity_token(config: AdxConfig) -> str:
    identity_endpoint = os.getenv("IDENTITY_ENDPOINT")
    identity_header = os.getenv("IDENTITY_HEADER")

    if identity_endpoint and identity_header:
        params = {"resource": KUSTO_RESOURCE, "api-version": "2019-08-01"}
        if config.client_id:
            params["client_id"] = config.client_id
        resp = requests.get(
            identity_endpoint,
            params=params,
            headers={"X-IDENTITY-HEADER": identity_header},
            timeout=config.timeout_seconds,
        )
    else:
        params = {
            "resource": KUSTO_RESOURCE,
            "api-version": "2018-02-01",
        }
        if config.client_id:
            params["client_id"] = config.client_id
        resp = requests.get(
            "http://169.254.169.254/metadata/identity/oauth2/token",
            params=params,
            headers={"Metadata": "true"},
            timeout=config.timeout_seconds,
        )

    try:
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise AdxAuthError(f"Managed identity token request failed: {exc}") from exc

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise AdxAuthError("Managed identity response missing access_token")
    return token


def get_access_token(config: AdxConfig) -> str:
    """Resolve an ADX token from explicit token, app auth, or managed identity."""
    if config.token:
        return config.token
    if config.use_managed_identity:
        return _request_managed_identity_token(config)
    if config.tenant_id and config.client_id and config.client_secret:
        return _request_client_credential_token(config)
    raise AdxAuthError(
        "ADX auth is not configured. Provide token or tenant/client/secret or managed identity settings."
    )


def _shape_rows(result_json: Dict[str, Any], sample_row_limit: int) -> Tuple[int, List[Dict[str, Any]]]:
    primary = next((t for t in result_json.get("tables", []) if t.get("name") == "PrimaryResult"), None)
    if not primary:
        return 0, []
    columns = [c.get("name") for c in primary.get("columns", [])]
    rows = primary.get("rows", [])

    sample: List[Dict[str, Any]] = []
    for row in rows[: max(sample_row_limit, 0)]:
        if isinstance(row, list):
            sample.append({columns[i]: row[i] for i in range(min(len(columns), len(row)))})
    return len(rows), sample


def execute_query_raw(
    *,
    query_text: str,
    config: AdxConfig,
    row_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute query via ADX REST endpoint and return raw JSON response."""
    token = get_access_token(config)
    limit = config.row_limit if row_limit is None else row_limit
    csl = query_text.strip()
    if limit >= 0:
        csl = f"{csl}\n| take {limit}"

    url = f"{config.cluster_uri.rstrip('/')}/v1/rest/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"db": config.database, "csl": csl}

    resp = requests.post(url, headers=headers, json=payload, timeout=config.timeout_seconds)
    try:
        resp.raise_for_status()
    except requests.RequestException as exc:
        details = resp.text.strip() if resp.text else str(exc)
        raise AdxQueryError(details) from exc

    return resp.json()


def validate_kql_query(query_text: str, config: AdxConfig, mode: str = "compile") -> Dict[str, Any]:
    """Compile/validate KQL against ADX using low-impact execution checks."""
    start = time.monotonic()

    # NOTE: keep result schema fields stable for pipeline artifact consumers.
    # ADX does not expose a simple dedicated compile endpoint in this repo today,
    # so compile mode executes with strict low row limit to force parser/binder validation.
    compile_limit = 0 if mode == "compile" else config.row_limit

    try:
        raw = execute_query_raw(query_text=query_text, config=config, row_limit=compile_limit)
        row_count, sample_rows = _shape_rows(raw, config.sample_row_limit if mode == "execute" else 0)
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "success",
            "stage": "compile" if mode == "compile" else "validation",
            "backend": "adx",
            "errors": [],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": row_count},
            "context": {
                "cluster_uri": config.cluster_uri,
                "database": config.database,
                "mode": mode,
            },
            "result": {
                "sample_rows": sample_rows,
                "raw": raw,
            },
        }
    except (AdxAuthError, AdxQueryError) as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "failure",
            "stage": "compile" if mode == "compile" else "validation",
            "backend": "adx",
            "errors": [str(exc)],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": 0},
            "context": {
                "cluster_uri": config.cluster_uri,
                "database": config.database,
                "mode": mode,
            },
            "result": {"sample_rows": [], "raw": {}},
        }


def run_kql_query(query_text: str, config: AdxConfig, timeout: Optional[int] = None, row_limit: Optional[int] = None) -> Dict[str, Any]:
    """Execute KQL against ADX and return structured result."""
    if timeout is not None:
        config = AdxConfig(**{**config.__dict__, "timeout_seconds": timeout})
    start = time.monotonic()

    try:
        raw = execute_query_raw(query_text=query_text, config=config, row_limit=row_limit)
        row_count, sample_rows = _shape_rows(raw, config.sample_row_limit)
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "success",
            "stage": "execution",
            "backend": "adx",
            "errors": [],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": row_count},
            "context": {
                "cluster_uri": config.cluster_uri,
                "database": config.database,
                "mode": "execute",
                "timeout_seconds": config.timeout_seconds,
                "row_limit": row_limit if row_limit is not None else config.row_limit,
            },
            "result": {
                "sample_rows": sample_rows,
                "raw": raw,
            },
        }
    except (AdxAuthError, AdxQueryError) as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "failure",
            "stage": "execution",
            "backend": "adx",
            "errors": [str(exc)],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": 0},
            "context": {
                "cluster_uri": config.cluster_uri,
                "database": config.database,
                "mode": "execute",
                "timeout_seconds": config.timeout_seconds,
                "row_limit": row_limit if row_limit is not None else config.row_limit,
            },
            "result": {"sample_rows": [], "raw": {}},
        }


def summarize_kql_results(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact KQL summary suitable for CI logs and orchestration metadata."""
    return {
        "status": result.get("status"),
        "stage": result.get("stage"),
        "backend": result.get("backend", "adx"),
        "row_count": result.get("metrics", {}).get("row_count", 0),
        "duration_ms": result.get("metrics", {}).get("duration_ms", 0),
        "errors": result.get("errors", []),
    }

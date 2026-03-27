"""Elasticsearch backend adapter for Lucene query compile and execution stages."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from elasticsearch import Elasticsearch


@dataclass
class ElasticConfig:
    """Elasticsearch connection configuration sourced from environment or CLI."""

    host: str
    index: str
    timeout_seconds: int = 30
    row_limit: int = 1000
    sample_row_limit: int = 5
    api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ElasticConfig":
        """Build config from environment variables for CI-friendly use."""
        return cls(
            host=os.getenv("ELASTIC_HOST", "http://localhost:9200"),
            index=os.getenv("ELASTIC_INDEX", "dfir-json-*"),
            timeout_seconds=int(os.getenv("ELASTIC_TIMEOUT", "30")),
            row_limit=int(os.getenv("ELASTIC_ROW_LIMIT", "1000")),
            sample_row_limit=int(os.getenv("ELASTIC_SAMPLE_ROWS", "5")),
            api_key=os.getenv("ELASTIC_API_KEY") or None,
        )


class ElasticQueryError(RuntimeError):
    """Raised when an Elasticsearch query request fails."""


def _build_client(config: ElasticConfig) -> Elasticsearch:
    """Construct an Elasticsearch client from config."""
    kwargs: Dict[str, Any] = {
        "hosts": [config.host],
        "request_timeout": config.timeout_seconds,
    }
    if config.api_key:
        kwargs["api_key"] = config.api_key
    return Elasticsearch(**kwargs)


def _shape_rows(hits: List[Dict[str, Any]], sample_row_limit: int) -> Tuple[int, List[Dict[str, Any]]]:
    """Extract total hit count and a capped sample of _source documents."""
    sample: List[Dict[str, Any]] = []
    for hit in hits[: max(sample_row_limit, 0)]:
        source = hit.get("_source", {})
        sample.append(source)
    return len(hits), sample


def execute_query(
    *,
    query_text: str,
    config: ElasticConfig,
    size: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a Lucene query_string search and return the raw ES response body."""
    client = _build_client(config)
    limit = config.row_limit if size is None else size

    body: Dict[str, Any] = {
        "query": {"query_string": {"query": query_text}},
        "size": limit,
    }

    try:
        resp = client.search(index=config.index, body=body)
    except Exception as exc:
        raise ElasticQueryError(str(exc)) from exc

    return dict(resp)


def validate_elastic_query(
    query_text: str,
    config: ElasticConfig,
    mode: str = "compile",
) -> Dict[str, Any]:
    """Compile/validate a Lucene query against Elasticsearch.

    In compile mode the query runs with size=0 so no documents are returned,
    but the cluster still parses and validates the query DSL.
    """
    start = time.monotonic()
    compile_size = 0 if mode == "compile" else config.row_limit

    try:
        raw = execute_query(query_text=query_text, config=config, size=compile_size)
        hits = raw.get("hits", {}).get("hits", [])
        total_value = raw.get("hits", {}).get("total", {})
        row_count = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value)
        _, sample_rows = _shape_rows(hits, config.sample_row_limit if mode == "execute" else 0)
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "success",
            "stage": "compile" if mode == "compile" else "validation",
            "backend": "elasticsearch",
            "errors": [],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": row_count},
            "context": {
                "host": config.host,
                "index": config.index,
                "mode": mode,
            },
            "result": {
                "sample_rows": sample_rows,
                "raw": raw,
            },
        }
    except ElasticQueryError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "failure",
            "stage": "compile" if mode == "compile" else "validation",
            "backend": "elasticsearch",
            "errors": [str(exc)],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": 0},
            "context": {
                "host": config.host,
                "index": config.index,
                "mode": mode,
            },
            "result": {"sample_rows": [], "raw": {}},
        }


def run_elastic_query(
    query_text: str,
    config: ElasticConfig,
    timeout: Optional[int] = None,
    row_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a Lucene query against Elasticsearch and return a structured result."""
    if timeout is not None:
        config = ElasticConfig(**{**config.__dict__, "timeout_seconds": timeout})
    start = time.monotonic()

    try:
        raw = execute_query(query_text=query_text, config=config, size=row_limit)
        hits = raw.get("hits", {}).get("hits", [])
        total_value = raw.get("hits", {}).get("total", {})
        row_count = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value)
        _, sample_rows = _shape_rows(hits, config.sample_row_limit)
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "success",
            "stage": "execution",
            "backend": "elasticsearch",
            "errors": [],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": row_count},
            "context": {
                "host": config.host,
                "index": config.index,
                "mode": "execute",
                "timeout_seconds": config.timeout_seconds,
                "row_limit": row_limit if row_limit is not None else config.row_limit,
            },
            "result": {
                "sample_rows": sample_rows,
                "raw": raw,
            },
        }
    except ElasticQueryError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "failure",
            "stage": "execution",
            "backend": "elasticsearch",
            "errors": [str(exc)],
            "warnings": [],
            "metrics": {"duration_ms": duration_ms, "row_count": 0},
            "context": {
                "host": config.host,
                "index": config.index,
                "mode": "execute",
                "timeout_seconds": config.timeout_seconds,
                "row_limit": row_limit if row_limit is not None else config.row_limit,
            },
            "result": {"sample_rows": [], "raw": {}},
        }


def summarize_elastic_results(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact Elasticsearch summary suitable for CI logs."""
    return {
        "status": result.get("status"),
        "stage": result.get("stage"),
        "backend": result.get("backend", "elasticsearch"),
        "row_count": result.get("metrics", {}).get("row_count", 0),
        "duration_ms": result.get("metrics", {}).get("duration_ms", 0),
        "errors": result.get("errors", []),
    }

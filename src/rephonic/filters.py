"""Filter encoding for the ``filters`` parameter on search endpoints.

The API expects a comma-separated string of ``field:operator:value`` clauses
(see https://rephonic.com/developers/search-filters). This module encodes
user-friendly Python forms into that wire format:

- **Stripe-style dict** — primary form: ``{"listeners": {"gte": 5000}, "active": True}``
- **list of strings** — raw clauses: ``["listeners:gte:5000", "active:is:true"]``
- **string** — legacy raw DSL: ``"listeners:gte:5000,active:is:true"``

The dict form mirrors the API's operator names exactly. In particular, ``in``
means the field must contain **all** of the given values (intersection), not
SQL-style membership. Use ``any`` for union / OR semantics.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Union

FilterSpec = Union[None, str, "list[str]", Mapping[str, Any]]
"""Accepted type for the ``filters`` parameter on search endpoints."""

_RESERVED = "-,:\\"


def encode_filters(filters: FilterSpec) -> str | None:
    """Encode filters into the comma-separated string the API expects.

    Returns ``None`` for an empty / missing input so callers can omit the
    query param entirely.
    """
    if filters is None:
        return None
    if isinstance(filters, str):
        return filters or None
    if isinstance(filters, list):
        return _encode_string_list(filters)
    if isinstance(filters, Mapping):
        return _encode_mapping(filters)
    raise TypeError(
        f"filters must be str, list, dict, or None; got {type(filters).__name__}"
    )


def _encode_string_list(items: list[Any]) -> str | None:
    if not items:
        return None
    for item in items:
        if not isinstance(item, str):
            raise TypeError(
                f"filter list items must be str; got {type(item).__name__}"
            )
    return ",".join(items)


def _encode_mapping(spec: Mapping[str, Any]) -> str | None:
    clauses: list[str] = []
    for field, value in spec.items():
        clauses.extend(_encode_field(field, value))
    return ",".join(clauses) if clauses else None


def _encode_field(field: str, value: Any) -> list[str]:
    if isinstance(value, bool):
        return [_clause(field, "is", _stringify(value))]
    if isinstance(value, Mapping):
        if not value:
            raise ValueError(f"filter spec for {field!r} is empty")
        return [_clause_for_op(field, op, v) for op, v in value.items()]
    raise TypeError(
        f"filter value for {field!r} must be bool or dict; got {type(value).__name__}"
    )


def _clause_for_op(field: str, op: str, value: Any) -> str:
    if op in ("gte", "lte"):
        return _clause(field, op, _stringify(value))
    if op == "is":
        if not isinstance(value, bool):
            raise TypeError(
                f"{field!r} 'is' operator expects bool; got {type(value).__name__}"
            )
        return _clause(field, op, _stringify(value))
    if op in ("any", "in"):
        if not isinstance(value, (list, tuple)):
            raise TypeError(
                f"{field!r} {op!r} operator expects a list; got {type(value).__name__}"
            )
        if not value:
            raise ValueError(f"{field!r} {op!r} operator expects a non-empty list")
        return _clause(field, op, "-".join(_escape(_stringify(v)) for v in value))
    raise ValueError(f"unknown operator {op!r} for field {field!r}")


def _clause(field: str, op: str, encoded_value: str) -> str:
    return f"{field}:{op}:{encoded_value}"


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _escape(s: str) -> str:
    return "".join("\\" + c if c in _RESERVED else c for c in s)

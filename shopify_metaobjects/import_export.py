"""CSV import/export utilities over MetaobjectClient (optional pandas)."""

from __future__ import annotations

from typing import Any

from shopify_metaobjects.client import MetaobjectClient


def upsert_rows(
    client: MetaobjectClient,
    *,
    metaobject_type: str,
    rows: list[dict[str, Any]],
    handle_key: str = "handle",
) -> dict[str, int]:
    """Upsert dict rows. Each row must include a handle column."""
    stats = {"upserted": 0, "failed": 0}
    for row in rows:
        handle = str(row.get(handle_key) or "").strip()
        if not handle:
            stats["failed"] += 1
            continue
        fields = {k: v for k, v in row.items() if k != handle_key}
        result = client.upsert(
            metaobject_type=metaobject_type,
            handle=handle,
            fields=fields,
        )
        if result.ok:
            stats["upserted"] += 1
        else:
            stats["failed"] += 1
    return stats


def process_csv(
    client: MetaobjectClient,
    *,
    file_path: str,
    metaobject_type: str,
    handle_key: str = "handle",
) -> dict[str, int]:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover
        raise ImportError("CSV support requires: pip install 'shopify-metaobjects[csv]'") from exc

    frame = pd.read_csv(file_path)
    rows = frame.to_dict(orient="records")
    return upsert_rows(
        client,
        metaobject_type=metaobject_type,
        rows=rows,
        handle_key=handle_key,
    )

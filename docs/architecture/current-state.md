# Current state — Shopify_Metaobjects (baseline)

**Date:** 2026-09-14  
**Branch:** `feat/transport-abstraction`  
**Commit inspected:** `main` at clone time

## Layout

| Path | Role |
|------|------|
| `shopify_metaobject_loader.py` | Monolithic implementation (CRUD, upsert, CSV, definitions, HTTP) |
| `shopify_metaobjects/` | Partial package; `loader.py` is a stub; `api.py` owns `requests` |
| `tests/` | Placeholders only; fail without editable install |
| `pyproject.toml` | Build-system only; distribution name in `setup.py`: `shopify-metaobject-loader` |
| `requirements.txt` | `pandas`, `requests` (dotenv/tenacity used but not pinned) |

## Transport coupling (to extract)

- `requests.post` in `api.make_graphql_request` and monolithic `_make_request` / fetch methods
- Constructor args: `shop_domain`, `access_token`, `api_version`
- Headers: `X-Shopify-Access-Token`
- URL: `https://{shop}/admin/api/{version}/graphql.json`
- `dotenv.load_dotenv` in scripts / loader imports
- Retry via `tenacity` around HTTP

## Domain logic to preserve

- `metaobjectUpsert` with `metaobject: { fields: [...] }` (already correct; not `values`)
- Fetch by handle, list/fetch all, CSV process, export
- Definition fetch / describe / create
- `Metaobject` model helpers
- Validation helpers against definitions

## Characterization tests

Existing tests are placeholders (`test_placeholder`). No behavioral suite to freeze; new FakeTransport tests become the baseline.

## Target after refactor

- Core: `MetaobjectClient(transport)` — no `requests`, no tokens
- Optional: `StandaloneShopifyTransport`, `DjangoShopifyTransport`
- Deprecated: `ShopifyMetaobjectLoader` facade → client + standalone transport

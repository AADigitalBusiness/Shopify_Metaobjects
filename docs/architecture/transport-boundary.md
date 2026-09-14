# Transport boundary

## Rule

`MetaobjectClient` speaks GraphQL metaobject operations only. Authentication and HTTP belong to an injected `GraphQLTransport`.

```text
MetaobjectClient
      │
      ▼
GraphQLTransport.execute(query, variables)
      │
      ├── FakeTransport (tests)
      ├── DjangoShopifyTransport → django_shopify.requests.execute_admin_graphql
      └── StandaloneShopifyTransport → requests + access_token
```

Core modules (`client`, `operations`, `models`, `transport`, `validation`, `definitions`) must not import `requests` or read access tokens.

## Retry ownership

- Transport may retry HTTP/rate limits.
- Client returns `retryable` on `MetaobjectUpsertResult` for workflow retry.
- Application (CMS) decides whether to re-invoke publish.

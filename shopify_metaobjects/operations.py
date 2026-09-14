"""GraphQL operation documents for metaobjects."""

UPSERT_MUTATION = """
mutation UpsertMetaobject($handle: MetaobjectHandleInput!, $metaobject: MetaobjectUpsertInput!) {
  metaobjectUpsert(handle: $handle, metaobject: $metaobject) {
    metaobject {
      id
      handle
      type
      fields {
        key
        value
      }
    }
    userErrors {
      field
      message
      code
    }
  }
}
""".strip()

GET_BY_HANDLE_QUERY = """
query GetMetaobjectByHandle($handle: MetaobjectHandleInput!) {
  metaobjectByHandle(handle: $handle) {
    id
    handle
    type
    fields {
      key
      value
    }
  }
}
""".strip()

# Compatibility query used by legacy loader (handle/type as separate args).
GET_BY_HANDLE_LEGACY_QUERY = """
query getMetaobject($handle: String!, $type: String!) {
  metaobject(handle: {type: $type, handle: $handle}) {
    id
    handle
    type
    fields {
      key
      value
    }
  }
}
""".strip()

LIST_METAOBJECTS_QUERY = """
query ListMetaobjects($type: String!, $first: Int!, $after: String) {
  metaobjects(type: $type, first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        handle
        type
        fields {
          key
          value
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
""".strip()

DELETE_MUTATION = """
mutation DeleteMetaobject($id: ID!) {
  metaobjectDelete(id: $id) {
    deletedId
    userErrors {
      field
      message
      code
    }
  }
}
""".strip()

DEFINITION_BY_TYPE_QUERY = """
query MetaobjectDefinitionByType($type: String!) {
  metaobjectDefinitionByType(type: $type) {
    id
    type
    name
    description
    fieldDefinitions {
      key
      name
      type {
        name
      }
      description
      required
      validations {
        name
        value
      }
    }
  }
}
""".strip()

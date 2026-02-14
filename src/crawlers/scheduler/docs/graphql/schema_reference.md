# GraphQL Schema Reference

## Schema Location

The GraphQL schema is defined in:
- `src/feed/graphql/schema.py` - Main schema
- `src/feed/graphql/ecommerce_schema.py` - E-commerce types and queries
- `src/feed/graphql/creator_schema.py` - Creator/Handle/Media types
- `src/feed/graphql/chan_schema.py` - 4chan types

## Schema Access

### Introspection Query

```graphql
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      fields {
        name
        type {
          name
          kind
        }
      }
    }
  }
}
```

### Get Schema SDL

```python
from feed.graphql.schema import schema
sdl = schema.as_str()
print(sdl)
```

## Type Definitions

### Product

```graphql
type Product {
  id: String!
  title: String!
  description: String!
  price: Float!
  currency: String!
  status: String!
  brand: String
  condition: String
  size: String
  category: String
  tags: [String!]!
  imageUrls: [String!]!
  sellerUsername: String
  likesCount: Int!
  createdUtc: String!
  updatedUtc: String
  url: String!
  permalink: String
  images: [ProductImage!]!
  seller: Seller
  priceHistory(limit: Int = 10): [PriceHistory!]!
}
```

### GarmentStyle

```graphql
type GarmentStyle {
  uuid: String!
  name: String!
  category: String!
  garmentType: String!
  primaryStyle: String!
  description: String
  color: String
  fit: String
  length: String
  material: String
  features: [StyleFeature!]!
  matchedProducts(limit: Int = 20): [ProductMatch!]!
}
```

### ProductMatch

```graphql
type ProductMatch {
  product: Product!
  confidenceScore: Float!
  matchType: String!
  matchedFeatures: [String!]!
}
```

## Query Examples

### Get Product with Full Details

```graphql
query GetProductDetails($id: String!) {
  product(id: $id) {
    id
    title
    price
    currency
    status
    brand
    images {
      url
      imageIndex
    }
    seller {
      username
    }
    priceHistory(limit: 20) {
      price
      currency
      timestamp
    }
  }
}
```

### Search and Filter Products

```graphql
query SearchAndFilter {
  searchProducts(queryText: "yoga pants", limit: 20) {
    id
    title
    price
    brand
  }
  
  products(filter: {
    category: "Tights"
    minPrice: 20.0
    maxPrice: 50.0
    status: "ONSALE"
    limit: 20
  }) {
    id
    title
    price
    url
  }
}
```

### Get Garment Style with Matched Products

```graphql
query GetStyleWithProducts($uuid: String!) {
  garmentStyle(uuid: $uuid) {
    name
    primaryStyle
    color
    features {
      featureType
      featureValue
    }
    matchedProducts(limit: 10) {
      product {
        id
        title
        price
        currency
        url
      }
      confidenceScore
      matchType
    }
  }
}
```

### Find Similar Styles

```graphql
query FindSimilar($uuid: String!) {
  similarStyles(styleUuid: $uuid, minSharedFeatures: 2) {
    uuid
    name
    primaryStyle
    color
    features {
      featureType
      featureValue
    }
  }
}
```

## Client Usage

### JavaScript/TypeScript (Apollo Client)

```typescript
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:8001/graphql',
  cache: new InMemoryCache()
});

const GET_PRODUCTS = gql`
  query GetProducts {
    products(limit: 20) {
      id
      title
      price
      images {
        url
      }
    }
  }
`;

const { data } = await client.query({ query: GET_PRODUCTS });
```

### Python (gql)

```python
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(url="http://localhost:8001/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql("""
  query {
    products(limit: 20) {
      id
      title
      price
    }
  }
""")

result = client.execute(query)
```

## Testing the Schema

### Validate Schema

```python
from feed.graphql.schema import schema

# Check schema is valid
assert schema is not None

# Get SDL
sdl = schema.as_str()
print(sdl)
```

### Test Queries

```python
from tests.e2e.puppeteer_test_setup import GraphQLTestClient

client = GraphQLTestClient()
response = await client.query("""
  query {
    __schema {
      queryType {
        name
        fields {
          name
        }
      }
    }
  }
""")
```

## Schema Evolution

When adding new types or fields:

1. Define type in appropriate schema file
2. Add query/mutation in main Query class
3. Update tests
4. Update documentation
5. Consider backward compatibility

## Performance Considerations

- Use field selection (don't request unnecessary fields)
- Use pagination (limit/offset)
- Consider data loaders for N+1 queries
- Cache frequently accessed data




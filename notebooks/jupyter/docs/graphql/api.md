# GraphQL API Documentation

## Endpoint

- **URL**: `http://localhost:8001/graphql`
- **WebSocket**: `ws://localhost:8001/graphql` (for subscriptions)

## Schema Overview

The GraphQL API provides access to:
- E-commerce products (Depop, Shopify)
- Garment styles and features
- Product matching and price history
- Reddit posts and images
- Creator/Handle/Media relationships

## E-commerce Queries

### Get Product by ID

```graphql
query GetProduct($id: String!) {
  product(id: $id) {
    id
    title
    description
    price
    currency
    status
    brand
    condition
    size
    category
    tags
    imageUrls
    sellerUsername
    likesCount
    createdUtc
    url
    images {
      url
      imageIndex
    }
    seller {
      username
    }
    priceHistory(limit: 10) {
      id
      price
      currency
      timestamp
    }
  }
}
```

**Variables**:
```json
{
  "id": "product_id_here"
}
```

### Search Products

```graphql
query SearchProducts($query: String!) {
  searchProducts(queryText: $query, limit: 20) {
    id
    title
    price
    currency
    brand
    status
    url
  }
}
```

### Filter Products

```graphql
query FilterProducts($filter: ProductFilter) {
  products(filter: $filter) {
    id
    title
    price
    currency
    brand
    category
    status
  }
}
```

**Variables**:
```json
{
  "filter": {
    "brand": "HANRO",
    "category": "Tights",
    "minPrice": 20.0,
    "maxPrice": 50.0,
    "status": "ONSALE",
    "limit": 20,
    "offset": 0
  }
}
```

## Garment Style Queries

### Get Garment Style

```graphql
query GetGarmentStyle($uuid: String!) {
  garmentStyle(uuid: $uuid) {
    uuid
    name
    category
    garmentType
    primaryStyle
    description
    color
    fit
    length
    material
    features {
      uuid
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

### Get Garment Styles

```graphql
query GetGarmentStyles($filter: StyleFilter) {
  garmentStyles(filter: $filter) {
    uuid
    name
    category
    garmentType
    primaryStyle
    color
    features {
      featureType
      featureValue
    }
  }
}
```

### Find Similar Styles

```graphql
query SimilarStyles($styleUuid: String!) {
  similarStyles(styleUuid: $styleUuid, minSharedFeatures: 2) {
    uuid
    name
    primaryStyle
    color
  }
}
```

## Reddit Queries

### Get Posts

```graphql
query GetPosts($filter: PostFilter) {
  posts(filter: $filter) {
    id
    title
    score
    numComments
    url
    subreddit
    author
    isImage
    imageUrl
  }
}
```

### Get Post with Images

```graphql
query GetPostWithImages($id: String!) {
  post(id: $id) {
    id
    title
    images {
      url
      source
    }
    links {
      url
      linkType
    }
  }
}
```

## Example Queries

### Find Products Matching a Style

```graphql
query FindStyleProducts($styleUuid: String!) {
  garmentStyle(uuid: $styleUuid) {
    name
    matchedProducts(limit: 20) {
      product {
        id
        title
        price
        currency
        url
        images {
          url
        }
      }
      confidenceScore
    }
  }
}
```

### Get Price Trends

```graphql
query PriceTrends($productId: String!) {
  product(id: $productId) {
    title
    priceHistory(limit: 30) {
      price
      currency
      timestamp
    }
  }
}
```

### Search for Sheer Panel Yoga Pants

```graphql
query FindSheerPanelPants {
  searchProducts(queryText: "sheer panel yoga pants black", limit: 20) {
    id
    title
    price
    currency
    brand
    url
    images {
      url
    }
  }
}
```

## Schema Introspection

You can introspect the schema:

```graphql
query IntrospectionQuery {
  __schema {
    queryType {
      name
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

## Error Handling

GraphQL returns errors in the `errors` field:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Product not found",
      "path": ["product"],
      "extensions": {
        "code": "NOT_FOUND"
      }
    }
  ]
}
```

## Subscriptions

Real-time updates via WebSocket:

```graphql
subscription FeedUpdates($subreddit: String) {
  feedUpdates(subreddit: $subreddit) {
    id
    title
    score
    url
    subreddit
  }
}
```

## Testing

Use the GraphQL test client:

```python
from tests.e2e.puppeteer_test_setup import GraphQLTestClient

client = GraphQLTestClient()
response = await client.query("""
  query {
    products(limit: 10) {
      id
      title
      price
    }
  }
""")
```

## Client Libraries

### JavaScript/TypeScript

```bash
npm install @apollo/client graphql
```

```javascript
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
      title
      price
    }
  }
`;

const { data } = await client.query({ query: GET_PRODUCTS });
```

### Python

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




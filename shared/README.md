# Shared Types

Common type definitions used across the Bunny platform.

## Installation

This package is referenced via workspace protocol:

```json
{
  "dependencies": {
    "@bunny/shared": "workspace:*"
  }
}
```

## Usage

```typescript
import { Platform, MediaType } from '@bunny/shared/types';
```

## Architecture

These types serve as the single source of truth for:
- Platform enums (social media platforms)
- Media type enums
- Common status enums

For GraphQL-specific types, generate from schema using GraphQL Code Generator.

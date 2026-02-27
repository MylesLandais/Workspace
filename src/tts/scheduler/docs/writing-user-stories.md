# Writing User Stories and Design Specifications

This guide provides best practices for writing effective user stories and design specifications that drive clear, actionable development work.

## Table of Contents

1. [User Story Format](#user-story-format)
2. [Writing Effective Stories](#writing-effective-stories)
3. [Design Specifications](#design-specifications)
4. [Story Templates](#story-templates)
5. [Common Pitfalls](#common-pitfalls)
6. [Examples from This Repository](#examples-from-this-repository)

## User Story Format

### Standard Template

```
As a [type of user]
I want to [perform some action]
So that [achieve some goal/benefit]
```

### Extended Template (Recommended)

```
### US-XXX: [Short Descriptive Title]

**As a** [type of user]  
**I want to** [perform some action]  
**So that** [achieve some goal/benefit]

**Status**: [Planned | In Progress | Implemented | Blocked]  
**Priority**: [Low | Medium | High | Critical]  
**Story Points**: [1-13]  
**Labels**: [feature, bug, enhancement, etc.]

**Context**:  
[Background information, why this is needed, related issues]

**Acceptance Criteria**:
- [ ] [Specific, testable condition]
- [ ] [Another testable condition]
- [ ] [Edge case or error handling]

**Technical Notes**:
[Implementation approach, dependencies, design decisions]

**Dependencies**:
- [Related story US-YYY]
- [Blocked by US-ZZZ]

**Testing**:
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing steps

**Documentation**:
- [ ] API documentation
- [ ] User guide updates
- [ ] Architecture decision record (if needed)
```

## Writing Effective Stories

### 1. Focus on User Value

**Bad:**
```
As a developer
I want to add a new database table
So that I can store more data
```

**Good:**
```
As a market analyst
I want to track product prices over time
So that I can analyze market trends and identify price drops
```

### 2. Be Specific and Testable

**Bad:**
```
As a user
I want better error messages
So that I know what went wrong
```

**Good:**
```
As a user
I want to see specific error messages when API calls fail
So that I can understand what went wrong and how to fix it

Acceptance Criteria:
- [ ] HTTP 404 errors show "Resource not found: [resource_id]"
- [ ] HTTP 401 errors show "Authentication required. Please check your API key."
- [ ] HTTP 500 errors show "Server error. Please try again later or contact support."
- [ ] Error messages include request ID for debugging
```

### 3. Include Context

**Bad:**
```
As a crawler
I want to respect rate limits
So that I don't get blocked
```

**Good:**
```
As a crawler system
I want to respect platform-specific rate limits
So that I don't get IP-banned and can maintain continuous operation

Context:
- Different platforms (Reddit, 4chan, Depop) have different rate limits
- Some platforms use exponential backoff
- We need to track rate limit state per platform
- Current implementation doesn't handle rate limits consistently
```

### 4. Define Clear Acceptance Criteria

Acceptance criteria should be:
- **Specific**: Clear, unambiguous conditions
- **Testable**: Can be verified with tests or manual checks
- **Complete**: Cover happy path, edge cases, and error conditions

**Example:**
```
Acceptance Criteria:
- [ ] Can add a product to tracking via API
- [ ] Product data includes: title, description, price, images, seller
- [ ] Price history is automatically recorded on first add
- [ ] Subsequent price checks update history, not create duplicates
- [ ] Invalid product URLs return 400 error with clear message
- [ ] Missing required fields return 400 error listing missing fields
```

### 5. Consider Technical Constraints

Include technical notes when relevant:

```
Technical Notes:
- Use existing DepopAdapter for data extraction
- Store in Neo4j using ProductStorage class
- Price history stored as PriceHistory nodes with NEXT_PRICE relationships
- Consider rate limiting: Depop allows 1 request per 2 seconds
```

## Design Specifications

Design specifications provide detailed technical design for implementing user stories. They should be created for:
- Complex features requiring architectural decisions
- Features affecting multiple systems
- Features with significant technical risk
- Features requiring new infrastructure

### Specification Template

```
# Design Specification: [Feature Name]

**Story**: US-XXX  
**Status**: [Draft | Review | Approved | Implemented]  
**Author**: [Name]  
**Date**: [YYYY-MM-DD]  
**Reviewers**: [Names]

## Overview

[High-level description of what we're building and why]

## Goals

1. [Primary goal]
2. [Secondary goal]
3. [Non-goal (what we're explicitly not doing)]

## Current State

[Describe how things work today, what problems exist]

## Proposed Solution

[Describe the proposed approach]

### Architecture

[Diagrams, component descriptions, data flow]

### Data Model

[Database schema, API contracts, data structures]

### API Design

[Endpoints, request/response formats, error handling]

### Algorithms/Logic

[Key algorithms, business logic, edge cases]

## Alternatives Considered

### Alternative 1: [Name]
**Pros**: [Benefits]  
**Cons**: [Drawbacks]  
**Why Not Chosen**: [Reason]

### Alternative 2: [Name]
[Same format]

## Implementation Plan

### Phase 1: [Name]
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Phase 2: [Name]
- [ ] Task 1
- [ ] Task 2

## Testing Strategy

### Unit Tests
[What to test at unit level]

### Integration Tests
[What to test at integration level]

### E2E Tests
[What to test end-to-end]

## Performance Considerations

[Performance requirements, benchmarks, optimization strategies]

## Security Considerations

[Security requirements, threat model, mitigation strategies]

## Migration Plan

[How to migrate from current state to new state]

## Rollout Plan

[Phased rollout, feature flags, monitoring]

## Open Questions

1. [Question 1]
2. [Question 2]

## References

- [Related ADR](./ARCHITECTURE_DECISIONS.md#ADR-XXX)
- [Related Story](./USER_STORIES.md#US-XXX)
- [External Documentation](https://...)
```

## Story Templates

### Template 1: Feature Story

```
### US-XXX: [Feature Name]

**As a** [user type]  
**I want to** [action]  
**So that** [benefit]

**Status**: Planned  
**Priority**: High  
**Story Points**: 5

**Context**:  
[Why this is needed]

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Technical Notes**:
[Implementation approach]

**Dependencies**:
- None

**Testing**:
- [ ] Unit tests
- [ ] Integration tests
```

### Template 2: Bug Fix Story

```
### US-XXX: Fix [Bug Description]

**As a** [user type]  
**I want to** [expected behavior]  
**So that** [benefit]

**Status**: In Progress  
**Priority**: High  
**Story Points**: 3

**Context**:  
[What's broken, how it manifests, impact]

**Root Cause**:  
[Why it's broken]

**Acceptance Criteria**:
- [ ] [Fixed behavior]
- [ ] [Regression test]

**Technical Notes**:
[Fix approach]

**Testing**:
- [ ] Reproduces bug
- [ ] Fix works
- [ ] No regressions
```

### Template 3: Technical Debt Story

```
### US-XXX: Refactor [Component]

**As a** developer  
**I want to** [refactor action]  
**So that** [maintainability/performance benefit]

**Status**: Planned  
**Priority**: Medium  
**Story Points**: 8

**Context**:  
[What's wrong with current implementation]

**Acceptance Criteria**:
- [ ] [Functionality preserved]
- [ ] [Code quality improved]
- [ ] [Tests updated]

**Technical Notes**:
[Refactoring approach, see REFACTORING_GUIDELINES.md]

**Dependencies**:
- [Related stories]
```

## Common Pitfalls

### 1. Vague or Generic Stories

**Bad:**
```
As a user
I want the system to work better
So that I'm happy
```

**Good:**
```
As a market analyst
I want to see price trends visualized in a chart
So that I can quickly identify price drops and market patterns
```

### 2. Implementation Details in Stories

**Bad:**
```
As a developer
I want to use Redis for caching
So that responses are faster
```

**Good:**
```
As a user
I want API responses to be faster
So that I don't have to wait long for results

Technical Notes:
- Consider caching with Redis
- Alternative: In-memory caching
```

### 3. Missing Acceptance Criteria

**Bad:**
```
As a user
I want to search for products
So that I can find what I need
```

**Good:**
```
As a user
I want to search for products
So that I can find what I need

Acceptance Criteria:
- [ ] Can search by product name
- [ ] Can search by style tags
- [ ] Results show matching products with images
- [ ] Empty results show helpful message
- [ ] Invalid queries show error message
```

### 4. Stories Too Large

**Bad:**
```
As a developer
I want to build the entire e-commerce platform
So that users can buy and sell products
```

**Good:** (Break into smaller stories)
```
US-001: User Registration
US-002: Product Listing
US-003: Product Search
US-004: Shopping Cart
US-005: Checkout Process
```

### 5. Missing Context

**Bad:**
```
As a crawler
I want to handle errors
So that it doesn't crash
```

**Good:**
```
As a crawler system
I want to handle network errors gracefully
So that crawling continues even when individual requests fail

Context:
- Network timeouts are common (5-10% of requests)
- Some sites return 503 errors temporarily
- We need to retry with exponential backoff
- After 3 failures, skip and log for manual review
```

## Examples from This Repository

### Good Example: US-001 (from USER_STORIES.md)

```
### US-001: Track Product Prices

**As a** market analyst  
**I want to** track prices of specific products over time  
**So that** I can analyze market trends and price fluctuations

**Status**: ✅ Implemented  
**Implementation**: `ProductStorage.store_product()` automatically creates PriceHistory nodes

**Acceptance Criteria**:
- [x] Can add products to price tracking
- [x] Price history is automatically recorded
- [x] Can query price history for any product
- [ ] Price changes trigger notifications (planned)
```

**Why it's good:**
- Clear user and value
- Specific implementation reference
- Clear acceptance criteria
- Status tracking

### Good Example: US-002

```
### US-002: Discover Products from Images

**As a** user browsing social media  
**I want to** find e-commerce listings for garments I see in images  
**So that** I can purchase similar items

**Status**: ✅ Implemented  
**Implementation**: `GarmentMatcher.analyze_and_match_image()` provides full workflow

**Acceptance Criteria**:
- [x] Can upload/analyze an image (via CV model input)
- [x] System identifies garment style (creates GarmentStyle nodes)
- [x] System finds matching products (ProductMatch relationships)
- [x] Provides links to marketplace listings (Depop, eBay, Poshmark, Mercari)
```

**Why it's good:**
- Clear user journey
- Specific technical implementation
- Complete acceptance criteria
- Links to actual code

## Story Review Checklist

Before marking a story as complete:

- [ ] Story follows template format
- [ ] User type is specific (not "user" or "developer" unless appropriate)
- [ ] Value proposition is clear
- [ ] Acceptance criteria are specific and testable
- [ ] All acceptance criteria are met
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Code is reviewed
- [ ] No regressions introduced

## Design Spec Review Checklist

Before approving a design spec:

- [ ] Problem is clearly defined
- [ ] Current state is documented
- [ ] Proposed solution is detailed
- [ ] Alternatives are considered
- [ ] Implementation plan is realistic
- [ ] Testing strategy is comprehensive
- [ ] Performance and security considered
- [ ] Migration plan exists (if needed)
- [ ] Open questions are identified

## Tools and Resources

- **Story Tracking**: Use GitHub Issues with labels and projects
- **Design Docs**: Store in `docs/design/` directory
- **ADR Template**: See [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)
- **User Stories**: See [USER_STORIES.md](./USER_STORIES.md)

## References

- [User Stories Guide](https://www.mountaingoatsoftware.com/agile/user-stories)
- [INVEST Criteria](https://en.wikipedia.org/wiki/INVEST_(mnemonic))
- [Acceptance Criteria Best Practices](https://www.agilealliance.org/glossary/acceptance-criteria/)




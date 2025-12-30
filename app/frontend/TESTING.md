# Testing Guide

Testing setup and best practices for the Feed Manager Client.

## Test Framework

- **Vitest**: Fast unit test runner (Vite-native)
- **React Testing Library**: Component testing utilities
- **jsdom**: DOM environment for browser API testing

## Running Tests

### In Docker

```bash
# Run all tests
docker-compose exec frontend bun run test

# Watch mode (re-runs on file changes)
docker-compose exec frontend bun run test:watch

# With coverage report
docker-compose exec frontend bun run test:coverage

# Interactive UI
docker-compose exec frontend bun run test:ui
```

### Locally

```bash
bun run test
bun run test:watch
bun run test:coverage
bun run test:ui
```

## Test Structure

```
src/
├── components/
│   ├── feed/
│   │   ├── FeedView.tsx
│   │   └── __tests__/
│   │       └── FeedView.test.tsx
│   └── admin/
│       ├── AdminConsole.tsx
│       └── __tests__/
│           └── AdminConsole.test.tsx
├── lib/
│   └── utils/
│       ├── formatters.ts
│       └── __tests__/
│           └── formatters.test.ts
└── test/
    ├── setup.ts          # Global test setup
    └── test-utils.tsx    # Custom render utilities
```

## Writing Tests

### Component Tests

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### Testing User Interactions

```typescript
import { fireEvent, waitFor } from '@testing-library/react';

it('handles button click', async () => {
  const handleClick = vi.fn();
  render(<Button onClick={handleClick} />);
  
  fireEvent.click(screen.getByRole('button'));
  
  await waitFor(() => {
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### Testing Async Behavior

```typescript
it('loads data asynchronously', async () => {
  render(<DataComponent />);
  
  // Wait for loading to complete
  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  });
});
```

## Test Coverage

Coverage reports are generated in `coverage/` directory:

- HTML report: `coverage/index.html`
- JSON report: `coverage/coverage-final.json`
- Text summary: printed to console

### Coverage Goals

- **Components**: >80% coverage
- **Utilities**: >90% coverage
- **Hooks**: >80% coverage

## Best Practices

1. **Test Behavior, Not Implementation**
   - Test what users see and do
   - Avoid testing internal state directly

2. **Use Semantic Queries**
   - Prefer `getByRole`, `getByLabelText`
   - Avoid `getByTestId` unless necessary

3. **Mock External Dependencies**
   - Mock API calls
   - Mock complex components
   - Use MSW for GraphQL mocking

4. **Keep Tests Isolated**
   - Each test should be independent
   - Clean up after tests (handled by setup.ts)

5. **Test Edge Cases**
   - Empty states
   - Loading states
   - Error states
   - Null/undefined handling

## Example Test Patterns

### Testing Form Inputs

```typescript
it('updates input value', () => {
  render(<SearchInput />);
  const input = screen.getByPlaceholderText('Search...');
  
  fireEvent.change(input, { target: { value: 'test' } });
  
  expect(input).toHaveValue('test');
});
```

### Testing Conditional Rendering

```typescript
it('shows message when no results', () => {
  render(<SearchResults results={[]} />);
  expect(screen.getByText('No results found')).toBeInTheDocument();
});

it('hides message when results exist', () => {
  render(<SearchResults results={[{ id: '1' }]} />);
  expect(screen.queryByText('No results found')).not.toBeInTheDocument();
});
```

### Testing Keyboard Navigation

```typescript
it('handles keyboard events', () => {
  const onClose = vi.fn();
  render(<Modal onClose={onClose} />);
  
  fireEvent.keyDown(document, { key: 'Escape' });
  
  expect(onClose).toHaveBeenCalled();
});
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests

See `.github/workflows/test.yml` for CI configuration.

## Debugging Tests

### Using Vitest UI

```bash
bun run test:ui
```

Opens interactive test UI in browser for debugging.

### Debugging in VS Code

Add to `.vscode/launch.json`:

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Tests",
  "runtimeExecutable": "bun",
  "runtimeArgs": ["run", "test"],
  "console": "integratedTerminal"
}
```

## Common Issues

### "Cannot find module 'react'"

- Ensure `@types/react` is installed
- Check `tsconfig.json` includes proper types

### "window is not defined"

- Ensure `jsdom` environment is set in `vitest.config.ts`
- Check test setup includes DOM globals

### Tests timing out

- Use `waitFor` for async operations
- Increase timeout if needed: `it('test', async () => { ... }, { timeout: 5000 })`



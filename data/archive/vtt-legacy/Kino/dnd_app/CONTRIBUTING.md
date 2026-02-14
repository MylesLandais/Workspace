# Contributing to D&D App

Thank you for your interest in contributing! This document outlines the development workflow and testing practices.

## Development Workflow

### Branch Strategy

1. **Create a feature branch** from `main` or `develop`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit with clear messages:
   ```bash
   git commit -m "Add feature: description of changes"
   ```

3. **Push to GitHub**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** using the PR template

### Code Review Process

All PRs must:
- Pass all tests (unit and integration)
- Have no linter errors
- Include tests for new functionality
- Follow the project's code style
- Update documentation if needed

## Testing

### Running Tests

```bash
# Run all unit tests (excludes integration tests)
mix test

# Run all tests including integration tests
mix test.all

# Run specific test file
mix test test/dnd_app/dice_test.exs

# Run tests with coverage
mix test --cover
```

### Test Structure

- **Unit Tests**: Fast, isolated tests in `test/dnd_app/`
  - `dice_test.exs` - Dice rolling logic
  - `characters_test.exs` - Character creation and stat calculation

- **Integration Tests**: Tests that require Neo4j in `test/dnd_app/db/`
  - `neo4j_test.exs` - Database operations (tagged with `@moduletag :integration`)

- **LiveView Tests**: UI and interaction tests in `test/dnd_app_web/live/`
  - `home_live_test.exs` - Dice roller UI
  - `character_live_test.exs` - Character creation and display

### Test Coverage Expectations

- **New features**: Must include unit tests
- **Bug fixes**: Must include regression tests
- **Database operations**: Must include integration tests
- **UI changes**: Must include LiveView tests

### Writing Tests

1. **Use descriptive test names**:
   ```elixir
   test "calculates ability modifier for score 12" do
     # ...
   end
   ```

2. **Group related tests** with `describe`:
   ```elixir
   describe "roll/1" do
     test "rolls a simple d20" do
       # ...
     end
   end
   ```

3. **Test edge cases**:
   - Invalid inputs
   - Boundary conditions
   - Error cases

4. **Keep tests independent**: Each test should be able to run in isolation

## Code Style

- Follow Elixir style guide
- Use `mix format` before committing
- Keep functions focused and small
- Add `@moduledoc` and `@doc` where appropriate

## Pre-commit Checklist

Before submitting a PR:

- [ ] All tests pass (`mix test`)
- [ ] Code is formatted (`mix format`)
- [ ] No linter warnings
- [ ] Tests added for new functionality
- [ ] Documentation updated if needed
- [ ] PR description is clear and complete

## Questions?

Feel free to ask questions in PR comments or open an issue for discussion.






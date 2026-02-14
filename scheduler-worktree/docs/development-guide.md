# Development Guide

This guide provides a quick reference for common development tasks and links to detailed documentation.

## Quick Links

- **[Contributing Guidelines](../CONTRIBUTING.md)**: Setup, workflow, and standards
- **[Refactoring Guidelines](REFACTORING_GUIDELINES.md)**: How to refactor code safely
- **[Writing User Stories](WRITING_USER_STORIES.md)**: Templates and best practices
- **[Repository Layout](REPOSITORY_LAYOUT.md)**: Where to put new code

## Common Tasks

### Starting a New Feature

1. **Write a user story** (see [WRITING_USER_STORIES.md](WRITING_USER_STORIES.md))
   - Define user, action, and value
   - List acceptance criteria
   - Add technical notes if needed

2. **Create a design spec** (if complex)
   - Document architecture
   - Define API contracts
   - Plan implementation phases

3. **Choose the right location** (see [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md))
   - Production code → `src/`
   - Scripts → `scripts/`
   - Examples → `notebooks/examples/`

4. **Write tests**
   - Unit tests for core logic
   - Integration tests for workflows
   - Update test coverage

5. **Update documentation**
   - Update relevant README files
   - Add API documentation
   - Update architecture docs if needed

### Refactoring Existing Code

1. **Plan the refactoring** (see [REFACTORING_GUIDELINES.md](REFACTORING_GUIDELINES.md))
   - Identify scope and dependencies
   - Create migration plan
   - Get approval for large changes

2. **Work incrementally**
   - Make small, testable changes
   - Keep tests passing
   - Commit frequently

3. **Update imports and references**
   - Update all import paths
   - Update documentation
   - Update scripts that reference moved code

4. **Verify and clean up**
   - Run full test suite
   - Check all imports work
   - Remove deprecated code

### Moving a Script

1. Identify target directory: `scripts/[category]/`
2. Move with git: `git mv script.py scripts/category/`
3. Update imports in the script
4. Update any references
5. Test the script

See [REFACTORING_GUIDELINES.md#migration-strategies](REFACTORING_GUIDELINES.md#migration-strategies) for details.

### Writing Documentation

1. **User Stories**: Use template from [WRITING_USER_STORIES.md](WRITING_USER_STORIES.md)
2. **Design Specs**: Use template from [WRITING_USER_STORIES.md#design-specifications](WRITING_USER_STORIES.md#design-specifications)
3. **Architecture Decisions**: See [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) for ADR format
4. **Code Comments**: Document public APIs, complex logic, and non-obvious decisions

## Repository Structure Quick Reference

```
src/              # Production code (importable)
scripts/          # Utility scripts (executable)
notebooks/        # Jupyter notebooks
tests/            # Test suite
docs/             # Documentation
agents/           # Agent implementations
```

See [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md) for detailed structure.

## Code Organization Principles

1. **Separation of Concerns**: Production code, scripts, and tests are separate
2. **Module Cohesion**: Related functionality grouped together
3. **Discoverability**: Clear naming and logical structure
4. **Maintainability**: Easy to find, understand, and modify code

## Naming Conventions

- **Modules**: `snake_case` (e.g., `image_dedup`)
- **Classes**: `PascalCase` (e.g., `ProductStorage`)
- **Functions**: `snake_case` (e.g., `get_connection`)
- **Scripts**: `snake_case` with verb (e.g., `check_status.py`)

## Before Submitting a PR

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No secrets committed (Talisman check)
- [ ] Imports are correct
- [ ] User story/design spec exists (for new features)
- [ ] Refactoring follows guidelines (for refactors)

## Getting Help

- Check the relevant guide in `docs/`
- Look at similar existing code
- Ask in an issue or PR
- Reference the relevant guide in your question

## References

- [Contributing Guidelines](../CONTRIBUTING.md)
- [Refactoring Guidelines](REFACTORING_GUIDELINES.md)
- [Writing User Stories](WRITING_USER_STORIES.md)
- [Repository Layout](REPOSITORY_LAYOUT.md)
- [Architecture Decisions](ARCHITECTURE_DECISIONS.md)




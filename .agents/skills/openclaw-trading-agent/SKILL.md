```markdown
# openclaw-trading-agent Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the `openclaw-trading-agent` Python codebase. You'll learn how to write code that fits the project's style, structure your files, use imports and exports, and follow commit and testing practices. This guide is ideal for contributors who want to maintain consistency and quality in their code.

## Coding Conventions

### File Naming
- Use **snake_case** for all file and module names.
  - Example: `trade_executor.py`, `market_data_handler.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .order_manager import OrderManager
    from ..utils import calculate_risk
    ```

### Export Style
- Use **named exports** by explicitly listing what should be accessible.
  - Example:
    ```python
    __all__ = ["TradeAgent", "OrderManager"]
    ```

### Commit Messages
- Follow **conventional commit** style.
- Use the `feat` prefix for new features.
  - Example:
    ```
    feat: add support for trailing stop orders
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new functionality or module  
**Command:** `/add-feature`

1. Create a new Python file using snake_case naming.
2. Implement the feature using relative imports for internal dependencies.
3. Add named exports to the module's `__all__` list if needed.
4. Write or update tests in a corresponding `*.test.*` file.
5. Commit your changes using a conventional commit message with the `feat` prefix.

### Writing and Running Tests
**Trigger:** When validating new or existing code  
**Command:** `/run-tests`

1. Place test files alongside implementation files, using the `*.test.*` naming pattern.
   - Example: `trade_executor.test.py`
2. Write tests using your preferred framework (none detected; choose one if needed).
3. Run tests manually using your chosen test runner (e.g., `pytest`, `unittest`).

### Importing Modules
**Trigger:** When referencing code from other modules within the package  
**Command:** `/import-module`

1. Use relative imports to access sibling or parent modules.
   - Example:
     ```python
     from .order_manager import OrderManager
     from ..utils import calculate_risk
     ```

## Testing Patterns

- Test files follow the `*.test.*` naming convention.
  - Example: `market_data_handler.test.py`
- Testing framework is not specified; select and use one (e.g., `pytest`, `unittest`).
- Place test files near the code they test for easy discovery and maintenance.

## Commands
| Command        | Purpose                                         |
|----------------|-------------------------------------------------|
| /add-feature   | Scaffold and commit a new feature module        |
| /run-tests     | Run all tests in the codebase                   |
| /import-module | Reference another module using relative imports  |
```

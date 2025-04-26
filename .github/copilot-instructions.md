### Context7

- **Always use the Context7 MCP Server** to reference documentation for libraries like Pydantic AI and Streamlit.
- For the tokens, **start with 5000**, but increase to **20000** if the first search does not return relevant documentation.
- **Limit searches to three attempts per specific piece of documentation.** If you cannot find what you need, use the Brace MCP Server for a wider search.

### Project Awareness & Context

1. **Read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.

2. **Check `TASK.md`** before beginning a new task:
   - If the task is not listed, add it with a brief description and today's date.

3. **Follow consistent naming conventions, file structures, and architecture patterns** as described in `PLANNING.md`.

### Code Structure & Modularity

1. **Keep files under 500 lines of code.** If a file approaches this limit, refactor it into smaller modules or helper files.

2. **Use clear, consistent imports:**
   - Prefer absolute imports for clarity.
   - Avoid relative imports like `.` or `..`, and instead adjust the system path for importing required modules.

### Testing & Reliability

1. **Write Pytest unit tests for all new features**, such as functions, classes, and routes.

2. **Update existing unit tests** when logic is modified.

3. **Organize tests in a `/tests` folder**, mirroring the structure of the main application. Each feature should include:
   - 1 test for expected behavior.
   - 1 test for edge cases.
   - 1 test for failure scenarios.

4. **Individually test all functions** used in agent tools.

### Task Management

1. **Mark tasks as completed in `TASK.md`** immediately after finishing them.

2. **Document new sub-tasks or TODOs** discovered during development in the "Discovered During Work" section of `TASK.md`.

### Style & Conventions

1. **Use Python** as the primary language.

2. **Adhere to PEP 8**:
   - Use type hints.
   - Format code with `black`.

3. **Use Pydantic** for data validation and parsing.

4. **Write Google-style docstrings** for all functions:

    ```python
    def example(param1: str) -> str:
        """
        Brief summary.

        Args:
            param1 (str): Description of the parameter.

        Returns:
            str: Description of the return value.
        """
    ```

### Documentation & Explainability

1. **Update `README.md`** when features are added, dependencies change, or setup steps are modified.

2. **Comment non-obvious code** to ensure it is understandable to a mid-level developer.

3. **Add `# Reason:` comments** to explain complex logic, focusing on the "why" rather than just the "what".

### AI Behavior Rules

1. **Ask questions if context is missing**—do not make assumptions.

2. **Verify paths and module names** before using them.

3. **Do not delete or overwrite existing code** unless explicitly instructed or as part of a defined task.

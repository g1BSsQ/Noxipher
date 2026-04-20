# Contributing to Noxipher

> [!IMPORTANT]
> ### 🛑 MANDATORY PRE-PUSH CHECKLIST
> Before pushing ANY code or submitting a Pull Request, you **MUST** run the following commands locally and ensure they all pass with **ZERO** errors. Failure to do so will result in automated rejection.
>
> 1. **Linting & Formatting**: `ruff check src/ tests/ --fix`
> 2. **Type Checking**: `mypy src/`
> 3. **Unit Tests**: `pytest`
>
> **Do NOT push if any of the above fails.**

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (for dependency and virtual environment management)
- Git

### Setting up the Development Environment

1. **Fork the repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/noxipher.git
   cd noxipher
   ```

3. **Install dependencies** using `uv`:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

## Development Workflow

### Coding Standards
We enforce coding standards using `ruff` and `mypy`:
- **Formatting and Linting**: We use `ruff`.
  ```bash
  ruff check .
  ruff format .
  ```
- **Type Checking**: We use strict type checking with `mypy`.
  ```bash
  mypy src/
  ```

### Testing
All code changes should be accompanied by relevant tests. We use `pytest` with `pytest-asyncio` for testing async code.
```bash
pytest
```

## Pull Request Process

1. Create a new branch from `main` for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes, following the coding standards and adding tests as necessary.
3. Ensure all tests, linters, and type checks pass.
4. Commit your changes with clear, descriptive commit messages.
5. Push to your fork and submit a Pull Request against the `main` branch of the upstream repository.

## Documentation
If your changes involve new features or API changes, please update the relevant documentation. We use ReadTheDocs for our documentation platform.

Thank you for contributing to make Noxipher better!

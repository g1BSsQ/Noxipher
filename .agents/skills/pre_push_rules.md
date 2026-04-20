# Strict Pre-Push Workflow

This skill defines the mandatory workflow that MUST be followed before pushing any code to the repository.

## 🛑 MANDATORY CHECKLIST
Before running `git push`, you MUST execute the following steps in order:

### 1. Linting & Formatting
Run `ruff` to ensure code style compliance.
```bash
ruff check src/ tests/ --fix
```

### 2. Static Type Checking
Run `mypy` to ensure type safety.
```bash
mypy src/
```

### 3. Automated Testing
Run `pytest` to ensure no regressions.
```bash
pytest
```

## 🚫 PROHIBITED ACTIONS
- **NEVER** push code if any of the above checks fail.
- **NEVER** assume code is correct without running local verification.
- **NEVER** use `git push --force` or `--no-verify` to bypass these rules.

## ✅ BEST PRACTICES
- If a check fails, fix the error and **RE-RUN ALL CHECKS** before pushing.
- Always check `.agents/skills/` for project-specific rules before starting a task.

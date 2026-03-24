Run before every commit.
Usage: /project:pre-commit-check

Steps:
1. python -m pytest tests/ -v
2. Verify README test count matches actual: find tests/ -name "test_*.py" | wc -l
3. Verify no instance/*.db files staged: git diff --cached --name-only | grep instance/
4. Report any mismatches.

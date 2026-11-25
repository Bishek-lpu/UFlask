# Contributing to uFlask

Thank you for your interest in contributing! 🎉

---

## Development Setup

```bash
git clone https://github.com/Bishek-lpu/UFlask.git
cd UFlask
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=uflask --cov-report=term-missing
```

## Code Style

- **MicroPython-compatible**: no `eval`, no f-strings (use `%`), no walrus operator
- **No external dependencies** in the core `uflask/` package
- Keep RAM usage in mind — the Pico W has ~180 kB free for user code
- Line length: 100 characters max

## Submitting Changes

1. Fork the repo and create a branch: `git checkout -b feature/my-feature`
2. Make your changes and add tests
3. Run `pytest` — all tests must pass
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Open a Pull Request with a clear description

## Commit Message Format

```
type: short description

Longer description if needed.

Closes #123
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`

Examples:
```
feat: add WebSocket support
fix: handle empty JSON body gracefully
docs: add deployment guide for Pico W
test: add test for multipart file upload
```

## Reporting Bugs

Use the [Bug Report template](https://github.com/Bishek-lpu/UFlask/issues/new?template=bug_report.yml) and include:
- uFlask version
- MicroPython version (if on Pico W)
- Minimal reproducible example
- Expected vs actual behaviour

## Requesting Features

Use the [Feature Request template](https://github.com/Bishek-lpu/UFlask/issues/new?template=feature_request.yml).

---

MIT License — your contributions are also MIT licensed.

# Contributing to Codeforces Editorial Finder

Thank you for your interest in contributing! 🎉

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/codeforces-editorial-finder.git
   cd codeforces-editorial-finder
   ```

3. **Install dependencies**
   ```bash
   uv sync --group dev
   uv run playwright install chromium
   ```

## Development Workflow

### 1. Create a branch for your issue

Branch name should match the issue number:

```bash
git checkout -b 42  # For issue #42
```

### 2. Make your changes

- Write clean, readable code
- Follow existing code style
- Add tests if applicable

### 3. Commit your changes

Start each commit message with the issue number:

```bash
git commit -m "#42: Add support for custom wait time"
git commit -m "#42: Fix timeout handling"
```

### 4. Run checks locally

Before pushing, ensure all checks pass:

```bash
just lint      # Run linting
just format    # Format code
just typecheck # Type checking
```

Or run everything:
```bash
just lint && just format && just typecheck
```

### 5. Push and create a Pull Request

```bash
git push origin 42
```

Then open a PR on GitHub targeting the `main` branch.

## Pull Request Guidelines

- **Title**: Brief description of changes (e.g., "Add REST API support")
- **Description**:
  - Reference the issue: `Closes #42`
  - Explain what and why
  - List any breaking changes
- **CI Checks**: All checks must pass ✅
- **Review**: Wait for maintainer review

## Code Style

- Python 3.13+
- Line length: 100 characters
- Use type hints
- Follow PEP 8 (enforced by `ruff`)

## Questions?

Open an issue or ask in your PR! We're here to help. 🚀

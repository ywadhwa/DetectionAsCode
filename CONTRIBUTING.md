# Contributing to Detection as Code

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `dev/*`: Feature and development branches

### Making Changes

1. Create a feature branch from `main`:
   ```bash
   git checkout -b dev/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Run validation before committing:
   ```bash
   ./scripts/validate.sh
   ```

4. Commit with a descriptive message:
   ```bash
   git commit -m "Add: description of your change"
   ```

5. Push and open a Pull Request

## Types of Contributions

### Adding Sigma Rules

1. Place rules in the appropriate category directory under `sigma-rules/`
2. Follow the naming convention: `<category>_<descriptive_name>.yml`
3. Include all required fields (title, id, status, description, logsource, detection, level)
4. Add ATT&CK tags where applicable
5. Document false positives

### Improving Scripts/Tooling

1. Maintain backward compatibility where possible
2. Add appropriate error handling
3. Update documentation if behavior changes

### Documentation

- Keep README and docs/ in sync with code changes
- Use clear, concise language
- Include examples where helpful

## Code Style

### Python

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Keep functions focused and testable
- Document complex logic with comments

### YAML (Sigma Rules)

- Use consistent indentation (4 spaces)
- Quote strings containing special characters
- Keep detection logic readable

## Pull Request Guidelines

### PR Title Format

- `Add: <description>` - New features or rules
- `Fix: <description>` - Bug fixes
- `Update: <description>` - Improvements to existing code
- `Docs: <description>` - Documentation changes

### PR Description

Include:
- What the change does
- Why it's needed
- How to test it
- Any breaking changes

### Review Process

1. All PRs require passing CI checks
2. Maintainer review is required before merge
3. Address review feedback promptly

## Testing

### Local Testing

```bash
# Run full validation suite
./scripts/validate.sh

# Test Splunk queries (requires Docker)
cd docker && docker-compose up -d
python scripts/test_splunk_queries.py --expectations tests/expected_matches.yml
docker-compose down
```

### CI Testing

The Azure DevOps pipeline runs automatically on:
- Push to `main` or `dev/*`
- Pull requests targeting `main`

## Questions?

- Open a GitHub Discussion for general questions
- Open an Issue for bugs or feature requests
- See the docs/ directory for detailed documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

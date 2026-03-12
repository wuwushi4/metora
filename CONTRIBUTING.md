# Contributing to Metora

Thank you for your interest in contributing to Metora! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/wuwushi4/metora.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- uv (Python package manager)

### Backend Development

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Using Docker (Recommended)

```bash
docker compose -f docker-compose.dev.yml up -d
```

## Code Style

- **Python**: Follow PEP 8. Use type hints where possible.
- **TypeScript/Vue**: Follow the existing ESLint configuration (`@antfu/eslint-config`).

## Pull Request Guidelines

- Keep PRs focused and small
- Write clear commit messages
- Update documentation if your changes affect user-facing features
- Make sure all existing functionality still works

## Reporting Issues

- Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template for bugs
- Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template for new ideas

## License

By contributing to Metora, you agree that your contributions will be licensed under the [Apache License 2.0](./LICENSE).

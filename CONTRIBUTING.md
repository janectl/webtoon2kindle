# 🤝 Contributing to Webtoon2Kindle

Contributions are welcome! Whether you're fixing bugs, improving performance, adding features, or updating documentation, feel free to contribute.

## Getting Started

1. Fork and clone the repository.
2. Create a new branch for your changes.
3. Install dependencies and run the tests:

```bash
pip install -r requirements.txt
pip install pytest
python -m pytest -v
```

4. Make your changes and ensure existing functionality still works.
5. Submit a pull request describing your changes.

## Development Guidelines

- Keep code clean, modular, and easy to maintain.
- Place comic source importers in `web/sources/`.
- Keep conversion and CBZ processing logic in `web/services/`.
- Add or update tests when changing functionality.
- Respect copyright and website access restrictions.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add new functionality
fix: resolve a bug
refactor: improve code structure
test: add or update tests
docs: update documentation
```

## Bug Reports & Feature Requests

Found a bug or have an idea? Open a GitHub Issue with a clear description and relevant details.

Thanks for helping improve Webtoon2Kindle! ❤️
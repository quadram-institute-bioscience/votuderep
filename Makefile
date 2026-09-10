.PHONY: help install install-dev install-docs test lint format clean docs docs-serve

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install package with development dependencies"
	@echo "  make install-docs  - Install documentation dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make docs          - Build documentation (output to docs/)"
	@echo "  make docs-serve    - Serve documentation locally for development"
	@echo "  make clean         - Remove build artifacts"

# Install package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev]"

# Install documentation dependencies
install-docs:
	pip install -e ".[docs]"

# Run tests
test:
	pytest tests/ -v

# Run linters
lint:
	ruff check src/
	mypy src/

# Format code
format:
	ruff format src/
	ruff check --fix src/

# Build documentation
docs:
	@echo "📚 Building documentation..."
	@if command -v mkdocs > /dev/null; then \
		mkdocs build && \
		echo "✅ Documentation built in docs/"; \
	else \
		echo "❌ Error: mkdocs is not installed"; \
		echo "   Install with: make install-docs"; \
		exit 1; \
	fi

# Serve documentation locally
docs-serve:
	@echo "🌐 Serving documentation at http://127.0.0.1:8000"
	@if command -v mkdocs > /dev/null; then \
		mkdocs serve; \
	else \
		echo "❌ Error: mkdocs is not installed"; \
		echo "   Install with: make install-docs"; \
		exit 1; \
	fi

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete"

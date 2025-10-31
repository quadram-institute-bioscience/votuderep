.PHONY: help install install-dev test lint format clean docs

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install package"
	@echo "  make install-dev  - Install package with development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make docs         - Generate documentation"
	@echo "  make clean        - Remove build artifacts"

# Install package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev]"

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

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	@if command -v pdoc > /dev/null; then \
		pdoc -o docs src/votuderep && \
		echo "✅ Documentation generated in docs/"; \
	else \
		echo "❌ Error: pdoc is not installed"; \
		echo "   Install with: pip install pdoc"; \
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

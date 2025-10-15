#!/bin/bash
set -e

echo "================================"
echo "Running code quality checks..."
echo "================================"
echo ""

echo "📝 Checking code formatting with black..."
black --check src/ tests/
echo "✓ Black formatting check passed"
echo ""

echo "🔍 Linting code with ruff..."
ruff check src/ tests/
echo "✓ Ruff linting passed"
echo ""

echo "🧪 Running tests with coverage..."
pytest --cov=votuderep --cov-report=term-missing --cov-report=xml -v
echo "✓ All tests passed"
echo ""

echo "================================"
echo "✅ All checks passed!"
echo "================================"

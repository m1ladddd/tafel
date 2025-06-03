# Makefile for Smart Grid Table Testing

.PHONY: test test-all test-original test-pandapower test-integration test-comprehensive test-performance test-security test-pipeline help clean

# Default target
help:
	@echo "🧪 Smart Grid Table Test Commands"
	@echo "================================="
	@echo "make test-all         - Run complete test pipeline (ALL tests)"
	@echo "make test-original    - Run original unit tests only"
	@echo "make test-pandapower  - Run Pandapower tests only"
	@echo "make test-integration - Run integration tests only"
	@echo "make test-comprehensive - Run comprehensive tests only"
	@echo "make test-performance - Run performance tests only (memory, load, concurrency)"
	@echo "make test-security    - Run security tests only (injection, validation)"
	@echo "make test-pipeline    - Run local test pipeline"
	@echo "make test-app        - Run application smoke test"
	@echo "make test-quick      - Run quick tests (original + integration)"
	@echo "make test-advanced   - Run advanced tests (performance + security)"
	@echo "make clean           - Clean cache files"
	@echo "make help            - Show this help"

# Run complete test pipeline
test-all: test-pipeline

# Run local test pipeline
test-pipeline:
	@echo "🚀 Running complete test pipeline..."
	python run_all_tests.py

# Run original unit tests
test-original:
	@echo "🧪 Running original unit tests..."
	cd test && python run_tests.py

# Run Pandapower tests
test-pandapower:
	@echo "🧪 Running Pandapower tests..."
	cd test && python test_pandapower_implementation.py

# Run integration tests
test-integration:
	@echo "🧪 Running integration tests..."
	cd test && python test_refactored_app.py

# Run comprehensive tests
test-comprehensive:
	@echo "🧪 Running comprehensive tests..."
	cd test && python test_refactored_comprehensive.py

# Run performance tests
test-performance:
	@echo "🚀 Running performance tests (memory, load, concurrency)..."
	cd test && python test_performance_advanced.py

# Run security tests
test-security:
	@echo "🔒 Running security tests (injection, validation)..."
	cd test && python test_security_validation.py

# Run application smoke test
test-app:
	@echo "🧪 Running application smoke test..."
	python -c "from main_controller import MainApplicationController; from app_state import AppState; app_state = AppState(); app_state.simulation_mode = True; controller = MainApplicationController(); controller.app_state.request_shutdown(); print('✅ Application smoke test passed')"

# Run quick tests (faster subset)
test-quick: test-original test-integration
	@echo "✅ Quick tests completed"

# Run advanced tests (performance + security)
test-advanced: test-performance test-security
	@echo "✅ Advanced tests completed"

# Use pytest for discovery
test-pytest:
	@echo "🧪 Running pytest discovery..."
	python -m pytest test/ -v

# Default test target (quick tests)
test: test-quick

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache cleaned" 
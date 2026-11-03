#!/bin/bash
# Test script to validate ops-controller code

set -e

echo "🧪 Testing ops-controller..."

# Check Python syntax
echo "📋 Checking Python syntax..."
python3 -m py_compile config.py
python3 -m py_compile railway_client.py
python3 -m py_compile postgres_configurator.py
python3 -m py_compile digitalocean_manager.py
python3 -m py_compile ops_controller.py

echo "✅ Syntax check passed"

# Try importing modules
echo "📦 Testing imports..."
python3 -c "import config; import railway_client; import postgres_configurator; import digitalocean_manager; import ops_controller"

echo "✅ Import test passed"

# Unit tests (pip install -r requirements.txt -r requirements-dev.txt)
echo "🧪 Running unit tests..."
python3 -m pytest -q tests

echo ""
echo "🎉 All tests passed!"
echo ""
echo "To run the controller:"
echo "  1. Copy .env.example to .env"
echo "  2. Configure your environment variables"
echo "  3. Run: docker-compose up -d"
echo "  4. Monitor: docker-compose logs -f"
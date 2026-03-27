#!/bin/bash
# Quick setup script for Detection as Code pipeline

set -e

echo "Detection as Code Pipeline Setup"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION found"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if sigma CLI is available
echo ""
echo "Checking Sigma CLI..."
if ! command -v sigma &> /dev/null; then
    echo "Sigma CLI not found in PATH. It should have been installed via requirements.txt"
    echo "   Try: pip3 install sigma-cli"
else
    echo "✓ Sigma CLI found"
fi

# Create output directories
echo ""
echo "Creating output directories..."
mkdir -p output/splunk output/kql output/elasticsearch

# Make scripts executable
echo ""
echo "Setting up scripts..."
chmod +x scripts/*.py

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "1. Add your Sigma rules to sigma-rules/<category>/"
echo "2. Run full validation: ./scripts/validate.sh"
echo "3. Convert to Elasticsearch bundle: python3 scripts/convert_sigma.py --backend elasticsearch --bundle-output output/elasticsearch/elasticsearch_bundle_\$(date +%Y%m%d_%H%M%S).json"
echo "4. Push to GitHub to trigger the CI/CD pipeline"
echo ""
echo "For more information, see README.md"

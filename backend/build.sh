#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Download Spacy model for entity extraction
python -m spacy download en_core_web_sm

# Static directory initialization
mkdir -p static/uploads

echo "✅ Build Complete"

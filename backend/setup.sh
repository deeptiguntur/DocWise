#!/bin/bash
set -e

echo "Setting up DocWise AI backend..."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Virtual environment created."
fi

source .venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ".env file created from .env.example — add your API keys."
fi

mkdir -p data/chroma

echo ""
echo "Setup complete. Next steps:"
echo "  1. Add your API keys to .env"
echo "  2. Run: source .venv/bin/activate"
echo "  3. Run: uvicorn main:app --reload"
echo "  4. Open: http://localhost:8000/docs"

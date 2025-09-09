#!/bin/bash
set -e
echo "🛠️  Activating venv..."
source venv/bin/activate 2>/dev/null || { echo "❌ Activate venv first"; exit 1; }
echo "🔐 Loading .env..."
export $(cat .env | xargs)
echo "🚀 Starting bot..."
python -m src.app

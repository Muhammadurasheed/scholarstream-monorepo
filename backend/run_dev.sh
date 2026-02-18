#!/bin/bash

# ScholarStream Backend Development Runner
# بسم الله الرحمن الرحيم

echo "🚀 Starting ScholarStream Backend..."
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create .env file from .env.example"
    echo "   cp .env.example .env"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Warning: Redis server not running"
    echo "   Start Redis: brew services start redis (macOS)"
    echo "              : sudo systemctl start redis (Linux)"
    echo "   Or: docker run -d -p 6379:6379 redis:latest"
    echo ""
fi

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $python_version"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the server
echo ""
echo "✅ Starting FastAPI server..."
echo "📍 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🏥 Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo "=================================="

python -m app.main

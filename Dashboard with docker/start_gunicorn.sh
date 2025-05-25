#!/bin/bash

# Startup script for Security Dashboard with Gunicorn
set -e

echo "🚀 Starting Security Dashboard with Gunicorn..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📋 Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Load environment variables
if [ -f ".env" ]; then
    echo "🔐 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Create logs directory
mkdir -p logs

echo "✅ Starting application with Gunicorn..."
echo "🌐 Application will be available at: http://localhost:${PORT:-5000}"
echo "📊 Dashboard URL: http://localhost:${PORT:-5000}/"
echo "📋 API Health Check: http://localhost:${PORT:-5000}/api/ping"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Gunicorn with configuration
gunicorn --config gunicorn.conf.py flaskkk:app

#!/bin/bash
set -e

echo "=========================================="
echo "  Bid Announce System - QA & Deploy"
echo "=========================================="

echo ""
echo "Step 1: Backend QA"
echo "------------------------------------------"
echo "Running ruff lint..."
ruff check src/ scripts/ tests/

echo "Running ruff format check..."
ruff format --check src/ scripts/ tests/

echo "Running pytest..."
pytest tests/ -v --cov=src --cov-report=term-missing

echo ""
echo "Step 2: Frontend QA"
echo "------------------------------------------"
echo "Installing frontend dependencies..."
cd frontend
npm ci

echo "Running TypeScript type check..."
npx tsc --noEmit

echo "Running ESLint..."
npx eslint src/ || true

echo "Running Vitest tests..."
npm run test:run

echo "Building frontend..."
npm run build

cd ..

echo ""
echo "Step 3: Deploy"
echo "------------------------------------------"
echo "Copying frontend build to web directory..."
rm -rf web
cp -r frontend/dist web

echo "Restarting backend server..."
if command -v pkill &> /dev/null; then
    pkill -f "uvicorn src.api.app:app" || true
fi

echo "Starting server..."
python scripts/start_server.py --no-browser &
SERVER_PID=$!

echo ""
echo "Waiting for server to start..."
sleep 3

echo ""
echo "Checking health endpoint..."
curl -f http://localhost:8000/api/health || echo "Server may still be starting..."

echo ""
echo "=========================================="
echo "  QA & Deploy Complete!"
echo "  Frontend: http://localhost:8000/"
echo "  API Docs: http://localhost:8000/docs"
echo "=========================================="

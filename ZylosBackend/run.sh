#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="venv"

echo "[run.sh] Preparing virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
if [ -f "$VENV_DIR/bin/activate" ]; then
  source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
  source "$VENV_DIR/Scripts/activate"
fi

echo "[run.sh] Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[run.sh] Initializing DB and folders..."
python scripts/init_db.py

echo "[run.sh] Starting scheduler (background)..."
nohup python -u app/services/scheduler.py > app/logs/scheduler.log 2>&1 &

echo "[run.sh] Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#chmod +x run.sh
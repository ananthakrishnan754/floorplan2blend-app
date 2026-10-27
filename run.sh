#!/bin/bash
# ==============================================================
# Floorplan to Blender 3D Generator - Linux/macOS Launcher
# ==============================================================
set -e

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting Web App at http://localhost:5000..."
python3 app.py

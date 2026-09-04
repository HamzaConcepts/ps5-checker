#!/usr/bin/env bash
echo "==================================================="
echo "    Starting PlayStation 5 Stock Monitor Bot"
echo "==================================================="

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt --quiet

echo "Launching PS5 Stock Monitor..."
python3 main.py

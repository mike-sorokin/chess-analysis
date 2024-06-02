#!/usr/bin/env sh

python -m venv venv
. venv/bin/activate
pip install -q -r requirements.txt

python main.py ./stockfish $1

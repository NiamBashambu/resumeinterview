#!/bin/bash
# Run the backend server
cd "$(dirname "$0")"
python3 -m uvicorn backend.main:app --reload --port 8000


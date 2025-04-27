#!/bin/bash
# Run FastAPI app with uvicorn

uvicorn app:app --reload --host 0.0.0.0 --port 8002

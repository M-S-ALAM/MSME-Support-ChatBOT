#!/bin/bash
# Run FastAPI app with uvicorn

# Note: You may see a warning about dependency conflicts (e.g., pyasn1-modules vs pyasn1).
# If your application works as expected, you can ignore this warning.
# If you encounter issues, consider running:
# pip install 'pyasn1<0.7.0,>=0.6.1'

uvicorn app:app --reload

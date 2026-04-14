"""Entry point for Vercel Python serverless function."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import app  # noqa: E402,F401

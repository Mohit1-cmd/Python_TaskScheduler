# conftest.py — pytest configuration
# Adds the project root to sys.path so imports like `from app.x import y` work from tests/
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

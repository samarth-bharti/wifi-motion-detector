"""Make `src/` importable in tests (so `import wifi_reader` works)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

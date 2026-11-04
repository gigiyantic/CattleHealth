import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("CH_DISABLE_SWEEPER", "1")
os.environ.setdefault("CH_DB_PATH", ":memory:")

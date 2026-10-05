import os
import tempfile

# Point the app at a throwaway sqlite file before any app module is imported.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp(prefix='hallspan-test-')}/test.db"

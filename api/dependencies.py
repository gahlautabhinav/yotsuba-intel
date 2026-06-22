from storage.engine import init_db
from storage.repository import Repository


def get_repo() -> Repository:
    """FastAPI dependency — returns a Repository instance (DB already initialized)."""
    return Repository()

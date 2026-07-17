"""PostgreSQL connection handling for the vehicle catalog."""

import os
from contextlib import contextmanager

import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/whogapswho"
)

_pool = None


def _get_pool():
    # Created lazily so importing this module (or starting the app) doesn't
    # require Postgres to already be reachable.
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(1, 5, DATABASE_URL)
    return _pool


@contextmanager
def get_cursor():
    """Yield a cursor for one unit of work; commits on success, rolls back on error."""
    conn = _get_pool().getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)

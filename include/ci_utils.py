import sqlalchemy
from sqlalchemy.engine import URL
from functools import lru_cache
from include.aws_secrets import get_db_credentials

DB_NAME_MAP = {
    "dev": "champs_qa",
    "stg": "champs_stg",
    "prod": "champs_prod",
}


def _build_url(env):
    creds = get_db_credentials(env)
    database = creds.get("database") or DB_NAME_MAP.get(env, "champs_qa")
    return URL.create(
        "mssql+pyodbc",
        username=creds["username"],
        password=creds["password"],
        host=creds["host"],
        port=creds.get("port", 1433),
        database=database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "TrustServerCertificate": "yes",
        },
    )


@lru_cache(maxsize=4)
def get_engine(env):
    return sqlalchemy.create_engine(_build_url(env))


# Backward compatibility: existing code can still use connect_db.conn_qa etc.
# Lazily created on first access to avoid cross-env auth at import time.
class _ConnectDB:
    _lazy = {"conn_prod": "prod", "conn_qa": "dev", "conn_stg": "stg"}

    def __getattr__(self, name):
        if name in self._lazy:
            engine = get_engine(self._lazy[name])
            setattr(self, name, engine)
            return engine
        raise AttributeError(f"connect_db has no attribute {name}")


connect_db = _ConnectDB()

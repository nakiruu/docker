import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI",
    "postgresql+psycopg2://superset:superset@superset-db:5432/superset",
)

_REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
_REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

_CACHE_BASE = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_REDIS_HOST": _REDIS_HOST,
    "CACHE_REDIS_PORT": _REDIS_PORT,
}

CACHE_CONFIG                = {**_CACHE_BASE, "CACHE_KEY_PREFIX": "superset_",        "CACHE_REDIS_DB": 1}
DATA_CACHE_CONFIG           = {**_CACHE_BASE, "CACHE_KEY_PREFIX": "superset_data_",   "CACHE_REDIS_DB": 2}
FILTER_STATE_CACHE_CONFIG   = {**_CACHE_BASE, "CACHE_KEY_PREFIX": "superset_filter_", "CACHE_REDIS_DB": 3}
EXPLORE_FORM_DATA_CACHE_CONFIG = {**_CACHE_BASE, "CACHE_KEY_PREFIX": "superset_explore_", "CACHE_REDIS_DB": 4}

WTF_CSRF_ENABLED  = True
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365
TALISMAN_ENABLED  = False

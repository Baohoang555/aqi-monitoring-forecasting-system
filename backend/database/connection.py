from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from configuration")

# Support both mysql:// and mysql+pymysql:// URL schemes
db_url = DATABASE_URL
if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

engine = create_engine(
    db_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

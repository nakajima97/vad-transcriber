from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

db_engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
db_session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

Base = declarative_base()


def get_db():
    """データベースセッションの依存性注入用関数"""
    with db_session() as session:
        yield session

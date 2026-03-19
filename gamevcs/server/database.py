import os
from typing import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from gamevcs.server.models import Base


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None

    def init(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        if self.engine:
            self.engine.dispose()


_db_instance: Database = None


def get_db() -> Generator[Session, None, None]:
    global _db_instance
    db = _db_instance.get_session()
    try:
        yield db
    finally:
        db.close()


def init_db(db_path: str) -> Database:
    global _db_instance
    _db_instance = Database(db_path)
    _db_instance.init()
    return _db_instance

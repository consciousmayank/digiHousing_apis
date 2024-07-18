from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import config

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
            cls._instance.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._instance.engine)
        return cls._instance

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db = Database()
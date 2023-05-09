from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from utils import Config


config = Config()

DATABASE_URL = config.get("database", "url")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session = sessionmaker(engine, expire_on_commit=False, autoflush=False, class_=AsyncSession)


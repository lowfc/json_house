from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Text, Integer, String, JSON, ForeignKey, Sequence

Base = declarative_base()


class Room(Base):
    """
    Room - is a table which stores a list of created requests.
    """
    __tablename__ = 'room'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    uri_hash = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime)
    content = Column(Text, nullable=False, default="")
    headers = Column(JSON, nullable=False, default="{}")
    require_parameters = Column(JSON, nullable=False, default="{}")
    on_invalid_status_code = Column(Integer, nullable=False, default=200)
    wait_microseconds = Column(Integer, nullable=False, default=0)
    content_type_id = Column(Integer, ForeignKey("content_type.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)


class ContentType(Base):
    """
    ContentType - is a table which stores a list of available content type
    """
    __tablename__ = 'content_type'

    id = Column(Integer, primary_key=True)
    type_name = Column(Text, nullable=False, index=True, unique=True)
    validate_as = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime, default=None)


class DisallowedHeaders(Base):
    """
    DisallowedHeaders - is a table which stores a list of disallowed HTTP headers.
    """
    __tablename__ = 'disallowed_headers'

    id = Column(Integer, primary_key=True)
    header_name = Column(Text, nullable=False, index=True, unique=True)


class Session(Base):
    """
    Session - is a table which stores a list of user session.
    """
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    token = Column(Text, nullable=False, index=True, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime)
    user_agent = Column(Text)


RequestIdSeq = Sequence('user_request_id_seq')  # sequence using for get in request id

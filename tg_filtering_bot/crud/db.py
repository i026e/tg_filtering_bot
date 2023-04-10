import enum

from sqlalchemy import Column, Integer, Enum, String, ForeignKey, DateTime, Boolean, func, PrimaryKeyConstraint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from tg_filtering_bot.config import settings

Base = declarative_base()


class Status(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    status = Column(Enum(Status), nullable=False)

    time_created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class ChatUser(Base):
    __tablename__ = "chat_user"

    chat_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    time_created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Filter(Base):
    __tablename__ = "filter"

    filter_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    filter_ = Column(String, nullable=False)
    status = Column(Enum(Status), nullable=False)

    time_created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


class Message(Base):
    __tablename__ = "message"

    message_id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    message = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserMessage(Base):
    __tablename__ = "user_message"

    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    message_id = Column(Integer, ForeignKey("message.message_id"), nullable=False)

    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed = Column(Boolean, nullable=False)
    pk = PrimaryKeyConstraint(user_id, message_id)


engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

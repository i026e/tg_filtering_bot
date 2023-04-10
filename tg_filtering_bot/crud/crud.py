from typing import List, Optional

from sqlalchemy import select, update

from tg_filtering_bot.crud.db import Message, async_session, User, Status, ChatUser, Filter, UserMessage
from tg_filtering_bot.crud.dto import QueueMessageDTO, UserChatDTO, UserFilterDTO
from tg_filtering_bot.crud.schema import UserId, MessageId


async def add_message_to_db(queue_message: QueueMessageDTO) -> Message:
    db_message = Message(
        message_id=queue_message.message_id,
        channel_id=queue_message.channel_id,
        message=queue_message.message,
        date=queue_message.date
    )
    async with async_session() as session:
        session.add(db_message)
        await session.commit()

    return db_message


async def create_user_message(
    user_id: UserId, message_id: MessageId, processed: bool = False
) -> UserMessage:
    db_user_message = UserMessage(
        user_id=user_id,
        message_id=message_id,
        processed=processed
    )

    async with async_session() as session:
        session.add(db_user_message)
        await session.commit()

    return db_user_message


async def mark_user_message_as_processed(db_user_message: UserMessage) -> None:
    async with async_session() as session:
        db_user_message.processed = True
        session.add(db_user_message)
        await session.commit()


async def create_or_update_user_chat(user_chat: UserChatDTO) -> None:
    db_user = User(
        user_id=user_chat.user_id,
        name=user_chat.name,
        username=user_chat.username,
        language_code=user_chat.language_code,
        status=Status.ACTIVE
    )

    db_chat_user = ChatUser(
        chat_id=user_chat.chat_id,
        user_id=user_chat.user_id
    )

    async with async_session() as session:
        user_update = await session.merge(db_user)
        session.add(user_update)

        chat_update = await session.merge(db_chat_user)
        session.add(chat_update)

        await session.commit()


async def get_latest_user_chat(user_id: UserId) -> Optional[UserChatDTO]:
    query = select(
        ChatUser.user_id,
        ChatUser.chat_id,
        User.name,
        User.username,
        User.language_code
    ).select_from(
        ChatUser
    ).join(
        User, User.user_id == ChatUser.user_id
    ).filter(
        ChatUser.user_id == user_id
    ).filter(
        User.status == Status.ACTIVE
    ).order_by(
        ChatUser.time_created.desc()
    )
    async with async_session() as session:
        result = (await session.execute(query)).first()
        if result:
            return UserChatDTO(
                user_id=result.user_id,
                chat_id=result.chat_id,
                name=result.name,
                username=result.username,
                language_code=result.language_code
            )
    return None


async def add_filter(user_filter: UserFilterDTO) -> None:
    db_filter = Filter(

        user_id=user_filter.user_id,
        filter_=user_filter.filter_,
        status=Status.ACTIVE
    )
    async with async_session() as session:
        session.add(db_filter)
        await session.commit()


async def disable_filter(user_filter: UserFilterDTO) -> None:
    query = update(Filter).where(
        Filter.user_id == user_filter.user_id
    ).where(
        Filter.filter_id == user_filter.filter_id
    ).values(
        status=Status.INACTIVE
    )

    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_active_filters() -> List[UserFilterDTO]:
    query = select(
        User.user_id, Filter.filter_, Filter.filter_id
    ).select_from(
        Filter
    ).join(
        User, User.user_id == Filter.user_id
    ).filter(
        User.status == Status.ACTIVE
    ).filter(
        Filter.status == Status.ACTIVE
    )

    async with async_session() as session:
        result = (await session.execute(query)).all()

        return [UserFilterDTO(user_id=r.user_id, filter_=r.filter_, filter_id=r.filter_id) for r in result]


async def get_user_filters(user_id: UserId) -> List[UserFilterDTO]:
    query = select(
        Filter.filter_id, Filter.filter_
    ).select_from(
        Filter
    ).filter(
        Filter.status == Status.ACTIVE
    ).filter(
        Filter.user_id == user_id
    ).order_by(
        Filter.time_created.asc()
    )

    async with async_session() as session:
        result = (await session.execute(query)).all()
        return [
            UserFilterDTO(filter_id=r.filter_id, filter_=r.filter_, user_id=user_id)
            for r in result
        ]

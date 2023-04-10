import dataclasses
import datetime

from tg_filtering_bot.crud.schema import UserId, MessageId, ChatId


@dataclasses.dataclass
class QueueMessageDTO:
    message_id: MessageId
    channel_id: ChatId
    message: str
    date: datetime.datetime


@dataclasses.dataclass
class UserChatDTO:
    user_id: UserId
    chat_id: ChatId
    name: str
    username: str
    language_code: str


@dataclasses.dataclass
class UserFilterDTO:
    user_id: UserId
    filter_: str
    filter_id: int


@dataclasses.dataclass
class ForwardMessageDTO:
    message: QueueMessageDTO
    user_chat: UserChatDTO

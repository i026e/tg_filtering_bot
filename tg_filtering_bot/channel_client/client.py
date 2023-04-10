import atexit
import multiprocessing
from typing import Any

from telethon import TelegramClient, events

from tg_filtering_bot.async_queue import AsyncQueue
from tg_filtering_bot.config import settings
from tg_filtering_bot.crud.dto import QueueMessageDTO
from tg_filtering_bot.crud.schema import ChatId
from tg_filtering_bot.logger import get_logger


class MonitoringClient:
    LOGGER = get_logger("MonitoringClient")

    def __init__(self, message_queue: AsyncQueue) -> None:

        self.client = TelegramClient(
            settings.LISTENER_API_NAME, settings.LISTENER_API_ID, settings.LISTENER_API_HASH
        )
        self.LOGGER.info("Client Created")

        self.client.add_event_handler(
            self.event_handler,
            events.NewMessage(chats=settings.LISTENER_CHANNEL_ID)
        )

        self.queue = message_queue

    async def load_old_messages(self, limit: int) -> None:
        async for message in self.client.iter_messages(entity=settings.LISTENER_CHANNEL_ID, limit=limit):
            await self.queue.put(QueueMessageDTO(
                message_id=message.id,
                channel_id=ChatId(message.chat_id),
                message=str(message.message),
                date=message.date
            ))

    def start(self) -> None:
        self.client.start()
        self.LOGGER.info("Client Started")

        if settings.LISTENER_LOAD_PREV_MESSAGES > 0:
            self.client.loop.create_task(self.load_old_messages(settings.LISTENER_LOAD_PREV_MESSAGES))

        self.client.run_until_disconnected()

    async def event_handler(self, event: Any) -> None:
        self.LOGGER.info("Event %s", event)

        await self.queue.put(QueueMessageDTO(
            message_id=event.id,
            channel_id=ChatId(event.message.chat_id),
            message=str(event.message.message),
            date=event.date
        ))


def start_monitoring_process() -> AsyncQueue[QueueMessageDTO]:
    queue: multiprocessing.Queue[QueueMessageDTO] = multiprocessing.Queue(maxsize=settings.QUEUE_SIZE)
    async_queue = AsyncQueue(queue)
    monitoring_client = MonitoringClient(async_queue)

    process = multiprocessing.Process(target=monitoring_client.start)
    process.start()
    atexit.register(process.join)

    return async_queue


def main():
    queue = start_monitoring_process()
    queue.sync_queue.get()


if __name__ == "__main__":
    main()

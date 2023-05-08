import atexit
import multiprocessing
import time
from typing import Any

from telethon import TelegramClient, events

from tg_filtering_bot.async_queue import AsyncQueue
from tg_filtering_bot.config import settings
from tg_filtering_bot.crud.dto import QueueMessageDTO
from tg_filtering_bot.crud.schema import ChatId
from tg_filtering_bot.logger import get_logger


class MonitoringClient:
    LOGGER = get_logger("MonitoringClient")

    @classmethod
    def create_client(cls) -> TelegramClient:
        cls.LOGGER.info(
            "Creating client for %s, %s", settings.LISTENER_API_NAME, settings.LISTENER_API_ID
        )
        return TelegramClient(
            settings.LISTENER_API_NAME, settings.LISTENER_API_ID, settings.LISTENER_API_HASH
        )

    def __init__(self, message_queue: AsyncQueue) -> None:
        self.client = self.create_client()

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
        self.client.start(phone=settings.LISTENER_PHONE, password=settings.LISTENER_PASSWORD)
        self.LOGGER.info("Client Started")

        if settings.LISTENER_LOAD_PREV_MESSAGES > 0:
            self.client.loop.create_task(self.load_old_messages(settings.LISTENER_LOAD_PREV_MESSAGES))

        safe_exit = False
        while not safe_exit:
            try:
                self.client.run_until_disconnected()
                safe_exit = True
            except Exception as e:
                self.LOGGER.exception(e)

    async def event_handler(self, event: Any) -> None:
        self.LOGGER.info("Event %s", event)

        await self.queue.put(QueueMessageDTO(
            message_id=event.id,
            channel_id=ChatId(event.message.chat_id),
            message=str(event.message.message),
            date=event.date
        ))

    @classmethod
    def login(cls) -> None:
        session_file = settings.BASE_DIR / (settings.LISTENER_API_NAME + ".session")
        session_file.unlink(missing_ok=True)

        client = cls.create_client()
        client.start(
            phone=settings.LISTENER_PHONE, password=settings.LISTENER_PASSWORD
        )


def start_monitoring_process() -> AsyncQueue[QueueMessageDTO]:
    queue: multiprocessing.Queue[QueueMessageDTO] = multiprocessing.Queue(maxsize=settings.QUEUE_SIZE)
    async_queue = AsyncQueue(queue)
    monitoring_client = MonitoringClient(async_queue)

    process = multiprocessing.Process(target=monitoring_client.start)
    process.start()
    atexit.register(process.join)

    time.sleep(1)
    if process.exitcode is not None:
        raise RuntimeError("MonitoringClient closed after launch")

    return async_queue


def main() -> None:
    queue = start_monitoring_process()
    queue.sync_queue.get()


def login() -> None:
    MonitoringClient.login()


if __name__ == "__main__":
    main()

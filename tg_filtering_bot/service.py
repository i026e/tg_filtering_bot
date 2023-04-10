import asyncio

from tg_filtering_bot.async_queue import AsyncQueue
from tg_filtering_bot.crud.crud import (
    add_message_to_db,
    mark_user_message_as_processed,
    get_active_filters,
    get_latest_user_chat, create_user_message
)
from tg_filtering_bot.crud.dto import QueueMessageDTO, ForwardMessageDTO
from tg_filtering_bot.logger import get_logger
from tg_filtering_bot.matcher import match_user_filters


class MainService:
    LOGGER = get_logger("MainService")

    def __init__(
        self, channel_queue: AsyncQueue, bot_message_queue: AsyncQueue
    ) -> None:
        self._channel_queue = channel_queue
        self._bot_message_queue = bot_message_queue

    async def process_channel_message(self, message: QueueMessageDTO) -> None:
        self.LOGGER.info("Processing message, %s", message)

        try:
            await add_message_to_db(message)
        except Exception as e:
            self.LOGGER.error(e)
            return

        active_filters = await get_active_filters()
        loop = asyncio.get_event_loop()
        user_ids = await loop.run_in_executor(None, match_user_filters, message, active_filters)

        for user_id in user_ids:
            try:
                user_message = await create_user_message(message_id=message.message_id, user_id=user_id)
                user_chat = await get_latest_user_chat(user_id)
                if user_chat:
                    await self._bot_message_queue.put(ForwardMessageDTO(
                        message=message,
                        user_chat=user_chat
                    ))
                    await mark_user_message_as_processed(user_message)
            except Exception as e:
                self.LOGGER.exception(e)

    async def serve(self) -> None:
        while True:
            try:
                message = await self._channel_queue.get()
                await self.process_channel_message(message)
            except Exception as e:
                self.LOGGER.exception(e)


def start_service(
    channel_queue: AsyncQueue, bot_message_queue: AsyncQueue
) -> None:
    service = MainService(
        channel_queue=channel_queue,
        bot_message_queue=bot_message_queue
    )
    asyncio.run(service.serve())

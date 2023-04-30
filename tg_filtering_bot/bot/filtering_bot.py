import asyncio
import atexit
import dataclasses
import multiprocessing
from typing import Any, Dict


from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageToForwardNotFound, ChatNotFound
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from tg_filtering_bot.async_queue import AsyncQueue
from tg_filtering_bot.config import settings
from tg_filtering_bot.crud.crud import (
    create_or_update_user_chat,
    add_filter,
    get_user_filters,
    disable_filter
)
from tg_filtering_bot.crud.dto import UserFilterDTO, UserChatDTO, ForwardMessageDTO
from tg_filtering_bot.logger import get_logger


I18N = I18nMiddleware(settings.I18N_DOMAIN, settings.LOCALES_DIR)
_ = I18N.gettext


class UserState(StatesGroup):
    adding = State()
    deleting = State()


@dataclasses.dataclass
class DeleteFilterData:
    order: int
    button: InlineKeyboardButton
    filter_: UserFilterDTO


def build_delete_filters_markup(
    storage_data: Dict[str, DeleteFilterData]
) -> InlineKeyboardMarkup:
    inline_kb = InlineKeyboardMarkup()

    delete_filters_data = [d for d in storage_data.values() if isinstance(d, DeleteFilterData)]
    for data in sorted(delete_filters_data, key=lambda d: d.order):
        inline_kb.add(data.button)
    return inline_kb


class FilteringBot:
    LOGGER = get_logger("FilteringBot")
    _BTN_DELETE_PREFIX = "delete_"

    def __init__(self, message_queue: AsyncQueue) -> None:
        self._message_queue = message_queue

        self.storage = MemoryStorage()
        self.bot = Bot(settings.BOT_TOKEN)
        self.dispatcher = Dispatcher(self.bot, storage=self.storage)
        self.dispatcher.middleware.setup(I18N)

        self.LOGGER.info("Bot created")

        self.dispatcher.register_message_handler(
            self.start_command,
            commands=['start'],
            state="*"
        )

        self.dispatcher.register_message_handler(
            self.add_command,
            commands=['add'],
            state="*"
        )

        self.dispatcher.register_message_handler(
            self.delete_command,
            commands=['delete'],
            state="*"
        )

        self.dispatcher.register_message_handler(
            self.list_command,
            commands=['list'],
            state="*"
        ),

        self.dispatcher.register_message_handler(
            self.cancel_command,
            commands=['cancel'],
            state="*"
        ),
        self.dispatcher.register_message_handler(
            self.add_address,
            state=UserState.adding
        ),

        self.dispatcher.register_callback_query_handler(
            self.delete_address,
            Text(startswith=self._BTN_DELETE_PREFIX),
            state=UserState.deleting
        )

    async def _set_base_commands(self) -> None:
        await self.bot.delete_my_commands()
        await self.bot.set_my_commands(commands=[
            BotCommand(
                command="add",
                description=_("Add new address")
            ),
            BotCommand(
                command="list",
                description=_("List addresses")
            ),
            BotCommand(
                command="delete",
                description=_("Delete address")
            ),
            BotCommand(
                command="cancel",
                description=_("Cancel previous command")
            ),
        ])

    async def _register_user(self, message: Any) -> None:
        if message:
            self.LOGGER.info("Adding or updating user %s, chat %s", message.from_user.id, message.chat.id)

            user_chat_dto = UserChatDTO(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                name=message.from_user.full_name,
                username=message.from_user.username,
                language_code=message.from_user.language_code
            )
            await create_or_update_user_chat(user_chat_dto)

    async def _process_message_queue(self) -> None:
        message = await self._message_queue.get()
        if isinstance(message, ForwardMessageDTO):
            return await self.forward_message(message)

        raise NotImplementedError(f"Processing for {message} is not implemented")

    async def _periodic(self) -> None:
        while True:
            try:
                await self._process_message_queue()
            except Exception as e:
                self.LOGGER.exception(e)

    def start_bot(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self._set_base_commands())
        loop.create_task(self._periodic())
        executor.start_polling(self.dispatcher, loop=loop)

    def stop_bot(self) -> None:
        self.dispatcher.stop_polling()

    async def _clear_state(self, state: FSMContext) -> None:
        await state.reset_state()
        await state.reset_data()
        await self._set_base_commands()

    async def start_command(self, message: Message, state: FSMContext) -> None:
        await self._register_user(message)
        await self._clear_state(state)

        await message.reply(_("""Hi there,
I am a filtering bot for '{channel}' channel. 
Please use command {command} to add a new address.""").format(
            channel=settings.LISTENER_CHANNEL_NAME, command="/add"
        ))

    async def add_command(self, message: Message, state: FSMContext) -> None:
        await self._register_user(message)

        await state.set_state(UserState.adding)
        await self.bot.send_message(message.chat.id, _("Please type street name to create a filter"))

    async def delete_command(self, message: Message, state: FSMContext) -> None:
        await self._register_user(message)

        filters = await get_user_filters(user_id=message.from_user.id)

        if not filters:
            return await message.reply(_("You have no addresses to delete"))

        await state.set_state(UserState.deleting)

        storage_data = {}

        for i, f in enumerate(filters, start=1):
            key = f"{self._BTN_DELETE_PREFIX}{f.filter_id}"
            storage_data[key] = DeleteFilterData(
                order=i,
                filter_=f,
                button=InlineKeyboardButton(
                    _("{i}. Delete {address}").format(i=i, address=f.filter_),
                    callback_data=key
                )
            )
        await state.set_data(storage_data)
        inline_kb = build_delete_filters_markup(storage_data)
        await message.reply(_("Click addresses to delete"), reply_markup=inline_kb)

    async def list_command(self, message: Message, state: FSMContext) -> Message:
        await self._register_user(message)

        filters = await get_user_filters(user_id=message.from_user.id)
        if not filters:
            return await message.reply(_("You have no addresses"))

        response = _("You addresses are:") + "\r\n" + "\r\n".join(
            f"{i}. {f.filter_}" for i, f in enumerate(filters, start=1)
        )

        return await message.reply(response)

    async def cancel_command(self, message: Message, state: FSMContext) -> None:
        await self._register_user(message)
        await self._clear_state(state)

    async def add_address(self, message: Message, state: FSMContext) -> None:
        await self._register_user(message)

        address = message.text
        self.LOGGER.info("Adding new address: %s", message)

        user_filter = UserFilterDTO(user_id=message.from_user.id, filter_=address, filter_id=-1)
        await add_filter(user_filter)

#        await self.bot.delete_state(message.from_user.id, message.chat.id)
        await self.bot.send_message(
            message.chat.id, _("Filter '{address}' was added for monitoring").format(address=address)
        )
        await self._clear_state(state)

    async def delete_address(self, event: CallbackQuery, state: FSMContext) -> Message:
        self.LOGGER.warning(event)

        storage_data = await state.get_data()

        if not storage_data or event.data not in storage_data:
            return await event.message.answer(_("No address to delete"))

        delete_filter_data = storage_data.pop(event.data)
        await disable_filter(delete_filter_data.filter_)

        await state.set_data(storage_data)

        await event.message.edit_reply_markup(build_delete_filters_markup(storage_data))
        return await event.message.answer(
            _("Filter '{address}' was deleted").format(address=delete_filter_data.filter_.filter_)
        )

    async def send_message_to_user(self, forward_message: ForwardMessageDTO) -> None:
        self.LOGGER.debug(
            "Sending message %s to user %s", forward_message.message.message_id, forward_message.user_chat.user_id
        )

        await self.bot.send_message(
            forward_message.user_chat.chat_id,
            forward_message.message.message
        )

    async def forward_message(self, forward_message: ForwardMessageDTO) -> None:
        self.LOGGER.debug(
            "Forwarding message %s to user %s", forward_message.message.message_id, forward_message.user_chat.user_id
        )

        try:
            await self.bot.forward_message(
                forward_message.user_chat.chat_id,
                from_chat_id=forward_message.message.channel_id,
                message_id=forward_message.message.message_id
            )
        except (MessageToForwardNotFound, ChatNotFound):
            self.LOGGER.warning(
                "Cannot forward message %s", forward_message.message.message_id
            )
            return await self.send_message_to_user(forward_message)


def start_filtering_bot() -> AsyncQueue[ForwardMessageDTO]:
    queue: multiprocessing.Queue[ForwardMessageDTO] = multiprocessing.Queue(maxsize=settings.QUEUE_SIZE)
    message_queue = AsyncQueue(queue)

    bot = FilteringBot(
        message_queue=message_queue
    )

    process = multiprocessing.Process(target=bot.start_bot)
    process.start()
    atexit.register(bot.stop_bot)
    atexit.register(process.join)

    return message_queue

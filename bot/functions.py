from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async

from users.models import User


def contact_request_btn():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Phone Number", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb


async def set_telegram_id_if_null(user_id: int, telegram_id: int) -> bool:
    def _update():
        return User.objects.filter(id=user_id, telegram_id__isnull=True).update(telegram_id=telegram_id)

    updated = await sync_to_async(_update, thread_sensitive=True)()
    return bool(updated)


async def get_user_by_phone(phone: str):
    return await sync_to_async(lambda: User.objects.filter(phone_number=phone).first(), thread_sensitive=True)()


async def get_user_by_chat_id(chat_id: int):
    return await sync_to_async(lambda: User.objects.filter(telegram_id=chat_id).first(), thread_sensitive=True)()
import os
import sys
import logging
import asyncio

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoursePlatform.settings")
django.setup()

from utils import OtpService
from bot.functions import contact_request_btn, get_user_by_phone, set_telegram_id_if_null, get_user_by_chat_id
from asgiref.sync import sync_to_async
from users.models import User

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 5430618568  # Your chat ID for error logs

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def send_error_log(error_message: str):
    \"\"\"Sends error logs to the admin.\"\"\"
    try:
        await bot.send_message(ADMIN_CHAT_ID, f"🚨 <b>Bot Error:</b>\n<pre>{error_message}</pre>")
    except Exception as e:
        logging.error(f"Failed to send error log to admin: {e}")

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    try:
        # Check if user is already registered and linked
        user = await get_user_by_chat_id(message.from_user.id)
        if user:
            await message.answer("Welcome back! You are already registered.", reply_markup=ReplyKeyboardRemove())
            return
            
        await message.answer("👋 Welcome to IlmSpace Bot!\n\nPlease share your phone number to receive your verification code.", reply_markup=contact_request_btn())
    except Exception as e:
        logging.exception("Error in start handler")
        await send_error_log(f"Start Handler Error: {str(e)}")
        await message.answer("An error occurred. Please try again later.")


@dp.message(F.contact)
async def contact_handler(message: Message) -> None:
    try:
        print("Received contact:", message.contact)
        print("Phone number from contact:", message.contact.phone_number)
        # Normalize phone number (keep only digits)
        phone_variant = ""
        for i in message.contact.phone_number:
            if i.isdigit():
                phone_variant += i
                
        # Check if user exists in DB (Login scenario)
        user = await get_user_by_phone(phone_variant)
        print("Found user:", user)
        print("Phone variant:", phone_variant)
        if user:
            # Link telegram_id if not set
            if not user.telegram_id:
                await set_telegram_id_if_null(user.id, message.from_user.id)
                
            # Check for login OTP
            otp_service = OtpService()
            otp = await asyncio.to_thread(otp_service.get_otp, phone_variant, "login")
            
            if otp:
                await message.answer(f"🔐 Your login code: {otp}", reply_markup=ReplyKeyboardRemove())
            else:
                await message.answer("✅ Account linked! You can now request a login code from the website.", reply_markup=ReplyKeyboardRemove())
            return

        # Registration scenario
        otp_service = OtpService()
        
        # Check if there is a pending registration OTP for this phone
        otp = await asyncio.to_thread(otp_service.get_otp, phone_variant, "register")
        
        if otp:
            await message.answer(f"📝 Your registration code: {otp}", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("⚠️ No pending registration found.\n\nPlease go to the website and fill out the registration form first.", reply_markup=ReplyKeyboardRemove())
            
    except Exception as e:
        logging.exception("Error in contact handler")
        await send_error_log(f"Contact Handler Error: {str(e)}")
        await message.answer("An error occurred while processing your request.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

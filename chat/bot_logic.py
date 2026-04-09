import os
import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from typing import Callable, Dict, Any, Awaitable

# 1. Sozlamalar
GEMINI_API_KEY = "AIzaSyAT2RIQazbGtuyMT_tRlNM3tGknq2iV7m4"
TELEGRAM_BOT_TOKEN = "8211385005:AAF0TbvnIC7URB2eMTRrS_e9GGUXT0xf_iE"
CHANNELS = ["@ss_kk_kk_dd"] # Tekshirilishi kerak bo'lgan kanallar ro'yxati

genai.configure(api_key=GEMINI_API_KEY)
session = AiohttpSession(timeout=40)
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
dp = Dispatcher()

# --- MAJBURIY OBUNA MIDDLEWARE ---
class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        for channel in CHANNELS:
            try:
                member = await event.bot.get_chat_member(chat_id=channel, user_id=event.from_user.id)
                if member.status in ["left", "kicked"]:
                    raise Exception("Not subscribed")
            except Exception:
                # Obuna bo'lmagan bo'lsa, tugma ko'rsatish
                buttons = [[InlineKeyboardButton(text="Kanalga obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}")]]
                markup = InlineKeyboardMarkup(inline_keyboard=buttons)
                return await event.answer(
                    f"Botdan foydalanish uchun quyidagi kanalga obuna bo'lishingiz shart: {channel}",
                    reply_markup=markup
                )
        
        return await handler(event, data)

# Middleware-ni ro'yxatdan o'tkazamiz
dp.message.middleware(SubscriptionMiddleware())

# --- QOLGAN LOGIKA ---
MODES = {
    "friendly": "Sen foydalanuvchining do'stisan. Samimiy va hazilkash bo'l.",
    "romantic": "Sen juda muloyim va romantik suhbatdoshsan.",
    "coding": "Sen professional dasturchisan. Faqat kod va texnik yordam ber.",
    "tutor": "Sen ingliz tili o'qituvchisisan. Xatolarni to'g'irla va o'rgat.",
    "default": "Sen aqlli yordamchisan."
}

mode_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Do'stona 😊"), KeyboardButton(text="Sevgi ❤️")],
        [KeyboardButton(text="Dasturlash 💻"), KeyboardButton(text="Ingliz tili 🇬🇧")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Rejimni tanlang va suhbatni boshlaymiz:", reply_markup=mode_kb)

@dp.message()
async def main_chat_handler(message: types.Message):
    from .models import UserProfile, ChatHistory
    
    user_id = message.from_user.id
    text = message.text

    mode_map = {
        "Do'stona 😊": "friendly",
        "Sevgi ❤️": "romantic",
        "Dasturlash 💻": "coding",
        "Ingliz tili 🇬🇧": "tutor"
    }

    if text in mode_map:
        mode = mode_map[text]
        user_profile, _ = await UserProfile.objects.aget_or_create(user_id=user_id)
        user_profile.current_mode = mode
        await user_profile.asave()
        await ChatHistory.objects.filter(user_id=user_id).adelete()
        await message.answer(f"Rejim o'zgardi: {text} ✨")
        return

    # Gemini qismi
    user_profile, _ = await UserProfile.objects.aget_or_create(user_id=user_id)
    system_instruction = MODES.get(user_profile.current_mode, MODES["default"])

    history_records = ChatHistory.objects.filter(user_id=user_id).order_by('created_at')[:15]
    formatted_history = []
    async for record in history_records:
        formatted_history.append({"role": record.role, "parts": [record.text]})

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_instruction
    )
    
    try:
        chat = model.start_chat(history=formatted_history)
        response = await asyncio.to_thread(chat.send_message, text)
        ai_response = response.text

        await ChatHistory.objects.acreate(user=user_profile, role="user", text=text)
        await ChatHistory.objects.acreate(user=user_profile, role="model", text=ai_response)

        await message.answer(ai_response, parse_mode="Markdown")
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        await message.answer("Xatolik yuz berdi, iltimos qaytadan urinib ko'ring.")

def start_bot():
    print("Bot ishga tushdi...")
    asyncio.run(dp.start_polling(bot))
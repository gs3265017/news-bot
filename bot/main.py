"""version 0.1"""

import os
import asyncio
from pathlib import Path  
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputFile, CallbackQuery

from dotenv import load_dotenv
from crypto import Crypto
from database import AsyncDatabase
from keyboards import get_editor_keyboard, get_review_keyboard

load_dotenv()

class ArticleStates(StatesGroup):
    draft = State()
    review = State()
    approved = State()
    rejected = State()

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = AsyncDatabase()
crypto = Crypto(os.getenv("ENCRYPTION_KEY"))

# Создаем папки при запуске
VAULT_PATH = Path(os.getenv("VAULT_PATH"))
VAULT_PATH.mkdir(parents=True, exist_ok=True)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("📝 Отправьте текст для создания статьи")

@dp.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    draft_path = VAULT_PATH / f"draft_{user_id}_{message.message_id}.md"
    
    with open(draft_path, 'w') as f:
        f.write(message.text)
    
    encrypted_path = VAULT_PATH / f"{draft_path.name}.enc"
    with open(encrypted_path, 'wb') as f:
        f.write(crypto.encrypt_file(draft_path))
    
    article_id = await db.add_article(user_id, str(encrypted_path))
    await state.set_state(ArticleStates.draft)
    await state.update_data(article_id=article_id)
    await message.answer("✅ Черновик сохранен", reply_markup=get_editor_keyboard(article_id))

@dp.callback_query(F.data.startswith("edit_"))
async def edit_article(callback: CallbackQuery, state: FSMContext):
    article_id = int(callback.data.split("_")[1])
    article = await db.get_article(article_id)
    
    with open(article.file_path, 'rb') as f:
        decrypted = crypto.decrypt_file(f.read())
    
    temp_path = Path("/tmp") / f"{article_id}.md"
    with open(temp_path, 'w') as f:
        f.write(decrypted)
    
    os.system(f"open -a Obsidian {temp_path}")
    await callback.answer("Файл открыт в Obsidian")

@dp.callback_query(F.data.startswith("review_"))
async def send_to_review(callback: CallbackQuery, state: FSMContext):
    article_id = int(callback.data.split("_")[1])
    await db.update_status(article_id, "review")
    
    article = await db.get_article(article_id)
    await bot.send_document(
        chat_id=os.getenv("REVIEWER_CHAT_ID"),
        document=InputFile(article.file_path),
        caption=f"📄 Статья #{article_id} на ревью",
        reply_markup=get_review_keyboard(article_id)
    )
    await callback.answer("Отправлено на ревью!")
    await state.set_state(ArticleStates.review)

@dp.callback_query(F.data.startswith("approve_"))
async def approve_article(callback: CallbackQuery, state: FSMContext):
    article_id = int(callback.data.split("_")[1])
    await db.update_status(article_id, "approved")
    await callback.message.edit_text(f"✅ Статья #{article_id} одобрена!")
    await state.set_state(ArticleStates.approved)

@dp.callback_query(F.data.startswith("reject_"))
async def reject_article(callback: CallbackQuery, state: FSMContext):
    article_id = int(callback.data.split("_")[1])
    await db.update_status(article_id, "rejected")
    await callback.message.edit_text(f"❌ Статья #{article_id} отклонена")
    await state.set_state(ArticleStates.rejected)

async def main():
    await db.connect()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

"""news_bot v0.1"""
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
from keyboards import (
    get_editor_keyboard,
    get_review_keyboard,
    get_approve_keyboard
)

load_dotenv()

class ArticleStates(StatesGroup):
    DRAFT = State()
    REVIEW = State()
    APPROVED = State()
    REJECTED = State()
    REQUEST_CHANGES = State()
    

class NewsBot:
    def __init__(self):
        self.bot = Bot(token=os.getenv("BOT_TOKEN"))
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.db = AsyncDatabase()
        self.crypto = Crypto(os.getenv("ENCRYPTION_KEY"))
        self.vault_path = Path(os.getenv("VAULT_PATH"))
        
        self._register_handlers()

    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        self.dp.message.register(self._start_handler, Command("start"))
        self.dp.message.register(self._text_handler, F.text)
        self.dp.callback_query.register(self._edit_handler, F.data.startswith("edit_"))
        self.dp.callback_query.register(self._review_handler, F.data.startswith("review_"))
        self.dp.callback_query.register(self._approve_handler, F.data.startswith("approve_"))
        self.dp.callback_query.register(self._reject_handler, F.data.startswith("reject_"))
        self.dp.callback_query.register(self._delete_handler, F.data.startswith("delete_"))
        self.dp.callback_query.register(self._request_changes_handler, F.data.startswith("request_changes_"))

    async def _start_handler(self, message: Message):
        """Обработка команды /start"""
        await message.answer("📝 Отправьте текст для создания статьи")

    async def _text_handler(self, message: Message, state: FSMContext):
        """Обработка текстовых сообщений"""
        try:
            user_id = message.from_user.id
            draft_path = self.vault_path / f"draft_{user_id}_{message.message_id}.md"
            
            draft_path.write_text(message.text, encoding='utf-8')
            encrypted_path = self.vault_path / f"{draft_path.name}.enc"
            encrypted_path.write_bytes(self.crypto.encrypt_file(draft_path))
            
            article_id = await self.db.add_article(user_id, str(encrypted_path))
            
            await state.set_state(ArticleStates.DRAFT)
            await state.update_data(article_id=article_id)
            await message.answer(
                "✅ Черновик сохранен",
                reply_markup=get_editor_keyboard(article_id)
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

    async def _edit_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка кнопки редактирования"""
        try:
            article_id = int(callback.data.split("_")[1])
            article = await self.db.get_article(article_id)
            
            if not article:
                await callback.answer("Статья не найдена!")
                return
            
            decrypted = self.crypto.decrypt_file(Path(article.file_path).read_bytes())
            temp_path = Path("/tmp") / f"{article_id}.md"
            temp_path.write_text(decrypted, encoding='utf-8')
            
            os.system(f"open -a Obsidian {temp_path}")
            await callback.answer("Файл открыт в Obsidian")
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def _review_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка отправки на ревью"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "review")
            
            article = await self.db.get_article(article_id)
            if not article:
                await callback.answer("Статья не найдена!")
                return
            
            await self.bot.send_document(
                chat_id=os.getenv("REVIEWER_CHAT_ID"),
                document=InputFile(article.file_path),
                caption=f"📄 Статья #{article_id} на ревью",
                reply_markup=get_review_keyboard(article_id)
            )
            await callback.answer("Отправлено на ревью!")
            await state.set_state(ArticleStates.REVIEW)
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def _approve_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка одобрения статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "approved")
            
            await callback.message.edit_text(
                text=f"✅ Статья #{article_id} одобрена. Выберите действие:",
                reply_markup=get_approve_keyboard(article_id)
            )
            await state.set_state(ArticleStates.APPROVED)
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def _reject_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка отклонения статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "rejected")
            await callback.message.edit_text(f"❌ Статья #{article_id} отклонена")
            await state.set_state(ArticleStates.REJECTED)
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def _delete_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка удаления статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.delete_article(article_id)
            await callback.message.edit_text("🗑 Статья удалена")
            await state.clear()
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def _request_changes_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка запроса правок"""
        try:
            article_id = int(callback.data.split("_")[1])
            await callback.message.edit_text(
                text=f"✏️ Введите комментарий с правками для статьи #{article_id}:"
            )
            await state.set_state(ArticleStates.REQUEST_CHANGES)
            await state.update_data(article_id=article_id)
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}")

    async def run(self):
        """Запуск бота"""
        await self.db.connect()
        self.vault_path.mkdir(parents=True, exist_ok=True)
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    bot = NewsBot()
    asyncio.run(bot.run())

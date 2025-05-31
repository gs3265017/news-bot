"""news_bot v0.1"""
import os
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputFile, CallbackQuery
from dotenv import load_dotenv

from crypto import Crypto
from database import AsyncDatabase
from keyboards import Keyboards

ADMINS = list(map(int, os.getenv("ADMIN_IDS").split(',')))

def admin_required(func):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMINS:
            await message.answer("⛔ Доступ запрещен")
            return
        return await func(message, *args, **kwargs)
    return wrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
load_dotenv()

class ArticleStates(StatesGroup):
    DRAFT = State()
    REVIEW = State()
    APPROVED = State()
    REJECTED = State()
    REQUEST_CHANGES = State()
    SCHEDULED = State()

class NewsBot:
    def __init__(self):
        self._check_env_vars()
        self.bot = Bot(token=os.getenv("BOT_TOKEN"))
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.db = AsyncDatabase()
        self.crypto = Crypto(os.getenv("ENCRYPTION_KEY"))
        self.vault_path = Path(os.getenv("VAULT_PATH"))
        self.keyboards = Keyboards()
        
        self._register_handlers()

    def _check_env_vars(self):
        """Проверка обязательных переменных окружения"""
        required_vars = [
            'BOT_TOKEN', 
            'ENCRYPTION_KEY', 
            'VAULT_PATH', 
            'REVIEWER_CHAT_ID'
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing)}")

    async def _get_channel_id_handler(self, message: Message):
        """
        Обработчик команды для получения ID канала
        """
        if not message.forward_from_chat:
            return await message.answer("ℹ️ Пожалуйста, перешлите сообщение из канала")
        
        chat = message.forward_from_chat
        await message.answer(
            f"🔍 Данные канала:\n"
            f"Название: {chat.title}\n"
            f"Username: @{chat.username}\n"
            f"ID: `{chat.id}`\n\n"
            f"Добавьте это в .env файл:\n"
            f"CHANNEL_ID={chat.id}",
            parse_mode="Markdown"
        )

    async def _start_handler(self, message: Message):
        """Обработка команды /start"""
        await message.answer(
            "📝 Бот для управления публикациями\n\n"
            "Отправьте текст для создания новой статьи",
            reply_markup=self.keyboards.main_menu()
        )

    async def _text_handler(self, message: Message, state: FSMContext):
        """Обработка текстовых сообщений"""
        try:
            if await state.get_state() != ArticleStates.DRAFT:
                return

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
                reply_markup=self.keyboards.editor_keyboard(article_id)
            )
            
        except Exception as e:
            logger.error(f"Error in _text_handler: {e}")
            await message.answer("❌ Произошла ошибка при сохранении черновика")

    async def _edit_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка кнопки редактирования"""
        try:
            article_id = int(callback.data.split("_")[1])
            article = await self.db.get_article(article_id)
            
            if not article or not Path(article.file_path).exists():
                await callback.answer("Файл статьи не найден!")
                return
            
            decrypted = self.crypto.decrypt_file(Path(article.file_path).read_bytes())
            temp_path = Path("/tmp") / f"{article_id}.md"
            temp_path.write_text(decrypted, encoding='utf-8')
            
            os.system(f"open -a Obsidian {temp_path}")
            await callback.answer("Файл открыт в Obsidian")
            
        except Exception as e:
            logger.error(f"Error in _edit_handler: {e}")
            await callback.answer("❌ Ошибка при открытии файла")

    async def _review_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка отправки на ревью"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "review")
            
            article = await self.db.get_article(article_id)
            if not article or not Path(article.file_path).exists():
                await callback.answer("Статья не найдена!")
                return
            
            await self.bot.send_document(
                chat_id=os.getenv("REVIEWER_CHAT_ID"),
                document=InputFile(article.file_path),
                caption=f"📄 Статья #{article_id} на ревью",
                reply_markup=self.keyboards.reviewer_keyboard(article_id)
            )
            await callback.answer("Отправлено на ревью!")
            await state.set_state(ArticleStates.REVIEW)
            
        except Exception as e:
            logger.error(f"Error in _review_handler: {e}")
            await callback.answer("❌ Ошибка при отправке на ревью")

    async def _approve_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка одобрения статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "approved")
            
            await callback.message.edit_text(
                text=f"✅ Статья #{article_id} одобрена. Выберите действие:",
                reply_markup=self.keyboards.publish_keyboard(article_id)
            )
            await state.set_state(ArticleStates.APPROVED)
            
        except Exception as e:
            logger.error(f"Error in _approve_handler: {e}")
            await callback.answer("❌ Ошибка при одобрении статьи")

    async def _reject_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка отклонения статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.update_status(article_id, "rejected")
            
            await callback.message.edit_text(
                text=f"❌ Статья #{article_id} отклонена",
                reply_markup=self.keyboards.back_keyboard()
            )
            await state.set_state(ArticleStates.REJECTED)
            
        except Exception as e:
            logger.error(f"Error in _reject_handler: {e}")
            await callback.answer("❌ Ошибка при отклонении статьи")

    async def _delete_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка удаления статьи"""
        try:
            article_id = int(callback.data.split("_")[1])
            await self.db.delete_article(article_id)
            
            await callback.message.edit_text("🗑 Статья удалена")
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in _delete_handler: {e}")
            await callback.answer("❌ Ошибка при удалении статьи")

    async def _request_changes_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка запроса правок"""
        try:
            article_id = int(callback.data.split("_")[1])
            
            await callback.message.edit_text(
                text=f"✏️ Введите комментарий с правками для статьи #{article_id}:",
                reply_markup=self.keyboards.back_keyboard()
            )
            await state.set_state(ArticleStates.REQUEST_CHANGES)
            await state.update_data(article_id=article_id)
            
        except Exception as e:
            logger.error(f"Error in _request_changes_handler: {e}")
            await callback.answer("❌ Ошибка при запросе правок")

    async def _changes_comment_handler(self, message: Message, state: FSMContext):
        """Обработка комментария с правками"""
        try:
            data = await state.get_data()
            await self.db.log_review(data['article_id'], message.text)
            
            await message.answer(
                "📝 Комментарий по правкам сохранён",
                reply_markup=self.keyboards.editor_keyboard(data['article_id'])
            )
            await state.set_state(ArticleStates.DRAFT)
            
        except Exception as e:
            logger.error(f"Error in _changes_comment_handler: {e}")
            await message.answer("❌ Ошибка при сохранении комментария")

    async def _back_handler(self, callback: CallbackQuery, state: FSMContext):
        """Обработка кнопки 'Назад'"""
        try:
            data = await state.get_data()
            await callback.message.edit_text(
                text="Возврат к редактированию статьи",
                reply_markup=self.keyboards.editor_keyboard(data['article_id'])
            )
            await state.set_state(ArticleStates.DRAFT)
            
        except Exception as e:
            logger.error(f"Error in _back_handler: {e}")
            await callback.answer("❌ Ошибка при возврате")

    async def _publish_to_channel(self, article_id: int):
        """Публикация статьи в DigitalCriticism"""
        try:
            article = await self.db.get_article(article_id)
            if not article:
                raise ValueError("Статья не найдена")
            
            decrypted = self.crypto.decrypt_file(Path(article.file_path).read_bytes())
            
            await self.bot.send_message(
                chat_id=os.getenv("CHANNEL_ID"),  
                text=decrypted,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка публикации: {e}")
            return False

    async def _get_channel_info(self, message: Message):
        """Обработчик команды получения информации о канале"""
        try:
            chat = await self.bot.get_chat("@digitalcriticism")
            
            admins = await self.bot.get_chat_administrators(chat.id)
            bot_is_admin = any([admin.user.id == self.bot.id for admin in admins])
            
            await message.answer(
                f"📊 Информация о канале:\n"
                f"Название: {chat.title}\n"
                f"ID: <code>{chat.id}</code>\n"
                f"Тип: {chat.type}\n"
                f"Бот является администратором: {'✅' if bot_is_admin else '❌'}\n\n"
                f"Добавьте в .env:\n"
                f"CHANNEL_ID={chat.id}",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
            logger.error(f"Ошибка в _get_channel_info_handler: {e}")

    async def _test_channel(self, message: Message):
        """Тестовая публикация"""
        test_msg = await self.bot.send_message(
            chat_id=os.getenv("CHANNEL_ID"),
            text="🔧 Тестовое сообщение от бота"
        )
        await message.answer(f"✅ Тест успешен. Сообщение ID: {test_msg.message_id}")

    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        handlers = [
            (self._start_handler, Command("start")),
            (self._get_channel_info, Command("get_channel_info")),
            (self._text_handler, F.text),
            (self._edit_handler, F.data.startswith("edit_")),
            (self._review_handler, F.data.startswith("review_")),
            (self._approve_handler, F.data.startswith("approve_")),
            (self._reject_handler, F.data.startswith("reject_")),
            (self._delete_handler, F.data.startswith("delete_")),
            (self._request_changes_handler, F.data.startswith("request_changes_")),
            (self._back_handler, F.data == "back"),
            (self._changes_comment_handler, ArticleStates.REQUEST_CHANGES)
        ]
        
        for handler, *filters in handlers:
            if filters:
                if handler.__name__.startswith('_'):
                    self.dp.message.register(handler, *filters)
                else:
                    self.dp.callback_query.register(handler, *filters)

    async def run(self):
        """Запуск бота"""
        try:
            await self.db.connect()
            self.vault_path.mkdir(parents=True, exist_ok=True)
            logger.info("Бот запущен")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.critical(f"Ошибка при запуске бота: {e}")
            
        finally:
            await self.db.close()
            await self.bot.session.close()
            logger.info("Бот остановлен")

async def main():
    bot = NewsBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())

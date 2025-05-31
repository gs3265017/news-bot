from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class Keyboards:
    """Класс для генерации всех клавиатур бота"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardBuilder:
        """Главное меню (Reply клавиатура)"""
        builder = ReplyKeyboardBuilder()
        builder.button(text="📝 Создать статью")
        builder.button(text="📚 Мои черновики")
        builder.button(text="📊 Статистика")
        builder.button(text="⚙️ Настройки")
        builder.adjust(2, 2)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

    @staticmethod
    def editor_keyboard(article_id: int) -> InlineKeyboardMarkup:
        """Клавиатура автора статьи"""
        builder = InlineKeyboardBuilder()
        builder.button(text="✏️ Редактировать", callback_data=f"edit_{article_id}")
        builder.button(text="📤 На ревью", callback_data=f"review_{article_id}")
        builder.button(text="🗑 Удалить", callback_data=f"delete_{article_id}")
        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def reviewer_keyboard(article_id: int) -> InlineKeyboardMarkup:
        """Клавиатура ревьюера"""
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Одобрить", callback_data=f"approve_{article_id}")
        builder.button(text="❌ Отклонить", callback_data=f"reject_{article_id}")
        builder.button(text="✏️ Правки", callback_data=f"request_changes_{article_id}")
        builder.button(text="💬 Комментарий", callback_data=f"comment_{article_id}")
        builder.adjust(2, 2)
        return builder.as_markup()

    @staticmethod
    def publish_keyboard(article_id: int) -> InlineKeyboardMarkup:
        """Клавиатура публикации"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Опубликовать", callback_data=f"publish_{article_id}")
        builder.button(text="⏰ Запланировать", callback_data=f"schedule_{article_id}")
        builder.button(text="🔙 Назад", callback_data="back_to_review")
        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def back_keyboard() -> InlineKeyboardMarkup:
        """Универсальная кнопка Назад"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back")
        return builder.as_markup()

    @staticmethod
    def confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действий"""
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data=f"confirm_{action}_{item_id}")
        builder.button(text="❌ Отменить", callback_data="cancel_action")
        return builder.as_markup()

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Меню настроек"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔔 Уведомления", callback_data="settings_notifications")
        builder.button(text="👥 Доступ", callback_data="settings_access")
        builder.button(text="📅 Расписание", callback_data="settings_schedule")
        builder.button(text="🔙 Главное меню", callback_data="main_menu")
        builder.adjust(1, 1, 2)
        return builder.as_markup()

    @staticmethod
    def pagination(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """Клавиатура пагинации"""
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️", callback_data=f"{prefix}_prev_{page}")
        builder.button(text=f"{page}/{total_pages}", callback_data="current_page")
        builder.button(text="➡️", callback_data=f"{prefix}_next_{page}")
        return builder.as_markup()
    
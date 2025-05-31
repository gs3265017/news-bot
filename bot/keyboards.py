from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_editor_keyboard(article_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для автора статьи"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Редактировать", 
                callback_data=f"edit_{article_id}"
            ),
            InlineKeyboardButton(
                text="📤 На ревью", 
                callback_data=f"review_{article_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить", 
                callback_data=f"delete_{article_id}"
            )
        ]
    ])

def get_review_keyboard(article_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ревьюера"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить", 
                callback_data=f"approve_{article_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить", 
                callback_data=f"reject_{article_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Запросить правки", 
                callback_data=f"request_changes_{article_id}"
            )
        ]
    ])

def get_approve_keyboard(article_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после одобрения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏰ Запланировать публикацию", 
                callback_data=f"schedule_{article_id}"
            ),
            InlineKeyboardButton(
                text="🚀 Опубликовать сейчас", 
                callback_data=f"publish_{article_id}"
            )
        ]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])


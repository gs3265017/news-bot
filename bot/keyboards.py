from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_review_keyboard(article_id: int):
    return InlineKeyboardMarkup().row(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{article_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{article_id}")
    )

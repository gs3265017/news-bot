import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def log_review(self, article_id: int, comment: str):
    """Логирование комментариев ревьюера"""
    async with self.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO review_comments (article_id, comment) VALUES ($1, $2)",
            article_id, comment
        )

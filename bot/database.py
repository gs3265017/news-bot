import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()


class AsyncDatabase:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )

    async def add_article(self, user_id: int, file_path: str) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "INSERT INTO articles (user_id, file_path, status) VALUES ($1, $2, 'draft') RETURNING id",
                user_id, file_path
            )

    async def get_article(self, article_id: int) -> dict:
        async with self.pool.acquire() as conn:
            article = await conn.fetchrow("SELECT * FROM articles WHERE id = $1", article_id)
            return dict(article) if article else None
        
    async def update_status(self, article_id: int, status: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE articles SET status = $1 WHERE id = $2",
                status, article_id
            )
        
    async def delete_article(self, article_id: int):
        """Удаление статьи из БД"""
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM articles WHERE id = $1", article_id)

    async def log_review(self, article_id: int, comment: str):
        """Логирование комментариев ревьюера"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO review_comments (article_id, comment) VALUES ($1, $2)",
                article_id, comment
        )
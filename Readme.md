# News Bot (v0.1)

Telegram-бот для редакторской работы с публикациями в Obsidian с системой ревью и шифрованием.

## 📌 Возможности

- Прием текста от пользователей
- Автоматическое сохранение в Obsidian Vault
- Шифрование файлов (AES-256)
- Система ревью с кнопками одобрения/отклонения
- Интеграция с PostgreSQL
- FSM для управления workflow

## ⚙️ Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-репозиторий/news-bot.git
cd news-bot
```
## Создайте и активируйте виртуальное окружение:
```bash 
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```
## Установка зависимостей
```bash
pip install -r requirements.txt
```
## Настройкка окружения
- Создайте файл .env на основе .env.example
- Укажите свои настройки в .env

### Конфигурация
Файл .env должен содержать:
```
BOT_TOKEN=ваш_токен_бота
REVIEWER_CHAT_ID=ваш_chat_id
VAULT_PATH=./vault/drafts
ENCRYPTION_KEY=ваш_32_символьный_ключ

# PostgreSQL
DB_NAME=telegram_bot
DB_USER=bot_user
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

## Структура проекта

```
news-bot/
├── bot/
│   ├── main.py          # Основной код бота
│   ├── crypto.py        # Шифрование/дешифрование
│   ├── database.py      # Работа с PostgreSQL
│   ├── keyboards.py     # Клавиатуры
│   └── states.py        # Состояния FSM
├── vault/               # Папка Obsidian
│   ├── drafts/          # Черновики
│   └── published/       # Опубликованные
├── .env                 # Настройки
├── requirements.txt     # Зависимости
└── README.md            # Этот файл
```
## Запуск
```bash
python bot/main.py
```

## Workflow
- Пользователь отправляет текст боту
- Бот сохраняет в Obsidian Vault (зашифровано)
- Автор отправляет на ревью
- Редактор проверяет и одобряет/отклоняет
- После одобрения - публикация


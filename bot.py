import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

GENRES = {
    28: "Бойовик", 12: "Пригоди", 16: "Анімація", 35: "Комедія",
    80: "Кримінал", 99: "Документальний", 18: "Драма", 10751: "Сімейний",
    14: "Фентезі", 36: "Історичний", 27: "Жахи", 10402: "Музика",
    9648: "Детектив", 10749: "Романтика", 878: "Фантастика",
    10770: "ТБ фільм", 53: "Трилер", 10752: "Воєнний", 37: "Вестерн"
}


def tmdb_get(endpoint, params=None):
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    params["language"] = "uk-UA"
    try:
        r = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"TMDB error: {e}")
        return None


def format_movie(movie, index=None):
    title = movie.get("title", "Без назви")
    year = movie.get("release_date", "")[:4] or "—"
    rating = movie.get("vote_average", 0)
    overview = movie.get("overview", "Опис відсутній.")
    genre_ids = movie.get("genre_ids", [])
    genres = ", ".join(GENRES.get(g, "") for g in genre_ids if g in GENRES) or "—"
    stars = "⭐" * round(rating / 2) if rating else ""
    prefix = f"{index}. " if index else ""
    overview_short = overview[:200] + "..." if len(overview) > 200 else overview
    return (
        f"{prefix}🎬 *{title}* ({year})\n"
        f"🎭 {genres}\n"
        f"⭐ {rating:.1f}/10 {stars}\n"
        f"📖 {overview_short}"
    )


def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔥 Зараз популярне", callback_data="popular"),
            InlineKeyboardButton("🎬 У прокаті", callback_data="now_playing"),
        ],
        [
            InlineKeyboardButton("🏆 Найвища оцінка", callback_data="top_rated"),
            InlineKeyboardButton("🔜 Незабаром", callback_data="upcoming"),
        ],
        [
            InlineKeyboardButton("🎲 Випадковий фільм", callback_data="random"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎥 *Привіт! Я — КіноБот* 🎥\n\n"
        "Я допоможу тобі знайти що подивитися:\n"
        "• Покажу що зараз популярне\n"
        "• Розповім що йде в кінотеатрах\n"
        "• Порекомендую найкращі фільми\n"
        "• Знайду фільми за назвою\n\n"
        "📩 Просто напиши назву фільму або обери категорію:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Як користуватися ботом:*\n\n"
        "• Натисни кнопку для перегляду категорії\n"
        "• Або просто напиши назву фільму для пошуку\n\n"
        "*Команди:*\n"
        "/start — головне меню\n"
        "/help — ця довідка\n"
        "/popular — популярні фільми\n"
        "/nowplaying — зараз у кіно\n"
        "/toprated — найкраще кіно всіх часів"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def show_popular(update, context, query=None):
    data = tmdb_get("/movie/popular", {"page": 1})
    if not data:
        msg = "😕 Не вдалося отримати дані. Спробуй пізніше."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    movies = data["results"][:5]
    text = "🔥 *Зараз популярне:*\n\n"
    text += "\n\n".join(format_movie(m, i + 1) for i, m in enumerate(movies))

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def show_now_playing(update, context, query=None):
    data = tmdb_get("/movie/now_playing", {"page": 1})
    if not data:
        msg = "😕 Не вдалося отримати дані. Спробуй пізніше."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    movies = data["results"][:5]
    text = "🎬 *Зараз у прокаті:*\n\n"
    text += "\n\n".join(format_movie(m, i + 1) for i, m in enumerate(movies))

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def show_top_rated(update, context, query=None):
    data = tmdb_get("/movie/top_rated", {"page": 1})
    if not data:
        msg = "😕 Не вдалося отримати дані. Спробуй пізніше."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    movies = data["results"][:5]
    text = "🏆 *Найвища оцінка всіх часів:*\n\n"
    text += "\n\n".join(format_movie(m, i + 1) for i, m in enumerate(movies))

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def show_upcoming(update, context, query=None):
    data = tmdb_get("/movie/upcoming", {"page": 1})
    if not data:
        msg = "😕 Не вдалося отримати дані. Спробуй пізніше."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    movies = data["results"][:5]
    text = "🔜 *Незабаром у кіно:*\n\n"
    text += "\n\n".join(format_movie(m, i + 1) for i, m in enumerate(movies))

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def show_random(update, context, query=None):
    import random
    page = random.randint(1, 10)
    data = tmdb_get("/movie/popular", {"page": page})
    if not data or not data.get("results"):
        msg = "😕 Не вдалося отримати дані. Спробуй пізніше."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    movie = random.choice(data["results"])
    text = "🎲 *Випадковий фільм для тебе:*\n\n" + format_movie(movie)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Ще один!", callback_data="random")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
    ])

    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    if not query_text:
        return

    data = tmdb_get("/search/movie", {"query": query_text, "page": 1})
    if not data or not data.get("results"):
        await update.message.reply_text(
            f"🔍 За запитом *{query_text}* нічого не знайдено.\n\nСпробуй іншу назву.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    movies = data["results"][:3]
    text = f"🔍 *Результати пошуку: «{query_text}»*\n\n"
    text += "\n\n".join(format_movie(m, i + 1) for i, m in enumerate(movies))

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "popular":
        await show_popular(update, context, query)
    elif query.data == "now_playing":
        await show_now_playing(update, context, query)
    elif query.data == "top_rated":
        await show_top_rated(update, context, query)
    elif query.data == "upcoming":
        await show_upcoming(update, context, query)
    elif query.data == "random":
        await show_random(update, context, query)
    elif query.data == "back":
        text = (
            "🎥 *Головне меню*\n\n"
            "Обери категорію або напиши назву фільму для пошуку:"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def popular_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_popular(update, context)


async def nowplaying_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_now_playing(update, context)


async def toprated_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_top_rated(update, context)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("popular", popular_command))
    app.add_handler(CommandHandler("nowplaying", nowplaying_command))
    app.add_handler(CommandHandler("toprated", toprated_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie))

    logger.info("Бот запущено!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

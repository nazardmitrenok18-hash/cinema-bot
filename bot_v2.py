import os
import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE = "https://api.themoviedb.org/3"

GENRES = {
    28: "Бойовик", 12: "Пригоди", 16: "Анімація", 35: "Комедія",
    80: "Кримінал", 18: "Драма", 14: "Фентезі", 27: "Жахи",
    10749: "Романтика", 878: "Фантастика", 53: "Трилер", 10752: "Воєнний"
}


def tmdb(endpoint, params=None):
    p = {"api_key": TMDB_API_KEY, "language": "uk-UA"}
    if params:
        p.update(params)
    try:
        r = requests.get(f"{TMDB_BASE}{endpoint}", params=p, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(e)
        return None


def fmt(movie, i=None):
    title = movie.get("title", "Без назви")
    year = movie.get("release_date", "")[:4] or "—"
    rating = movie.get("vote_average", 0)
    overview = movie.get("overview", "Опис відсутній.")[:200]
    genres = ", ".join(GENRES.get(g, "") for g in movie.get("genre_ids", []) if g in GENRES) or "—"
    prefix = f"{i}. " if i else ""
    return f"{prefix}🎬 *{title}* ({year})\n🎭 {genres}\n⭐ {rating:.1f}/10\n📖 {overview}..."


def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Популярне", callback_data="popular"),
         InlineKeyboardButton("🎬 У прокаті", callback_data="now_playing")],
        [InlineKeyboardButton("🏆 Топ рейтинг", callback_data="top_rated"),
         InlineKeyboardButton("🔜 Незабаром", callback_data="upcoming")],
        [InlineKeyboardButton("🎲 Випадковий фільм", callback_data="random")],
    ])


def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 *КіноБот* — твій провідник у світі кіно!\n\nОбери категорію або напиши назву фільму:",
        parse_mode="Markdown", reply_markup=main_kb()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    endpoints = {
        "popular": ("/movie/popular", "🔥 *Зараз популярне:*"),
        "now_playing": ("/movie/now_playing", "🎬 *Зараз у прокаті:*"),
        "top_rated": ("/movie/top_rated", "🏆 *Найвища оцінка:*"),
        "upcoming": ("/movie/upcoming", "🔜 *Незабаром у кіно:*"),
    }

    if q.data == "back":
        await q.edit_message_text("🎥 Головне меню:\n\nОбери категорію або напиши назву фільму:",
                                   parse_mode="Markdown", reply_markup=main_kb())
        return

    if q.data == "random":
        import random
        data = tmdb("/movie/popular", {"page": random.randint(1, 5)})
        if data and data.get("results"):
            movie = random.choice(data["results"])
            text = "🎲 *Випадковий фільм:*\n\n" + fmt(movie)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Ще один!", callback_data="random")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")],
            ])
            await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    if q.data in endpoints:
        endpoint, title = endpoints[q.data]
        data = tmdb(endpoint, {"page": 1})
        if not data:
            await q.edit_message_text("😕 Помилка. Спробуй пізніше.", reply_markup=back_kb())
            return
        movies = data.get("results", [])[:5]
        text = title + "\n\n" + "\n\n".join(fmt(m, i + 1) for i, m in enumerate(movies))
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=back_kb())


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    data = tmdb("/search/movie", {"query": query})
    if not data or not data.get("results"):
        await update.message.reply_text(f"🔍 За запитом *{query}* нічого не знайдено.",
                                         parse_mode="Markdown", reply_markup=main_kb())
        return
    movies = data["results"][:3]
    text = f"🔍 *Результати: «{query}»*\n\n" + "\n\n".join(fmt(m, i + 1) for i, m in enumerate(movies))
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=back_kb())


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    logger.info("Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()

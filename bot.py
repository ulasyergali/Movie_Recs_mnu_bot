from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import json
import random
from movies import movies

# ---------------- JSON storage -----------------
def load_favorites():
    try:
        with open("favorites.json", "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_favorites(favorites):
    with open("favorites.json", "w") as f:
        json.dump(favorites, f)

def load_watched():
    try:
        with open("watched.json", "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_watched(watched):
    with open("watched.json", "w") as f:
        json.dump(watched, f)

# ---------------- /start & Main Menu -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Hi! I am your AI Movie Recommendation Bot!\n"
        "Please choose a genre to get recommendations."
    )
    await show_main_menu(update)

async def show_main_menu(update_or_query):
    genres = list(movies.keys())
    buttons = [InlineKeyboardButton(f"{g}", callback_data=f"genre:{g}") for g in genres]
    buttons.append(InlineKeyboardButton("💖 Favorites", callback_data="favorites_menu"))
    buttons.append(InlineKeyboardButton("📽️ Watched Movies", callback_data="watched_menu"))
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_query, "message"):
        await update_or_query.message.reply_text("📂 Main Menu:", reply_markup=reply_markup)
    else:
        await update_or_query.message.reply_text("📂 Main Menu:", reply_markup=reply_markup)

# ---------------- Button Handler -----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    # --- Genre selection ---
    if data.startswith("genre:"):
        genre = data.split(":")[1]
        selected_movies = random.sample(movies[genre], min(5, len(movies[genre])))
        buttons = [[InlineKeyboardButton(f"⭐ Add '{m}'", callback_data=f"fav:{m}")] for m in selected_movies]
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text(f"🎬 Here are some {genre} movies:", reply_markup=reply_markup)

    # --- Add to Favorites ---
    elif data.startswith("fav:"):
        movie_name = data.split(":")[1]
        favorites = load_favorites()
        if user_id not in favorites:
            favorites[user_id] = []
        if movie_name not in favorites[user_id]:
            favorites[user_id].append(movie_name)
            save_favorites(favorites)
            await query.message.reply_text(f"✅ '{movie_name}' added to your favorites!")
        else:
            await query.message.reply_text(f"⚠️ '{movie_name}' is already in your favorites!")

        buttons = [
            [InlineKeyboardButton("💖 Show Favorites", callback_data="favorites_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text("What do you want to do next?", reply_markup=reply_markup)

    # --- Favorites Menu ---
    elif data == "favorites_menu":
        favorites = load_favorites()
        user_favorites = favorites.get(user_id, [])
        if user_favorites:
            buttons = [[InlineKeyboardButton(f"{m}", callback_data=f"fav_choice:{m}")] for m in user_favorites]
        else:
            buttons = []
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text("💖 Your Favorites:", reply_markup=reply_markup)

    # --- Favorite choice ---
    elif data.startswith("fav_choice:"):
        movie_name = data.split(":")[1]
        buttons = [
            [InlineKeyboardButton("🗑️ Remove from Favorites", callback_data=f"remove:{movie_name}")],
            [InlineKeyboardButton("📽️ Add to Watched", callback_data=f"watched:{movie_name}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text(f"Selected: {movie_name}", reply_markup=reply_markup)

    # --- Remove from Favorites ---
    elif data.startswith("remove:"):
        movie_name = data.split(":")[1]
        favorites = load_favorites()
        if movie_name in favorites.get(user_id, []):
            favorites[user_id].remove(movie_name)
            save_favorites(favorites)
            await query.message.reply_text(f"🗑️ '{movie_name}' removed from favorites.")
        await button(update, context)  # Show updated favorites

    # --- Add to Watched ---
    elif data.startswith("watched:"):
        movie_name = data.split(":")[1]
        watched = load_watched()
        if user_id not in watched:
            watched[user_id] = {}
        if movie_name not in watched[user_id]:
            watched[user_id][movie_name] = "-"  # No rating yet
            save_watched(watched)
            await query.message.reply_text(f"📽️ '{movie_name}' added to Watched list.")
        await show_watched_menu(query)

    # --- Watched Menu ---
    elif data == "watched_menu":
        await show_watched_menu(query)

    # --- Watched movie choice for rating ---
    elif data.startswith("watched_choice:"):
        movie_name = data.split(":")[1]
        buttons = [[InlineKeyboardButton(f"{i}⭐", callback_data=f"rate:{movie_name}:{i}")] for i in range(1, 6)]
        buttons.append([InlineKeyboardButton("🏠 Back to Watched", callback_data="watched_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text(f"Rate '{movie_name}':", reply_markup=reply_markup)

    # --- Rate watched movie ---
    elif data.startswith("rate:"):
        parts = data.split(":")
        movie_name = parts[1]
        rating = parts[2]
        watched = load_watched()
        if user_id not in watched:
            watched[user_id] = {}
        watched[user_id][movie_name] = rating
        save_watched(watched)
        await query.message.reply_text(f"⭐ Rated '{movie_name}' as {rating}/5")
        await show_watched_menu(query)

    # --- Main Menu ---
    elif data == "main_menu":
        await show_main_menu(query)

# ---------------- Show Watched Menu -----------------
async def show_watched_menu(update_or_query):
    user_id = str(update_or_query.from_user.id)
    watched = load_watched()
    user_watched = watched.get(user_id, {})

    buttons = []
    for movie, rating in user_watched.items():
        display = f"{movie} ({rating})"
        buttons.append([InlineKeyboardButton(display, callback_data=f"watched_choice:{movie}")])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await update_or_query.message.reply_text("📽️ Watched Movies:", reply_markup=reply_markup)

# ---------------- MAIN BOT -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token("8688487846:AAHqspR2JDv1pQkTZ0sooGXHXCP4nYSpITI").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myfavorites", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()
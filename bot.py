import random
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Bot tokenin
TOKEN = '8121790668:AAGsCTKLkA3H7O78AWimvNhnIAE5Eoo92vY'

WORDS = ['alma', 'söhbət', 'banana', 'gülümsəyən üz', 'top', 'uçan quş', 'raket', 'kitab', 'pizza', 'göz', 'dəvə']

target_word = None
game_active = False
scores = {}

def start(update: Update, context: CallbackContext):
    global target_word, game_active
    if not game_active:
        target_word = random.choice(WORDS)
        game_active = True
        update.message.reply_text(f"Tez tap: '{target_word}' sözünü ən birinci yaz!")

        def timeout():
            global game_active
            if game_active:
                game_active = False
                update.message.reply_text("Vaxt bitdi! Heç kim doğru cavab vermədi.")

        timer = threading.Timer(10.0, timeout)
        timer.start()
    else:
        update.message.reply_text("Oyun artıq aktivdir! Əvvəlcə /stop yazıb dayandırın.")

def stop(update: Update, context: CallbackContext):
    global game_active
    if game_active:
        game_active = False
        update.message.reply_text("Oyun dayandırıldı.")
    else:
        update.message.reply_text("Hazırda aktiv oyun yoxdur.")

def status(update: Update, context: CallbackContext):
    if game_active:
        update.message.reply_text("Hazırda oyun AKTİVDİR!")
    else:
        update.message.reply_text("Hazırda oyun YOXDUR.")

def top(update: Update, context: CallbackContext):
    if not scores:
        update.message.reply_text("Hələ heç kim xal qazanmayıb.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = "Xal cədvəli:\n"
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        user = context.bot.get_chat_member(update.effective_chat.id, user_id).user
        leaderboard += f"{i}. {user.first_name} — {score} xal\n"

    update.message.reply_text(leaderboard)

def check_message(update: Update, context: CallbackContext):
    global target_word, game_active
    if game_active and update.message.text.lower() == target_word.lower():
        user = update.message.from_user
        name = user.first_name
        user_id = user.id
        scores[user_id] = scores.get(user_id, 0) + 1
        update.message.reply_text(f"Təbriklər, {name} qazandı!\nÜmumi xalların: {scores[user_id]}")
        game_active = False

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("basla", start))
    dp.add_handler(CommandHandler("saxla", stop))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

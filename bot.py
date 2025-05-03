import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Bot tokenin
TOKEN = '8121790668:AAGsCTKLkA3H7O78AWimvNhnIAE5Eoo92vY'

WORDS = ['alma', 'söhbət', 'banana', 'gülümsəyən üz', 'top', 'uçan quş', 'raket', 'kitab', 'pizza', 'göz', 'dəvə']

target_word = None
game_active = False
scores = {}
inactivity_timer = None  # 10 dəqiqəlik susqunluq taymeri

def start(update: Update, context: CallbackContext):
    global target_word, game_active
    if not game_active:
        game_active = True
        target_word = random.choice(WORDS)
        update.message.reply_text(f"Tez tap: '{target_word}' sözünü ən birinci yaz!")
        reset_inactivity_timer(update, context)
    else:
        update.message.reply_text("Oyun artıq aktivdir! Əvvəlcə /saxla yazıb dayandırın.")

def stop(update: Update, context: CallbackContext):
    global game_active, inactivity_timer
    if game_active:
        game_active = False
        if inactivity_timer:
            inactivity_timer.schedule_removal()
            inactivity_timer = None
        context.bot.send_message(chat_id=update.effective_chat.id, text="Oyun dayandırıldı.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hazırda aktiv oyun yoxdur.")

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
        target_word = random.choice(WORDS)
        update.message.reply_text(f"Növbəti söz: '{target_word}'")
    reset_inactivity_timer(update, context)

def stop_due_to_inactivity(context: CallbackContext):
    global game_active
    game_active = False
    context.bot.send_message(chat_id=context.job.context, text="10 dəqiqə heç kim yazmadı, oyun avtomatik dayandırıldı.")

def reset_inactivity_timer(update: Update, context: CallbackContext):
    global inactivity_timer
    if inactivity_timer:
        inactivity_timer.schedule_removal()
    inactivity_timer = context.job_queue.run_once(stop_due_to_inactivity, 600, context=update.effective_chat.id)

def main():
    updater = Updater(TOKEN, use_context=True)
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

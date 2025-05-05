import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = '8121790668:AAHzM2CqGr6DYfRbatjpFYVPEuUMgMFZO8g'

WORDS = ['alma', 'çətir', 'kompyuter', 'pəncərə', 'dəftər', 'açar', 'oyuncaq', 'elektrikləşdirilmişdərdənsinizmi',
         'qələm', 'divar', 'telefon', 'çay', 'ayna', 'kitabxana', 'dəli', 'kəpənək', 'sevgi', 'bulud', 'ulduz',
         'əjdaha', 'səssizlik', 'canavar', 'pozan', 'kalkulyator', 'aşçıabbasaşasmışasmışsadaazasmış', 'zəka',
         'təhlükə', 'kölgə', 'robot', 'baki', 'samirlə qurban', 'söhbət', 'dünya', 'duman', 'sari', 'hamster',
         'qurbaqa', 'saat', 'gülümsəyən üz', 'top', 'uçan quş', 'raket', 'kitab', 'pizza', 'göz', 'dəvə']

game_active = {}
target_words = {}
last_words = {}
scores = {}
inactivity_timers = {}

def get_new_word(chat_id):
    last_word = last_words.get(chat_id)
    new_word = random.choice(WORDS)
    while new_word == last_word:
        new_word = random.choice(WORDS)
    last_words[chat_id] = new_word
    return new_word

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text.lower()
    if any(bad in text for bad in ["vpn", "bit.ly", "t.me/vpn", "http", "https"]):
        return

    if not game_active.get(chat_id, False):
        game_active[chat_id] = True
        word = get_new_word(chat_id)
        target_words[chat_id] = word
        update.message.reply_text(f"Tez tap: '{word}' sözünü ən birinci yaz!")
        reset_inactivity_timer(update, context)
    else:
        update.message.reply_text("Oyun artıq aktivdir! Əvvəlcə /saxla yazıb dayandırın.")

def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if game_active.get(chat_id, False):
        game_active[chat_id] = False
        if inactivity_timers.get(chat_id):
            inactivity_timers[chat_id].schedule_removal()
            inactivity_timers[chat_id] = None
        context.bot.send_message(chat_id=chat_id, text="Bu söhbətdə oyun dayandırıldı.")
    else:
        context.bot.send_message(chat_id=chat_id, text="Bu söhbətdə aktiv oyun yoxdur.")

def status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("Hazırda oyun AKTİVDİR!" if game_active.get(chat_id, False) else "Hazırda oyun YOXDUR.")

def top(update: Update, context: CallbackContext):
    if not scores:
        update.message.reply_text("Hələ heç kim xal qazanmayıb.")
        return
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard = "Xal cədvəli:\n"
"
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        user = context.bot.get_chat_member(update.effective_chat.id, user_id).user
        leaderboard += f"{i}. {user.first_name} — {score} xal
"
    update.message.reply_text(leaderboard)

def check_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not game_active.get(chat_id, False):
        return

    user_text = update.message.text.strip().lower()
    if user_text == target_words.get(chat_id, "").lower():
        user = update.message.from_user
        scores[user.id] = scores.get(user.id, 0) + 1
        update.message.reply_text(f"Təbriklər, {user.first_name} qazandı!
Ümumi xalların: {scores[user.id]}")
        word = get_new_word(chat_id)
        target_words[chat_id] = word
        update.message.reply_text(f"Növbəti söz: '{word}'")
    else:
        update.message.reply_text("Yanlışdır! Sözü düz yaz!")
    reset_inactivity_timer(update, context)

def stop_due_to_inactivity(context: CallbackContext):
    chat_id = context.job.context
    game_active[chat_id] = False
    context.bot.send_message(chat_id=chat_id, text="10 dəqiqə heç kim yazmadı, oyun avtomatik dayandırıldı.")

def reset_inactivity_timer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if inactivity_timers.get(chat_id):
        inactivity_timers[chat_id].schedule_removal()
    inactivity_timers[chat_id] = context.job_queue.run_once(stop_due_to_inactivity, 600, context=chat_id)

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

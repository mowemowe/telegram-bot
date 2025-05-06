import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = '8121790668:AAGZtaXLTViBIw9hfEHe4bnIO4xbEH-3iXk'

WORDS = ['alma', 'çətir', 'kompyuter', 'pəncərə', 'dəftər', 'açar', 'oyuncaq', 'elektrikləşdirilmişdərdənsinizmi',
         'qələm', 'divar', 'telefon', 'çay', 'ayna', 'kitabxana', 'dəli', 'kəpənək', 'sevgi', 'bulud', 'ulduz',
         'əjdaha', 'səssizlik', 'canavar', 'pozan', 'kalkulyator', 'aşçıabbasaşasmışasmışsadaazasmış', 'zəka',
         'təhlükə', 'kölgə', 'robot', 'baki', 'samirlə qurban', 'söhbət', 'dünya', 'duman', 'sari', 'hamster',
         'qurbaqa', 'saat', 'gülümsə', 'zor', 'sual', 'top', 'uçan quş', 'raket', 'kitab', 'pizza', 'göz', 'dəvə']

game_active = {}
target_words = {}
last_words = {}
scores = {}
inactivity_timers = {}
stats = {}  # user_id: [ümumi oyun sayı, düzgün cavab sayı]

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
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        user = context.bot.get_chat_member(update.effective_chat.id, user_id).user
        leaderboard += f"{i}. {user.first_name} — {score} xal\n"
    update.message.reply_text(leaderboard)

def show_stats(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in stats:
        update.message.reply_text("Hələ heç bir oyunda iştirak etməmisən.")
        return
    total, correct = stats[user_id]
    percent = int((correct / total) * 100) if total > 0 else 0
    update.message.reply_text(f"Oyun sayı: {total}\nDüzgün cavab: {correct}\nDəqiqlik: {percent}%")

def check_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not game_active.get(chat_id, False):
        return
    user_text = update.message.text.strip().lower()
    user = update.message.from_user
    user_id = user.id

    # Stats üçün qeyd
    if user_id not in stats:
        stats[user_id] = [0, 0]
    stats[user_id][0] += 1  # ümumi oyun sayı artır

    if user_text == target_words.get(chat_id, "").lower():
        scores[user_id] = scores.get(user_id, 0) + 1
        stats[user_id][1] += 1  # düzgün cavab sayı artır
        update.message.reply_text(f"Təbriklər, {user.first_name} qazandı!\nÜmumi xalların: {scores[user_id]}")
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
    dp.add_handler(CommandHandler("tarixce", show_stats))  # yeni əmr
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

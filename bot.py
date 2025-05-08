import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

TOKEN = '8121790668:AAFRciXl87HahPfuF19M0eXaW5yAi8BaYv8'

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
stats = {}
start_times = {}

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
        start_times[chat_id] = time.time()
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
    chat_id = update.effective_chat.id
    if chat_id not in stats or not stats[chat_id]:
        update.message.reply_text("Bu söhbətdə hələ heç kim iştirak etməyib.")
        return
    user_stats = stats[chat_id]
    sorted_stats = sorted(user_stats.items(), key=lambda x: x[1][1], reverse=True)
    text = "📊 *Qrup Statistikası:*\n"
    for i, (user_id, (total, correct)) in enumerate(sorted_stats, 1):
        percent = int((correct / total) * 100) if total > 0 else 0
        try:
            user = context.bot.get_chat_member(chat_id, user_id).user
            name = user.first_name
        except:
            name = f"ID:{user_id}"
        text += f"{i}. {name} — {correct} düzgün / {total} cəmi ({percent}%)\n"
    update.message.reply_text(text, parse_mode='Markdown')

def check_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not game_active.get(chat_id, False):
        return
    user_text = update.message.text.strip().lower()
    user = update.message.from_user
    user_id = user.id
    if chat_id not in stats:
        stats[chat_id] = {}
    if user_id not in stats[chat_id]:
        stats[chat_id][user_id] = [0, 0]
    stats[chat_id][user_id][0] += 1
    if user_text == target_words.get(chat_id, "").lower():
        end_time = time.time()
        duration = round(end_time - start_times.get(chat_id, end_time), 2)

        scores[user_id] = scores.get(user_id, 0) + 1
        stats[chat_id][user_id][1] += 1
        update.message.reply_text(f"Təbriklər, {user.first_name} qazandı! ({duration} saniyəyə)\nÜmumi xalların: {scores[user_id]}")

        username = user.username or user.first_name
        context.bot.send_message(
            chat_id=chat_id,
            text=f"⭐ Günün ulduzu: @{username} — bu raundda ən sürətli cavab verdi!"
        )

        word = get_new_word(chat_id)
        target_words[chat_id] = word
        start_times[chat_id] = time.time()
        update.message.reply_text(f"Növbəti söz: '{word}'")
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

def menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🚀 Oyuna Başla", callback_data='basla'),
         InlineKeyboardButton("⛔ Oyunu Saxla", callback_data='saxla')],
        [InlineKeyboardButton("📊 Xal Cədvəli", callback_data='top'),
         InlineKeyboardButton("ℹ️ Status", callback_data='status')],
        [InlineKeyboardButton("🧠 Statistikalar", callback_data='tarixce')],
        [InlineKeyboardButton("❌ Bağla", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("⚙️ *Ayarlar Menyusu:*", reply_markup=reply_markup, parse_mode='Markdown')

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    fake_update = Update(update.update_id, message=query.message)
    if data == 'basla':
        start(fake_update, context)
    elif data == 'saxla':
        stop(fake_update, context)
    elif data == 'status':
        status(fake_update, context)
    elif data == 'top':
        top(fake_update, context)
    elif data == 'tarixce':
        show_stats(fake_update, context)
    elif data == 'close':
        query.edit_message_text("✅ Menyu bağlandı.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("basla", start))
    dp.add_handler(CommandHandler("saxla", stop))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("top", top))
    dp.add_handler(CommandHandler("tarixce", show_stats))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

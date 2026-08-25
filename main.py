import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# 1. Put your actual bot token here
BOT_TOKEN = "8932528165:AAGCsidU65K984KSEXPW8QcdVxT3bVjPBkk"

# 2. Channel & Link Settings (Bot must be an ADMIN in this channel)
CHANNEL_ID = "@googlejobhubsudeb"
CHANNEL_LINK = "https://t.me/googlejobhubsudeb"
GUIDE_LINK = "https://t.me/googlejobhubsudeb/3460"

# 3. Direct image link
BANNER_IMAGE_URL = "https://i.postimg.cc/ZRT1RJZ5/1787637100424.png"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# Check if user joined the channel
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False


# /start command
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_user_member(user_id):
        send_welcome_screen(chat_id)
    else:
        send_join_prompt(chat_id)


# Prompt to join channel
def send_join_prompt(chat_id):
    text = (
        "⚠️ <b>Access Denied!</b>\n\n"
        "You must join our official channel to use this bot.\n"
        "Click the button below to join, then tap <b>Check ✅</b>."
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    markup.row(
        InlineKeyboardButton("Check ✅", callback_data="check_subscription")
    )

    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


# Check button callback
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def handle_check(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if is_user_member(user_id):
        try:
            bot.delete_message(chat_id=chat_id, message_id=call.message.id)
        except Exception:
            pass
        send_welcome_screen(chat_id)
    else:
        bot.answer_callback_query(
            call.id, "❌ You have not joined the channel yet!", show_alert=True
        )


# Welcome Banner
def send_welcome_screen(chat_id):
    caption = (
        "💼 <b>Complete Tasks and Get Paid!</b>\n\n"
        "💵 For each task you will receive: <b>$0.20</b>\n\n"
        "✨ <b>It’s very simple:</b>\n"
        "🤖 Submit your gmail details to the bot\n"
        "📋 For every gmail sell earn 0.20$\n"
        "🏁 Earn every refer $0.05 per task approved"
    )

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("How To do task ❓", url=GUIDE_LINK))

    bot.send_photo(
        chat_id=chat_id,
        photo=BANNER_IMAGE_URL,
        caption=caption,
        reply_markup=markup,
    )


if __name__ == "__main__":
    print("Bot is running successfully...")
    bot.infinity_polling()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# 1. Put your BotFather token here
BOT_TOKEN = "8932528165:AAGuepEKPlBSknT0Cn91KcTlSZlEOH5nh60"

# 2. Channel settings (Make sure your bot is an ADMIN in your channel)
CHANNEL_ID = "@googlejobhubsudeb"
CHANNEL_LINK = "https://t.me/googlejobhubsudeb"
GUIDE_LINK = "https://t.me/googlejobhubsudeb/3460"

# 3. Your direct postimg link from earlier
BANNER_IMAGE_URL = "https://i.postimg.cc/ZRT1RJZ5/1787637100424.png"


# Check if user is in the channel
async def is_user_member(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except TelegramError:
        return False


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if await is_user_member(context.bot, user_id):
        await send_welcome_screen(chat_id, context)
    else:
        await send_join_prompt(chat_id, context)


# Prompt user to join the channel
async def send_join_prompt(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚠️ <b>Access Denied!</b>\n\n"
        "You must join our official channel to use this bot.\n"
        "Click the button below to join, then tap <b>Check ✅</b>."
    )
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Check ✅", callback_data="check_subscription")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )


# Handler for the "Check ✅" button
async def handle_check_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if await is_user_member(context.bot, user_id):
        await query.message.delete()
        await send_welcome_screen(chat_id, context)
    else:
        await query.answer(
            "❌ You have not joined the channel yet!", show_alert=True
        )


# Welcome banner with formatted text and button
async def send_welcome_screen(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "💼 <b>Complete Tasks and Get Paid!</b>\n\n"
        "💵 For each task you will receive: <b>$0.20</b>\n\n"
        "✨ <b>It’s very simple:</b>\n"
        "🤖 Submit your gmail details to the bot\n"
        "📋 For every gmail sell earn 0.20$\n"
        "🏁 Earn every refer $0.05 per task approved"
    )

    inline_keyboard = [
        [InlineKeyboardButton("How To do task ❓", url=GUIDE_LINK)]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=BANNER_IMAGE_URL,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=inline_markup,
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        CallbackQueryHandler(
            handle_check_button, pattern="^check_subscription$"
        )
    )

    print("Bot is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

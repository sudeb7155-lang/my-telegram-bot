import io
import urllib.request
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- Configurations ---
BOT_TOKEN = "8902730851:AAGkd2yeSywLUWdwGK7S-Q0RhTLMo84HpA0"
ADMIN_ID = 6112720850

CHANNEL_ID = "@googlejobhubsudeb"
CHANNEL_LINK = "https://t.me/googlejobhubsudeb"
GUIDE_LINK = "https://t.me/googlejobhubsudeb/3460"

# --- Dedicated Image URLs ---
IMG_MAIN_DASHBOARD  = "https://i.postimg.cc/ZRT1RJZ5/1787637100424.png"
IMG_ACCESS_DENIED   = "https://i.postimg.cc/y867gtR9/1787647894179.png"
IMG_STEP_1          = "https://i.postimg.cc/fR3DfXH5/1787648315087.png"
IMG_STEP_2          = "https://i.postimg.cc/KjgD50gq/1787648456890.png"
IMG_STEP_3          = "https://i.postimg.cc/76qL9hJ5/1787648563973.png"
IMG_STEP_4          = "https://i.postimg.cc/SKMZdNFf/1787648824010.png"
IMG_TASK_REVIEW_BOX = "https://i.postimg.cc/MpdtqPVP/1787649087021.png"
IMG_TASK_SUBMITTED  = "https://i.postimg.cc/3JpmtLtv/1787649259762.png"
IMG_ACCOUNT_STATUS  = "https://i.postimg.cc/jjk4pDPM/IMG-20260825-145145-076.jpg"
IMG_BALANCE         = "https://i.postimg.cc/pTRPtdvR/IMG-20260825-145336-476.jpg"
IMG_REFERRAL        = "https://i.postimg.cc/W4syNqdw/IMG-20260825-145510-251.jpg"
IMG_SUPPORT         = "https://i.postimg.cc/QthSg2Qy/1787650073869.png"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# In-memory database structures
users = {}          # {user_id: {"balance": 0.0, "pending": 0.0, "referrer": id, "referrals": 0, "referral_approvals": 0}}
tasks = {}          # {task_id: {"user_id": id, "step1": str, "step2": str, "step3": str, "step4": str, "status": str}}
withdrawals = {}    # {wd_id: {"user_id": id, "amount": float, "method": str, "address": str, "status": str}}
user_sessions = {}  # {user_id: {"flow": str, "step": str, "data": dict}}
admin_broadcast_state = {}

task_counter = 1001
withdraw_counter = 5001


def send_safe_photo(chat_id, url, caption="", reply_markup=None):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    if url and url.startswith("http"):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as response:
                img_data = response.read()
                img_io = io.BytesIO(img_data)
                img_io.name = "photo.jpg"
                return bot.send_photo(chat_id, photo=img_io, caption=caption, reply_markup=reply_markup)
        except Exception:
            pass

        try:
            return bot.send_photo(chat_id, photo=url, caption=caption, reply_markup=reply_markup)
        except Exception:
            pass

    return bot.send_message(chat_id, text=caption, reply_markup=reply_markup)


def get_user(user_id, referrer_id=None):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.0,
            "pending": 0.0,
            "referrer": referrer_id,
            "referrals": 0,
            "referral_approvals": 0,
        }
    return users[user_id]


def is_channel_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True  # Fallback to avoid blocking testing if channel isn't bound


def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📋 Task", callback_data="btn_task"),
        InlineKeyboardButton("📊 Account Status", callback_data="btn_status"),
        InlineKeyboardButton("💰 Balance", callback_data="btn_balance"),
        InlineKeyboardButton("👥 My Referral", callback_data="btn_referral"),
        InlineKeyboardButton("🆘 Support", callback_data="btn_support"),
        InlineKeyboardButton("📺 Tutorial", url=GUIDE_LINK),
    )
    return markup


def cancel_btn():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="btn_cancel"))
    return markup


def send_home(chat_id):
    caption = (
        "💼 <b>Complete Tasks and Get Paid!</b>\n\n"
        "💵 For each task you will receive: <b>$0.20</b>\n\n"
        "✨ <b>It’s very simple:</b>\n"
        "🤖 Follow the assigned bot instructions\n"
        "📋 Complete tasks to earn rewards\n"
        "🏁 Earn referral bonuses for active users"
    )
    send_safe_photo(chat_id, IMG_MAIN_DASHBOARD, caption=caption, reply_markup=main_menu())


# --- Entry Point ---

@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        ref = int(args[1])
        if ref != user_id and ref in users:
            referrer_id = ref
            users[referrer_id]["referrals"] += 1

    get_user(user_id, referrer_id)

    if is_channel_member(user_id):
        send_home(chat_id)
    else:
        text = (
            "⚠️ <b>Access Denied!</b>\n\n"
            "You must join our official channel to use this bot.\n"
            "Click below to join, then tap <b>Check ✅</b>."
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        markup.row(InlineKeyboardButton("Check ✅", callback_data="check_sub"))
        send_safe_photo(chat_id, IMG_ACCESS_DENIED, caption=text, reply_markup=markup)


# --- Admin Broadcast Engine ---

@bot.message_handler(commands=["broadcast", "broadcast_pin"])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        return

    should_pin = message.text.startswith("/broadcast_pin")
    admin_broadcast_state[ADMIN_ID] = {
        "step": "AWAIT_BC_IMAGE",
        "pin": should_pin,
        "image_url": None,
        "caption": ""
    }

    pin_note = "📌 <b>PIN MODE ENABLED</b> (will auto-pin in all chats)\n\n" if should_pin else ""
    bot.send_message(
        ADMIN_ID,
        f"📢 <b>ADMIN BROADCAST CREATOR</b>\n{pin_note}"
        "<b>Step 1:</b> Send the image URL for the broadcast (or type <code>skip</code> to send text only):"
    )


@bot.message_handler(func=lambda msg: msg.from_user.id == ADMIN_ID and ADMIN_ID in admin_broadcast_state)
def process_broadcast_creation(message):
    state = admin_broadcast_state[ADMIN_ID]
    step = state["step"]

    if step == "AWAIT_BC_IMAGE":
        img_input = message.text.strip()
        state["image_url"] = None if img_input.lower() == "skip" else img_input
        state["step"] = "AWAIT_BC_TEXT"
        bot.send_message(
            ADMIN_ID,
            "<b>Step 2:</b> Enter the broadcast message text.\n"
            "• Supports Telegram HTML & Premium Emojis."
        )

    elif step == "AWAIT_BC_TEXT":
        state["caption"] = message.text
        img_url = state["image_url"]
        caption = state["caption"]
        pin_flag = "Yes" if state["pin"] else "No"

        preview_markup = InlineKeyboardMarkup()
        preview_markup.row(
            InlineKeyboardButton("🚀 Send Broadcast Now", callback_data="adm_send_bc"),
            InlineKeyboardButton("❌ Cancel", callback_data="adm_cancel_bc")
        )

        bot.send_message(ADMIN_ID, f"🔍 <b>BROADCAST PREVIEW (Auto-Pin: {pin_flag})</b>:")
        if img_url:
            send_safe_photo(ADMIN_ID, img_url, caption=caption, reply_markup=preview_markup)
        else:
            bot.send_message(ADMIN_ID, text=caption, reply_markup=preview_markup)


# --- Universal Form Inputs Handler ---

@bot.message_handler(func=lambda msg: msg.from_user.id in user_sessions)
def handle_user_inputs(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    session = user_sessions[user_id]
    flow = session.get("flow")
    step = session.get("step")
    text = message.text.strip()

    if flow == "TASK":
        if step == "STEP_1":
            if not text.lower().endswith("@gmail.com") or "@" not in text:
                bot.reply_to(
                    message,
                    "❌ <b>Invalid Gmail!</b> Address must end with <code>@gmail.com</code>:",
                    reply_markup=cancel_btn(),
                )
                return

            session["data"]["step1"] = text
            session["step"] = "STEP_2"
            send_safe_photo(chat_id, IMG_STEP_2, caption="<b>Step 2:</b>", reply_markup=cancel_btn())

        elif step == "STEP_2":
            session["data"]["step2"] = text
            session["step"] = "STEP_3"
            send_safe_photo(chat_id, IMG_STEP_3, caption="<b>Step 3:</b>", reply_markup=cancel_btn())

        elif step == "STEP_3":
            session["data"]["step3"] = text
            session["step"] = "STEP_4"
            send_safe_photo(chat_id, IMG_STEP_4, caption="<b>Step 4:</b>", reply_markup=cancel_btn())

        elif step == "STEP_4":
            session["data"]["step4"] = text
            session["step"] = "CONFIRM"

            data = session["data"]
            summary = (
                "╔══════════════════════════╗\n"
                "   📝 <b>TASK SUBMISSION BOX</b>\n"
                "╚══════════════════════════╝\n\n"
                f"📧 <b>Step 1:</b> <code>{data.get('step1')}</code>\n"
                f"🔹 <b>Step 2:</b> <code>{data.get('step2')}</code>\n"
                f"🔹 <b>Step 3:</b> <code>{data.get('step3')}</code>\n"
                f"🔹 <b>Step 4:</b> <code>{data.get('step4')}</code>\n\n"
                "<b>Done would you like to submit ❓</b>"
            )
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("Submit ✅", callback_data="btn_submit_final"),
                InlineKeyboardButton("Cancel ❌", callback_data="btn_cancel"),
            )
            send_safe_photo(chat_id, IMG_TASK_REVIEW_BOX, caption=summary, reply_markup=markup)

    elif flow == "WITHDRAW" and step == "AWAIT_ADDRESS":
        global withdraw_counter
        method = session["data"]["method"]
        user = get_user(user_id)
        amount = user["balance"]

        wd_id = str(withdraw_counter)
        withdraw_counter += 1

        user["balance"] = 0.0
        user_sessions.pop(user_id, None)

        withdrawals[wd_id] = {
            "user_id": user_id,
            "amount": amount,
            "method": method,
            "address": text,
            "status": "pending"
        }

        bot.send_message(
            chat_id,
            f"✅ <b>Withdrawal Request Submitted!</b>\n\n"
            f"🆔 <b>Request ID:</b> <code>#{wd_id}</code>\n"
            f"💵 <b>Amount:</b> ${amount:.2f}\n"
            f"💳 <b>Method:</b> {method}\n"
            f"📍 <b>Account/Address:</b> <code>{text}</code>\n\n"
            "<i>Your request is being reviewed by the admin.</i>"
        )
        send_home(chat_id)

        admin_card = (
            f"🚨 <b>NEW WITHDRAWAL REQUEST (#{wd_id})</b>\n\n"
            f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
            f"💵 <b>Amount:</b> ${amount:.2f}\n"
            f"💳 <b>Method:</b> {method}\n"
            f"📍 <b>Address/UPI:</b> <code>{text}</code>"
        )
        admin_markup = InlineKeyboardMarkup()
        admin_markup.row(
            InlineKeyboardButton("Paid / Approve ✅", callback_data=f"wdapp_{wd_id}"),
            InlineKeyboardButton("Reject ❌", callback_data=f"wdrej_{wd_id}")
        )
        try:
            bot.send_message(ADMIN_ID, admin_card, reply_markup=admin_markup)
        except Exception:
            pass


# --- Callback Router ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    global task_counter

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    # Start Task
    if call.data == "btn_task":
        user_sessions[user_id] = {"flow": "TASK", "step": "STEP_1", "data": {}}
        caption = (
            "⚠️ <b>Before submit watch tutorial video carefully</b>\n\n"
            "<b>Step 1:</b> Submit your gmail address make sure (@gmail.com):"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📺 Tutorial", url=GUIDE_LINK))
        markup.row(InlineKeyboardButton("❌ Cancel", callback_data="btn_cancel"))
        send_safe_photo(chat_id, IMG_STEP_1, caption=caption, reply_markup=markup)

    # Submit Task Final Step
    elif call.data == "btn_submit_final":
        session = user_sessions.pop(user_id, None)
        if session and "data" in session:
            data = session["data"]
            task_id = str(task_counter)
            task_counter += 1

            tasks[task_id] = {
                "user_id": user_id,
                "step1": data.get("step1"),
                "step2": data.get("step2"),
                "step3": data.get("step3"),
                "step4": data.get("step4"),
                "status": "pending",
            }
            get_user(user_id)["pending"] += 0.20

            caption = (
                "✅ <b>Your task in review admin will review soon</b>\n"
                "<b>Expected time 24-72h</b>\n\n"
                f"🆔 <b>Task ID:</b> <code>#{task_id}</code>"
            )
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
            send_safe_photo(chat_id, IMG_TASK_SUBMITTED, caption=caption, reply_markup=markup)

            admin_msg = (
                f"🔔 <b>New Task Submitted (#{task_id})</b>\n\n"
                f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
                f"📧 <b>Step 1:</b> <code>{data.get('step1')}</code>\n"
                f"🔹 <b>Step 2:</b> <code>{data.get('step2')}</code>\n"
                f"🔹 <b>Step 3:</b> <code>{data.get('step3')}</code>\n"
                f"🔹 <b>Step 4:</b> <code>{data.get('step4')}</code>"
            )
            admin_markup = InlineKeyboardMarkup()
            admin_markup.row(
                InlineKeyboardButton("Approve ✅", callback_data=f"adm_app_{task_id}"),
                InlineKeyboardButton("Reject ❌", callback_data=f"adm_rej_{task_id}"),
            )
            try:
                bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
            except Exception:
                pass
        else:
            bot.send_message(chat_id, "⚠️ No active task found. Please restart via Task button.")
            send_home(chat_id)

    # Broadcast Execution
    elif call.data == "adm_cancel_bc":
        admin_broadcast_state.pop(ADMIN_ID, None)
        bot.send_message(ADMIN_ID, "❌ Broadcast cancelled.")

    elif call.data == "adm_send_bc":
        if ADMIN_ID not in admin_broadcast_state:
            bot.send_message(ADMIN_ID, "⚠️ No broadcast queued.")
            return

        state = admin_broadcast_state.pop(ADMIN_ID)
        img_url = state["image_url"]
        caption = state["caption"]
        should_pin = state["pin"]

        sent_count = 0
        bot.send_message(ADMIN_ID, "⏳ <i>Sending broadcast to all bot users...</i>")

        # Collect target users (fallback to ADMIN_ID if users dict is empty during test)
        target_ids = set(users.keys())
        target_ids.add(ADMIN_ID)

        for target_id in target_ids:
            try:
                sent_msg = None
                if img_url:
                    sent_msg = send_safe_photo(target_id, img_url, caption=caption)
                else:
                    sent_msg = bot.send_message(chat_id=target_id, text=caption)

                if should_pin and sent_msg:
                    try:
                        bot.pin_chat_message(chat_id=target_id, message_id=sent_msg.message_id)
                    except Exception:
                        pass
                sent_count += 1
            except Exception:
                continue

        bot.send_message(ADMIN_ID, f"✅ <b>Broadcast Completed!</b>\nDelivered to {sent_count} chats.")

    elif call.data == "check_sub":
        if is_channel_member(user_id):
            send_home(chat_id)
        else:
            bot.send_message(chat_id, "❌ You have not joined the channel yet!")

    elif call.data == "btn_cancel":
        user_sessions.pop(user_id, None)
        bot.send_message(chat_id, "❌ Action cancelled.")
        send_home(chat_id)

    # Admin Task Review
    elif call.data.startswith("adm_app_") or call.data.startswith("adm_rej_"):
        if user_id != ADMIN_ID:
            return

        action = "app" if "adm_app_" in call.data else "rej"
        tid = call.data.split("_")[2]
        task = tasks.get(tid)

        if not task or task["status"] != "pending":
            return

        t_user_id = task["user_id"]
        t_user = get_user(t_user_id)

        if action == "app":
            task["status"] = "approved"
            t_user["balance"] += 0.20
            t_user["pending"] = max(0.0, t_user["pending"] - 0.20)

            ref_id = t_user.get("referrer")
            if ref_id and ref_id in users:
                users[ref_id]["balance"] += 0.05
                users[ref_id]["referral_approvals"] += 1
                try:
                    bot.send_message(
                        ref_id,
                        "🎉 <b>Referral Bonus Added!</b>\n\n"
                        "Your referred friend's task has been approved.\n"
                        "💵 <b>+$0.05</b> has been added to your balance!"
                    )
                except Exception:
                    pass

            try:
                bot.send_message(t_user_id, f"🎉 <b>Task #{tid} Approved!</b>\n+$0.20 added to your active balance.")
            except Exception:
                pass
            bot.send_message(ADMIN_ID, f"✅ <b>Task #{tid} Approved</b> by Admin.")

        elif action == "rej":
            task["status"] = "rejected"
            t_user["pending"] = max(0.0, t_user["pending"] - 0.20)
            try:
                bot.send_message(t_user_id, f"❌ <b>Task #{tid} Rejected.</b>")
            except Exception:
                pass
            bot.send_message(ADMIN_ID, f"❌ <b>Task #{tid} Rejected</b> by Admin.")

    # Admin Withdrawal Review
    elif call.data.startswith("wdapp_") or call.data.startswith("wdrej_"):
        if user_id != ADMIN_ID:
            return

        action = "app" if call.data.startswith("wdapp_") else "rej"
        wd_id = call.data.split("_")[1]
        wd = withdrawals.get(wd_id)

        if not wd or wd["status"] != "pending":
            return

        t_user_id = wd["user_id"]
        t_user = get_user(t_user_id)

        if action == "app":
            wd["status"] = "approved"
            try:
                bot.send_message(
                    t_user_id,
                    f"🎉 <b>Payment Received & Approved! ✅</b>\n\n"
                    f"💵 <b>Amount:</b> ${wd['amount']:.2f}\n"
                    f"💳 <b>Method:</b> {wd['method']}\n"
                    f"📍 <b>Account/Address:</b> <code>{wd['address']}</code>"
                )
            except Exception:
                pass
            bot.send_message(ADMIN_ID, f"✅ <b>Withdrawal #{wd_id} Marked as Paid.</b>")

        elif action == "rej":
            wd["status"] = "rejected"
            t_user["balance"] += wd["amount"]
            try:
                bot.send_message(
                    t_user_id,
                    f"❌ <b>Withdrawal Request #{wd_id} Rejected.</b>\n"
                    f"<b>${wd['amount']:.2f}</b> refunded to your active balance."
                )
            except Exception:
                pass
            bot.send_message(ADMIN_ID, f"❌ <b>Withdrawal #{wd_id} Rejected & Refunded.</b>")

    elif call.data == "btn_back":
        send_home(chat_id)

    elif call.data == "btn_status":
        history_lines = []
        for tid, t in tasks.items():
            if t.get("user_id") == user_id:
                status_raw = t.get("status", "pending")
                reward = " | Approved 0.20$+" if status_raw == "approved" else ""
                history_lines.append(
                    f"• <b>Task ID:</b> #{tid}\n"
                    f"  <b>Step 1:</b> <code>{t.get('step1', 'N/A')}</code>\n"
                    f"  <b>Status:</b> <b>{status_raw.upper()}</b>{reward}"
                )

        history_str = "\n\n".join(history_lines) if history_lines else "No task submissions found."
        caption = f"📊 <b>MY ACCOUNTS HISTORY</b>\n\n{history_str}"

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📋 Submit Task", callback_data="btn_task"))
        markup.row(InlineKeyboardButton("📺 Tutorial", url=GUIDE_LINK))
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        send_safe_photo(chat_id, IMG_ACCOUNT_STATUS, caption=caption, reply_markup=markup)

    elif call.data == "btn_balance":
        u = get_user(user_id)
        caption = (
            "💰 <b>Your balance history</b>\n\n"
            f"💵 <b>Active balance:</b> ${u['balance']:.2f}\n"
            f"⏳ <b>Pending:</b> ${u['pending']:.2f}\n\n"
            "💳 <b>Minimum withdrawal $0.2/₹18</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💳 Withdrawal", callback_data="btn_withdraw"))
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        send_safe_photo(chat_id, IMG_BALANCE, caption=caption, reply_markup=markup)

    elif call.data == "btn_referral":
        u = get_user(user_id)
        bot_info = bot.get_me()
        invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
        total_earned = u["referral_approvals"] * 0.05

        caption = (
            "👥 <b>MY REFERRAL NETWORK</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Total Earnings:</b> ${total_earned:.2f}\n"
            f"👥 <b>Invited Users:</b> {u['referrals']}\n"
            f"✅ <b>Referral Approvals:</b> {u['referral_approvals']}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎁 <b>Your Reward:</b>\n"
            "Get $0.05 for every approved account your friends make!\n\n"
            f"👇 <b>Your Invite link :-</b>\n<code>{invite_link}</code>"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        send_safe_photo(chat_id, IMG_REFERRAL, caption=caption, reply_markup=markup)

    elif call.data == "btn_support":
        caption = (
            "🆘 <b>Support</b>\n\n"
            "We are actively reply 24×7 now\n"
            "Please type your questions in admin section <b>@SUDEBNOMERCY</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        send_safe_photo(chat_id, IMG_SUPPORT, caption=caption, reply_markup=markup)

    elif call.data == "btn_withdraw":
        u = get_user(user_id)
        if u["balance"] < 0.20:
            bot.send_message(chat_id, "❌ <b>Minimum withdrawal balance is $0.20 / ₹18!</b>")
        else:
            text = (
                "💳 <b>Select Your Payment Method:</b>\n\n"
                f"💵 <b>Available Balance:</b> ${u['balance']:.2f}\n\n"
                "Choose an option below to proceed:"
            )
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("🇮🇳 UPI (India)", callback_data="wd_method_upi"),
                InlineKeyboardButton("💵 USDT (Crypto)", callback_data="wd_method_usdt")
            )
            markup.row(InlineKeyboardButton("❌ Cancel", callback_data="btn_cancel"))
            bot.send_message(chat_id, text=text, reply_markup=markup)

    elif call.data in ["wd_method_upi", "wd_method_usdt"]:
        method = "UPI (India)" if call.data == "wd_method_upi" else "USDT (BEP20 / TRC20)"
        user_sessions[user_id] = {
            "flow": "WITHDRAW",
            "step": "AWAIT_ADDRESS",
            "data": {"method": method}
        }
        prompt_text = "🇮🇳 <b>Enter your UPI ID</b>:" if call.data == "wd_method_upi" else "💵 <b>Enter your USDT Wallet Address</b>:"
        bot.send_message(chat_id, prompt_text, reply_markup=cancel_btn())


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)

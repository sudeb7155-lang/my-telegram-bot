import time
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# --- Configurations ---
BOT_TOKEN = "8902730851:AAHBRDhlBe_7Bslo691CzbatqYL6KkMEjYk"
ADMIN_ID =  6112720850 # Replace with your numerical Telegram user ID

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

# In-memory storage
users = {}          # {user_id: {"balance": 0.0, "pending": 0.0, "referrer": id, "referrals": 0, "referral_approvals": 0}}
tasks = {}          # {task_id: {"user_id": id, "email": str, "field2": str, "field3": str, "field4": str, "status": str}}
user_sessions = {}   # {user_id: {"step": str, "data": dict}}
admin_broadcast_state = {} # Stores broadcast draft state for admin
task_counter = 1001


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
        return False


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


# --- Entry & Membership ---

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
        bot.send_photo(chat_id, photo=IMG_ACCESS_DENIED, caption=text, reply_markup=markup)


def send_home(chat_id):
    caption = (
        "💼 <b>Complete Tasks and Get Paid!</b>\n\n"
        "💵 For each task you will receive: <b>$0.20</b>\n\n"
        "✨ <b>It’s very simple:</b>\n"
        "🤖 Follow the assigned bot instructions\n"
        "📋 Complete tasks to earn rewards\n"
        "🏁 Earn referral bonuses for active users"
    )
    bot.send_photo(chat_id, photo=IMG_MAIN_DASHBOARD, caption=caption, reply_markup=main_menu())


# --- Admin Broadcast Engine with Live Images & Pinned Messages ---

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
        if img_input.lower() != "skip":
            state["image_url"] = img_input
        else:
            state["image_url"] = None

        state["step"] = "AWAIT_BC_TEXT"
        bot.send_message(
            ADMIN_ID,
            "<b>Step 2:</b> Enter the broadcast message text.\n"
            "• You can use Telegram Premium Emojis & HTML (<code>&lt;b&gt;bold&lt;/b&gt;</code>, <code>&lt;tg-emoji id=&quot;...&quot;&gt;🔥&lt;/tg-emoji&gt;</code>)."
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
            bot.send_photo(ADMIN_ID, photo=img_url, caption=caption, reply_markup=preview_markup)
        else:
            bot.send_message(ADMIN_ID, text=caption, reply_markup=preview_markup)


# --- 4-Step Form Flow with Attached Images ---

@bot.callback_query_handler(func=lambda call: call.data == "btn_task")
def start_task(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    user_sessions[user_id] = {"step": "STEP_1", "data": {}}

    caption = (
        "⚠️ <b>Before submit watch tutorial video carefully</b>\n\n"
        "<b>Step 1:</b> Submit your gmail address make sure (@gmail.com):"
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📺 Tutorial", url=GUIDE_LINK))
    markup.row(InlineKeyboardButton("❌ Cancel", callback_data="btn_cancel"))

    bot.send_photo(chat_id, photo=IMG_STEP_1, caption=caption, reply_markup=markup)


@bot.message_handler(func=lambda msg: msg.from_user.id in user_sessions)
def handle_form_steps(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    session = user_sessions[user_id]
    step = session["step"]

    # Step 1: Gmail
    if step == "STEP_1":
        val = message.text.strip()
        if not val.endswith("@gmail.com") or "@" not in val:
            bot.reply_to(
                message,
                "❌ <b>Invalid Gmail!</b> Address must end with <code>@gmail.com</code>:",
                reply_markup=cancel_btn(),
            )
            return

        session["data"]["email"] = val
        session["step"] = "STEP_2"
        bot.send_photo(
            chat_id,
            photo=IMG_STEP_2,
            caption="<b>Step 2:</b> Enter your worker username / name:",
            reply_markup=cancel_btn(),
        )

    # Step 2: Name & 3-sec check simulation
    elif step == "STEP_2":
        session["data"]["field2"] = message.text.strip()
        
        status_msg = bot.send_message(chat_id, "⏳ <i>Hold on we are checking 3 second waiting checking.....</i>")
        time.sleep(3)
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass

        session["step"] = "STEP_3"
        bot.send_photo(
            chat_id,
            photo=IMG_STEP_3,
            caption="<b>Step 3:</b> Enter your task proof / work reference ID:",
            reply_markup=cancel_btn(),
        )

    # Step 3: Reference
    elif step == "STEP_3":
        session["data"]["field3"] = message.text.strip()
        session["step"] = "STEP_4"
        bot.send_photo(
            chat_id,
            photo=IMG_STEP_4,
            caption="<b>Step 4:</b> Enter any additional task notes (or type 'None'):",
            reply_markup=cancel_btn(),
        )

    # Step 4: Notes & Final Confirmation Box
    elif step == "STEP_4":
        session["data"]["field4"] = message.text.strip()
        session["step"] = "CONFIRM"

        data = session["data"]
        summary = (
            "╔══════════════════════════╗\n"
            "   📝 <b>TASK SUBMISSION BOX</b>\n"
            "╚══════════════════════════╝\n\n"
            f"📧 <b>Gmail:</b> <code>{data['email']}</code>\n"
            f"👤 <b>Worker:</b> <code>{data['field2']}</code>\n"
            f"🆔 <b>Task Proof:</b> <code>{data['field3']}</code>\n"
            f"📝 <b>Notes:</b> <code>{data['field4']}</code>\n\n"
            "<b>Done would you like to submit ❓</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Submit ✅", callback_data="btn_submit_final"),
            InlineKeyboardButton("Cancel ❌", callback_data="btn_cancel"),
        )
        bot.send_photo(chat_id, photo=IMG_TASK_REVIEW_BOX, caption=summary, reply_markup=markup)


# --- Callback Router ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    global task_counter

    # Broadcast Execution
    if call.data == "adm_cancel_bc":
        admin_broadcast_state.pop(ADMIN_ID, None)
        bot.edit_message_text("❌ Broadcast cancelled.", chat_id=ADMIN_ID, message_id=call.message.id)

    elif call.data == "adm_send_bc":
        if ADMIN_ID not in admin_broadcast_state:
            return
        
        state = admin_broadcast_state.pop(ADMIN_ID)
        img_url = state["image_url"]
        caption = state["caption"]
        should_pin = state["pin"]

        sent_count = 0
        bot.edit_message_text("⏳ <i>Sending broadcast to all bot users...</i>", chat_id=ADMIN_ID, message_id=call.message.id)

        for target_id in list(users.keys()):
            try:
                sent_msg = None
                if img_url:
                    sent_msg = bot.send_photo(chat_id=target_id, photo=img_url, caption=caption)
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

        bot.send_message(ADMIN_ID, f"✅ <b>Broadcast Completed!</b>\nSuccessfully delivered to {sent_count} users.")

    elif call.data == "check_sub":
        if is_channel_member(user_id):
            bot.delete_message(chat_id, call.message.id)
            send_home(chat_id)
        else:
            bot.answer_callback_query(call.id, "❌ You have not joined the channel yet!", show_alert=True)

    elif call.data == "btn_cancel":
        user_sessions.pop(user_id, None)
        bot.send_message(chat_id, "❌ Task submission cancelled.")
        send_home(chat_id)

    elif call.data == "btn_submit_final":
        if user_id in user_sessions:
            data = user_sessions.pop(user_id, {}).get("data", {})
            task_id = str(task_counter)
            task_counter += 1

            tasks[task_id] = {
                "user_id": user_id,
                "email": data.get("email"),
                "field2": data.get("field2"),
                "field3": data.get("field3"),
                "field4": data.get("field4"),
                "status": "pending",
            }
            users[user_id]["pending"] += 0.20

            caption = (
                "✅ <b>Your task in review admin will review soon</b>\n"
                "<b>Expected time 24-72h</b>\n\n"
                f"🆔 <b>Task ID:</b> <code>#{task_id}</code>"
            )
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
            bot.send_photo(chat_id, photo=IMG_TASK_SUBMITTED, caption=caption, reply_markup=markup)

            # Admin Review Card
            admin_msg = (
                f"🔔 <b>New Task Submitted (#{task_id})</b>\n\n"
                f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
                f"📧 <b>Gmail:</b> <code>{data.get('email')}</code>\n"
                f"👤 <b>Worker:</b> <code>{data.get('field2')}</code>\n"
                f"🆔 <b>Proof:</b> <code>{data.get('field3')}</code>\n"
                f"📝 <b>Notes:</b> <code>{data.get('field4')}</code>"
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

    # Admin actions
    elif call.data.startswith("adm_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Unauthorized.", show_alert=True)
            return

        action, tid = call.data.split("_")[1], call.data.split("_")[2]
        task = tasks.get(tid)

        if not task or task["status"] != "pending":
            bot.answer_callback_query(call.id, "Already processed.", show_alert=True)
            return

        t_user_id = task["user_id"]
        t_user = users.get(t_user_id, {})

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

            bot.send_message(t_user_id, f"🎉 <b>Task #{tid} Approved!</b>\n+$0.20 added to your active balance.")
            bot.edit_message_text(f"✅ <b>Task #{tid} Approved</b> by Admin.", chat_id=ADMIN_ID, message_id=call.message.id)

        elif action == "rej":
            task["status"] = "rejected"
            t_user["pending"] = max(0.0, t_user["pending"] - 0.20)
            bot.send_message(t_user_id, f"❌ <b>Task #{tid} Rejected.</b>")
            bot.edit_message_text(f"❌ <b>Task #{tid} Rejected</b> by Admin.", chat_id=ADMIN_ID, message_id=call.message.id)

    elif call.data == "btn_back":
        send_home(chat_id)

    elif call.data == "btn_status":
        history_lines = []
        for tid, t in tasks.items():
            if t["user_id"] == user_id:
                reward = " | Approved 0.20$+" if t["status"] == "approved" else ""
                history_lines.append(
                    f"• <b>Task ID:</b> #{tid}\n"
                    f"  Gmail: <code>{t['email']}</code>\n"
                    f"  Proof: <code>{t['field3']}</code>\n"
                    f"  Status: <b>{t['status'].upper()}</b>{reward}"
                )

        history_str = "\n\n".join(history_lines) if history_lines else "No task submissions found."
        caption = f"📊 <b>MY ACCOUNTS HISTORY</b>\n\n{history_str}"

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📋 Submit Task", callback_data="btn_task"))
        markup.row(InlineKeyboardButton("📺 Tutorial", url=GUIDE_LINK))
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        bot.send_photo(chat_id, photo=IMG_ACCOUNT_STATUS, caption=caption, reply_markup=markup)

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
        bot.send_photo(chat_id, photo=IMG_BALANCE, caption=caption, reply_markup=markup)

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
        bot.send_photo(chat_id, photo=IMG_REFERRAL, caption=caption, reply_markup=markup)

    elif call.data == "btn_support":
        caption = (
            "🆘 <b>Support</b>\n\n"
            "We are actively reply 24×7 now\n"
            "Please type your questions in admin section <b>@SUDEBNOMERCY</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="btn_back"))
        bot.send_photo(chat_id, photo=IMG_SUPPORT, caption=caption, reply_markup=markup)

    elif call.data == "btn_withdraw":
        u = get_user(user_id)
        if u["balance"] < 0.20:
            bot.answer_callback_query(call.id, "❌ Minimum withdrawal balance is $0.20!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "✅ Withdrawal requested! Admin will process your payout.", show_alert=True)


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

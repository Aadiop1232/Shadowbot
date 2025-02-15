# handlers.py
import logging
import sqlite3
import csv
import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from config import REQUIRED_CHANNELS
from database import (
    add_user, mark_user_verified, get_user, add_user_log,
    is_admin, is_owner, generate_key, ban_user, unban_user, add_admin
)

logger = logging.getLogger(__name__)
USERS_PER_PAGE = 10

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    add_user(user.id, user.username)
    if is_admin(user.id):
        mark_user_verified(user.id)
        update.message.reply_text(
            "Welcome Admin/Owner! You are auto verified.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        welcome = (
            f"Hey {user.first_name}, Welcome To Shadow Rewards Bot!\n"
            "Please verify yourself by joining the below channels."
        )
        update.message.reply_photo(
            photo="https://i.imgur.com/mDAjGNm.jpeg",
            caption=welcome,
            reply_markup=get_verification_keyboard()
        )

def verify_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if is_admin(user_id):
        mark_user_verified(user_id)
        query.answer("Welcome Admin/Owner! You are auto verified.")
        query.edit_message_text(
            text="You are verified! Welcome to the main menu.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    not_joined = []
    for channel in REQUIRED_CHANNELS:
        try:
            member_status = context.bot.get_chat_member(chat_id=channel, user_id=user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                not_joined.append(channel)
        except Exception as e:
            logger.error(f"Error checking channel {channel}: {e}")
            not_joined.append(channel)

    if not_joined:
        text = "Please join the following channels:\n" + "\n".join(not_joined)
        query.answer()
        query.edit_message_text(text=text, reply_markup=get_verification_keyboard())
    else:
        mark_user_verified(user_id)
        add_user_log(user_id, "Verified")
        query.answer("You are verified! Welcome to the main menu.")
        context.bot.send_message(
            chat_id=user_id,
            text="You are verified! Welcome to the main menu.",
            reply_markup=get_main_menu_keyboard()
        )

def change_lang_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Language feature is disabled.")
    query.edit_message_text(
        text="Language feature is disabled.",
        reply_markup=get_main_menu_keyboard()
    )

def set_language_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer("Language feature is disabled.")
    query.edit_message_text(
        text="Language feature is disabled.",
        reply_markup=get_main_menu_keyboard()
    )

def menu_help_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    help_text = (
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/claim <key> - Claim a reward key\n"
        "/ban <user_id> - Ban a user (admin only)\n"
        "/unban <user_id> - Unban a user (admin only)\n"
        "/addowner <user_id> - Add a new owner (owner only)"
    )
    query.edit_message_text(text=help_text, reply_markup=get_main_menu_keyboard())

def ban_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Access denied. Only admins can ban users.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        target = int(context.args[0])
        ban_user(target)
        update.message.reply_text(f"User {target} has been banned.")
    except ValueError:
        update.message.reply_text("User ID must be a number.")

def unban_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Access denied. Only admins can unban users.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        target = int(context.args[0])
        unban_user(target)
        update.message.reply_text(f"User {target} has been unbanned.")
    except ValueError:
        update.message.reply_text("User ID must be a number.")

def add_owner_command(update: Update, context: CallbackContext):
    requesting_user = update.effective_user.id
    if not is_owner(requesting_user):
        update.message.reply_text("Access denied. Only owners can add new owners.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /addowner <user_id>")
        return
    try:
        new_owner_id = int(context.args[0])
        add_admin(new_owner_id, role='owner')
        update.message.reply_text(f"User {new_owner_id} has been added as an owner.")
    except ValueError:
        update.message.reply_text("User ID must be a number.")

def admin_users_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    page = 1
    data = query.data
    if data.startswith("userlist_page_"):
        try:
            page = int(data.split("_")[-1])
        except:
            page = 1
    query.edit_message_text(text="User List:", reply_markup=get_user_list_keyboard(page))

def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if data == "verify":
        verify_callback(update, context)
    elif data == "change_lang":
        change_lang_callback(update, context)
    elif data.startswith("set_lang_"):
        set_language_callback(update, context)
    elif data == "menu_help":
        menu_help_callback(update, context)
    elif data.startswith("userlist_page_"):
        admin_users_callback(update, context)
    else:
        query.answer("Command not recognized.")

def message_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if context.user_data.get('awaiting_review'):
        review_text = update.message.text
        add_user_log(user_id, f"Review: {review_text}")
        update.message.reply_text("Thank you for your feedback!",
                                  reply_markup=get_main_menu_keyboard())
        context.user_data['awaiting_review'] = False
    else:
        update.message.reply_text("Command not recognized. Use /help for assistance.")

def claim_key_command(update: Update, context: CallbackContext):
    args = context.args
    user_id = update.effective_user.id
    if not args:
        update.message.reply_text("Usage: /claim <key>")
        return
    key_input = args[0].strip()
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT key, type, points_value, is_claimed FROM keys WHERE key = ?", (key_input,))
    key_data = c.fetchone()
    if key_data:
        if key_data[3] == 1:
            update.message.reply_text("This key has already been claimed.")
        else:
            c.execute("UPDATE keys SET is_claimed = 1 WHERE key = ?", (key_input,))
            c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (key_data[2], user_id))
            conn.commit()
            update.message.reply_text(f"Key claimed! You received {key_data[2]} points.")
            add_user_log(user_id, f"Claimed key {key_input} for {key_data[2]} points")
    else:
        update.message.reply_text("Invalid key.")
    conn.close()

# ---------------------------
# Inline Keyboard Builders
# ---------------------------
def get_verification_keyboard():
    keyboard = []
    row = []
    for channel in REQUIRED_CHANNELS:
        btn = InlineKeyboardButton(text=channel, url=f"https://t.me/{channel.strip('@')}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="Verify", callback_data="verify"),
        InlineKeyboardButton(text="Change Language", callback_data="change_lang")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    # Only English is used
    languages = ['en']
    keyboard = []
    row = []
    for lang in languages:
        row.append(InlineKeyboardButton(text=lang.upper(), callback_data=f"set_lang_{lang}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="Rewards", callback_data="menu_rewards"),
            InlineKeyboardButton(text="Account Info", callback_data="menu_account"),
            InlineKeyboardButton(text="Referral System", callback_data="menu_referral")
        ],
        [
            InlineKeyboardButton(text="Change Language", callback_data="change_lang"),
            InlineKeyboardButton(text="Review/Suggestion", callback_data="menu_review"),
            InlineKeyboardButton(text="Admin Panel", callback_data="menu_admin")
        ],
        [
            InlineKeyboardButton(text="Help", callback_data="menu_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="Add/Remove Platform", callback_data="admin_platform"),
            InlineKeyboardButton(text="Add Stock", callback_data="admin_stock")
        ],
        [
            InlineKeyboardButton(text="Add Channel", callback_data="admin_channel"),
            InlineKeyboardButton(text="Admin Management", callback_data="admin_management")
        ],
        [
            InlineKeyboardButton(text="User Section", callback_data="admin_users"),
            InlineKeyboardButton(text="Key Generator", callback_data="admin_key")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_list_keyboard(page):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    offset = (page - 1) * USERS_PER_PAGE
    c.execute("SELECT user_id, username FROM users LIMIT ? OFFSET ?", (USERS_PER_PAGE, offset))
    users = c.fetchall()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    conn.close()

    keyboard = []
    for u in users:
        keyboard.append([InlineKeyboardButton(text=f"{u[1]} ({u[0]})", callback_data="noop")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="« Prev", callback_data=f"userlist_page_{page-1}"))
    if offset + USERS_PER_PAGE < total:
        nav_buttons.append(InlineKeyboardButton(text="Next »", callback_data=f"userlist_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="Back", callback_data="menu_admin")])
    return InlineKeyboardMarkup(keyboard)

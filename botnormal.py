#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import random
import asyncio
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔐 تنظیمات امن (از Environment)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "8122493225"))

DATA_FILE = "bot_data.json"

data = {
    'user_data': {},
    'message_history': {},
    'admin_messages': {}
}

# 🔧 لاگ
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 📁 مدیریت داده
def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 📊 نوار پیشرفت
def create_progress_bar(percent, length=10):
    filled = int(length * percent / 100)
    return "▅" * filled + "▁" * (length - filled)

# 🎬 انیمیشن
async def send_progress_animation(chat_id, message_id, context):
    for percent in [15, 35, 65, 85, 100]:
        bar = create_progress_bar(percent)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⏳ در حال بررسی پیام...\n\n{bar}\n{percent}%"
            )
        except:
            pass
        await asyncio.sleep(1)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ پیام شما ارسال شد.\n⏱ منتظر پاسخ باشید."
        )
    except:
        pass

# 📨 استخراج پیام
def extract_message_info(update: Update):
    m = update.message
    if m.text:
        return ('text', m.text)
    if m.photo:
        return ('photo', m.photo[-1].file_id)
    if m.voice:
        return ('voice', m.voice.file_id)
    if m.video:
        return ('video', m.video.file_id)
    if m.document:
        return ('document', m.document.file_id)
    return ('unknown', 'پیام ناشناخته')

# 👤 پیام کاربر
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_USER_ID:
        return

    data['user_data'][str(user.id)] = {
        'name': user.full_name,
        'username': user.username
    }

    msg_type, content = extract_message_info(update)

    progress = await update.message.reply_text("⏳ در حال بررسی پیام...")
    asyncio.create_task(send_progress_animation(progress.chat_id, progress.message_id, context))

    sent = await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=f"📩 پیام جدید\n\n👤 {user.full_name}\n🆔 {user.id}\n📝 {content}"
    )

    data['admin_messages'][str(sent.message_id)] = user.id
    save_data()

# 👑 پاسخ ادمین
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return

    if not update.message.reply_to_message:
        return

    reply_id = str(update.message.reply_to_message.message_id)
    if reply_id not in data['admin_messages']:
        await update.message.reply_text("❌ این پیام معتبر نیست")
        return

    user_id = data['admin_messages'][reply_id]
    msg_type, content = extract_message_info(update)

    if msg_type == 'text':
        await context.bot.send_message(chat_id=user_id, text=content)
    else:
        await context.bot.send_message(chat_id=user_id, text="📨 پاسخ پشتیبانی ارسال شد")

    await update.message.reply_text("✅ پاسخ ارسال شد")

# 🚀 شروع
def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN تنظیم نشده")

    load_data()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("سلام 👋 پیام خود را ارسال کنید")))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_USER_ID), handle_admin_message))
    app.add_handler(MessageHandler(~filters.Chat(ADMIN_USER_ID), handle_user_message))

    app.run_polling()

if __name__ == "__main__":
    main()
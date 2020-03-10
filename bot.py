import csv
import io
import logging
from decimal import Decimal
from functools import wraps
from datetime import datetime

import matplotlib.pyplot as plt
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

import matplotlib
matplotlib.use('Agg')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
with open('token.txt') as f:
    TOKEN = f.read().strip()
with open('admin_ids.txt') as f:
    ADMIN_IDS = list(map(str.strip, f.readlines()))

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)

    return wrapped


@restricted
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


@restricted
def analyze_temp(update, context):
    doc = update.message.document
    chat_id = update.effective_chat.id
    if doc.file_name == 'data.csv':
        new_doc = io.BytesIO()
        doc.get_file().download(out=new_doc)
        str_doc = io.StringIO(new_doc.getvalue().decode())

        resp_doc = get_plot(str_doc)
        context.bot.send_document(
            chat_id=chat_id, document=resp_doc, filename='last_temp.png'
        )


def get_plot(file_data):
    file_data.seek(0)
    lines = list(csv.reader(file_data))

    date_time = [datetime.strptime(l[0], '%d.%m.%Y %H:%M:%S') for l in lines]
    temperature = [Decimal(l[1]) for l in lines]
    humidity = [Decimal(l[2]) for l in lines]

    fig, ax = plt.subplots()
    fig.set_figheight(10)
    fig.set_figwidth(20)
    ax.plot(date_time, temperature)
    ax.plot(date_time, humidity)
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    return buf


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.document, analyze_temp)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(start_handler)

updater.start_polling()

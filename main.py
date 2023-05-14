import os
import logging
from telegram_imports import *

from blast import blast_handler
from mastermind import mastermind_handler
from verification import verification_handler
from help import help_handler

# TODO
# Add conversationflow for facilitators
# Linking supabase 
# fix logging
# set reminders for those who never complete


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class The100ClubBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(os.environ.get('TELEGRAM_BOT_TOKEN')).build()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_message = \
"""
Welcome to The 100 Club's Telegram Bot!

The 100 Club is an exclusive mastermind community for founders, supporting founders in their journey. Find out more at https://the100club.io.

This bot is used for the following purposes:
• /verify - Verification of membership
• /mastermind - Confirmation of attendance

Cheers,
Joseph
"""

        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text + '\n\nWe are unable to respond to this... choose an option or report this issue using /help.')

    def run(self):
        start_handler = CommandHandler('start', self.start)
        echo_handler = MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex('^q$')), self.echo)

        self.application.add_handler(start_handler)
        self.application.add_handler(mastermind_handler)
        self.application.add_handler(verification_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(blast_handler)
        self.application.add_handler(echo_handler)
        
        self.application.run_polling()


The100ClubBot().run()




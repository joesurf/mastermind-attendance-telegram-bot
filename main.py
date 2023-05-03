import os
import logging
# import requests
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv


from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters


from database import create_db_connection


# TODO
# Add conversationflow for facilitators
# 



# Initialising credentials 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

host = os.environ.get("DB_HOST")
user = "admin"
password = os.environ.get("DB_PASS") 
database = "teleslack"



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# mastermind flow
ATTENDANCE, CONFIRMATION, AVAILABLE, UNAVAILABLE, UNSURE, QUESTIONNAIRE, COMPLETE, ALL_UNAVAILABLE = range(8)
END = ConversationHandler.END

# help flow
HELP_CONFIRMATION1, HELP_CONFIRMATION2 = range(2)

# verification flow
CHECK_EMAIL = range(1)

from messages import start_message


class The100ClubBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(os.environ.get('TELEGRAM_BOT_TOKEN')).build()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)

    async def mastermind(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        chat_id = update.effective_chat.id 

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text='Please wait while we verify your status...', 
        )

        person = await self.information(chat_id)
        context.user_data['person'] = person

        if person:
            keyboard = [['Confirm attendance']]

            await context.bot.send_message(chat_id=update.effective_chat.id, text='What do you want to do?',
                                        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)) 
            
            return ATTENDANCE
        
        else:

            bot_mastermind_unverified = \
f"""
Hello there, it seems that you haven't been verified. Click any of the options below and oour team will respond shortly.

Please verify before continuing: /verify 
"""
            await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_mastermind_unverified)

            return END

    async def information(self, chat_id):
        person = {
            'contact_info': {
                'email': '',
                'first_name': ''     
            },
            'mastermind_group_id': '',
            'invited': False
        }

        connection = create_db_connection(host, user, password, database)
        cursor = connection.cursor()


        cursor.execute(f'SELECT person_id, mastermind_group_id FROM messaging_member WHERE chat_id="{chat_id}"')
        response = cursor.fetchone()

        if response:
            person_id = response[0]
            mastermind_group_id = response[1]

            cursor.execute(f'SELECT first_name, email FROM auth_user WHERE id="{person_id}"')
            response = cursor.fetchone()

            if response:
                person['contact_info']['first_name'] = response[0]
                person['contact_info']['email'] = response[1]

            person['mastermind_group_id'] = mastermind_group_id

            connection.commit()
            connection.close()

            return person

        else:

            return None


    async def attendance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        person = context.user_data['person']

        connection = create_db_connection(host, user, password, database)
        cursor = connection.cursor()

        if person['invited']:
            other_group = person['mastermind_info']['similar_groups']
            cursor.execute(f'SELECT group_name, session_datetime, session_location, similar_groups FROM messaging_mastermindgroup WHERE group_name="{other_group}"')
            response = cursor.fetchone()            
        else:
            mastermind_group_id = person['mastermind_group_id']
            cursor.execute(f'SELECT group_name, session_datetime, session_location, similar_groups FROM messaging_mastermindgroup WHERE id="{mastermind_group_id}"')
            response = cursor.fetchone()


        if response:
            mastermind_info = {
                'group_name': response[0],
                'date': response[1].strftime('%A, %d %B %Y'),
                'time': response[1].strftime('%I:%M %p') + ' onwards',
                'location': response[2],
                'similar_groups': response[3]
            },

            person['mastermind_info'] = mastermind_info[0] # for some reason this is in a tuple

            bot_mastermind_verified = \
f"""
Hello {person['contact_info']['first_name']}, 

{person['mastermind_info']['group_name']}

Here are the details for your mastermind session:
Date: {person['mastermind_info']['date']}
Time: {person['mastermind_info']['time']}
Location: {person['mastermind_info']['location']}
"""
            
            keyboard = [['Will be there', 'Unavailable', 'Unsure']]

            
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=bot_mastermind_verified, 
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Can you make it?')
            )

            return CONFIRMATION
        
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="There's a techincal issue - the team has been informed and will get back to you shortly.", 
            )

            return END

    async def update_availability(self, status):
        connection = create_db_connection(host, user, password, database)
        cursor = connection.cursor()

        cursor.execute(f'UPDATE ')
        response = cursor.fetchone()   




    async def available(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
        attending_message = \
f"""
Awesome, before you go off, help us complete this questionnaire in preparation for the session.

First, state your challenge / problem in one sentence:
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=attending_message, 
        )

        await self.update_availability(update.message.text)

        return QUESTIONNAIRE

    async def unavailable(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        person = context.user_data['person']

        if person['mastermind_info']['similar_groups'] and not person['invited']:
            person['invited'] = True

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Checking other available dates...", 
            )

            return ATTENDANCE
        
        else:

            return ALL_UNAVAILABLE

    async def unsure(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        
        # TODO choose option: reminder or invitation
        # TODO invited condition

        return END


    async def questionnaire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        person = context.user_data['person']

        mastermind_questionnaire_message = \
    f"""
    Next, share with us some context about this challenge:
    """
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mastermind_questionnaire_message
        )      

        return COMPLETE


    async def complete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mastermind_end_message = \
    f"""
    Got it, will be sharing this with the facilitator for the session. See you there!
    """
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mastermind_end_message
        )

        return END

    async def all_unavailable(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mastermind_unavailable = \
f"""
Unfortunately, we are unable to find other dates. Please keep a lookout for next month's session or request a group change if this issue is recurring.
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=mastermind_unavailable, 
        )   

        return END  

    async def verify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Get identifier from user

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Input your email for verification:",
        )

        return CHECK_EMAIL


    async def check_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        email = update.message.text # TODO do some regex

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Checking email...",
        )

        connection = create_db_connection(host, user, password, database)
        cursor = connection.cursor()

        cursor.execute(f'SELECT first_name, id FROM auth_user WHERE email="{email}"')
        response = cursor.fetchone()

        if response:
            first_name = response[0]
            person_id = response[1]

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"{first_name}, your email has been verified. Feel free to use any of the features in this bot!",
            )

            chat_id = update.effective_chat.id

            cursor.execute(f'UPDATE messaging_member SET chat_id="{chat_id}" WHERE person_id="{person_id}"')
            connection.commit()
            connection.close()

            # TODO do 2FA with phone number
            # TODO allow only one time verification

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"We can't seem to verify your email. Please check with your contact from The 100 Club.",
            )

        return END

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [['Mastermind assistance', 'Technical support', 'Others']]

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text='How can I help you?', 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )

        return HELP_CONFIRMATION1

    async def help_confirmation1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['issue'] = update.message.text

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f'Please input your telegram handle:', 
        )
        return HELP_CONFIRMATION2

    async def help_confirmation2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text='We apologise for the inconvenience. Our team will get back to you shortly.', 
        )

        issue = context.user_data['issue']
        telegram = update.message.text

        await context.bot.send_message(
            chat_id='797737829', 
            text=f"{telegram} has reported an issue: {issue}", 
        )
        return END

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text + '\n\nWe are unable to respond to this... choose an option or report this issue using /help.')

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
        user = update.message.from_user
        logger.info("User %s canceled the conversation.", user.first_name)
        await update.message.reply_text(
            "Something unexpected happened. Report this to The 100 Club team.", reply_markup=ReplyKeyboardRemove()
        )

        return END


    def run(self):

        mastermind_handler = ConversationHandler(
            entry_points=[CommandHandler('mastermind', self.mastermind)],
            states={
                ATTENDANCE: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.attendance)],
                CONFIRMATION: [
                    MessageHandler(
                        filters.Regex("^Will be there$"), 
                        self.available),
                    MessageHandler(
                        filters.Regex("^Unavailable$"),
                        self.unavailable),
                    MessageHandler(
                        filters.Regex("^Unsure$"),
                        self.unsure)
                ],

                QUESTIONNAIRE: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.questionnaire)],
                COMPLETE: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.complete)],
                ALL_UNAVAILABLE: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.all_unavailable)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            allow_reentry=True
        )

        help_handler = ConversationHandler(
            entry_points=[CommandHandler('help', self.help)],
            states={
                HELP_CONFIRMATION1: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.help_confirmation1)],
                HELP_CONFIRMATION2: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.help_confirmation2)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        verification_handler = ConversationHandler(
            entry_points=[CommandHandler('verify', self.verify)],
            states={
                CHECK_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), self.check_email)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        start_handler = CommandHandler('start', self.start)
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo)

        self.application.add_handler(start_handler)
        self.application.add_handler(mastermind_handler)
        self.application.add_handler(verification_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(echo_handler)
        
        self.application.run_polling()


The100ClubBot().run()




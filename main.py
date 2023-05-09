import os
import logging
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv
from simple_colors import black


from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters


from database import read_one_query, read_all_query, execute_query
from messages import start_message


# TODO
# Add conversationflow for facilitators
# Linking supabase 
# fix logging
# set reminders for those who never complete



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
ATTENDANCE, CONFIRMATION, AVAILABLE, UNAVAILABLE, UNSURE, QUESTIONNAIRE, COMPLETE = range(7)
END = ConversationHandler.END

# help flow
HELP_CONFIRMATION1, HELP_CONFIRMATION2 = range(2)

# verification flow
CHECK_EMAIL = range(1)

class The100ClubBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(os.environ.get('TELEGRAM_BOT_TOKEN')).build()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)


    async def information(self, chat_id):
        person = {
            'contact_info': {
                'email': '',
                'first_name': ''     
            },
            'mastermind_group_id': '',
            'invited': False
        }

        response = read_one_query(f'SELECT person_id, mastermind_group_id FROM messaging_member WHERE chat_id="{chat_id}"')

        if response:
            person_id = response[0]
            mastermind_group_id = response[1]

            response = read_one_query(f'SELECT first_name, email FROM auth_user WHERE id="{person_id}"')

            if response:
                person['contact_info']['first_name'] = response[0]
                person['contact_info']['email'] = response[1]

            person['mastermind_group_id'] = mastermind_group_id

            return person

        else:

            return None


    async def attendance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        # verify person
        


        if 'person' not in context.user_data:

            chat_id = update.effective_chat.id 

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text='Please wait while we verify your status...', 
            )

            person = await self.information(chat_id)
            context.user_data['person'] = person

        else:
            person = context.user_data['person']


        if not person:

            bot_mastermind_unverified = \
f"""
Hello there, it seems that you haven't been verified. Click any of the options below and oour team will respond shortly.

Please verify before continuing: /verify 
"""
            await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_mastermind_unverified)

            return END

        # purpose: give attendance options

        person = context.user_data['person']

        if person['invited']:
            other_group = person['mastermind_info']['similar_groups']
            response = read_one_query(f'SELECT group_name, session_datetime, session_location, similar_groups, calendar_link FROM messaging_mastermindgroup WHERE group_name="{other_group}"')
        else:
            mastermind_group_id = person['mastermind_group_id']
            response = read_one_query(f'SELECT group_name, session_datetime, session_location, similar_groups, calendar_link FROM messaging_mastermindgroup WHERE id="{mastermind_group_id}"')


        if response:
            mastermind_info = {
                'group_name': response[0],
                'date': response[1].strftime('%A, %d %B %Y'),
                'time': response[1].strftime('%I:%-M %p') + ' onwards',
                'location': response[2],
                'similar_groups': response[3],
                'calendar_link': response[4],
                'full_date': response[1]
            },

            person['mastermind_info'] = mastermind_info[0] # for some reason this is in a tuple

            bot_mastermind_verified = \
f"""
Hello {person['contact_info']['first_name']}, 

Group: {person['mastermind_info']['group_name']}

Here are the details for your mastermind session:
Date: {person['mastermind_info']['date']}
Time: {person['mastermind_info']['time']}
Location: {person['mastermind_info']['location']}

The details are already in your calendar. Otherwise, click this link: <a href='{person['mastermind_info']['calendar_link']}'>Google Calendar Invite Link</a>

P.s. For members, go for your core group session as much as possible. Indicate your availability as of now - if you're unsure, you may update your availability again in the future by entering /mastermind.

#attendance
"""
            
            keyboard = [['Will be there', 'Unavailable']]

            
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=bot_mastermind_verified, 
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Can you make it?'),
                parse_mode=ParseMode.HTML
            )

            return CONFIRMATION
        
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="There's a techincal issue - the team has been informed and will get back to you shortly.", 
            )

            return END

    async def update_availability(self, status, chat_id, challenge=None, context=None, session_date=None, telegram_context=None):


        response = read_one_query(f'SELECT id FROM messaging_member WHERE chat_id="{chat_id}"')
        person_id = response[0]

        responses = read_all_query(f'SELECT session_date FROM messaging_attendancequestionnaire WHERE person_id="{person_id}"')

        existing_questionnaire_date = None
        update = False

        if responses:
            for response in responses:
                if session_date.month == response[0].month:
                    existing_questionnaire_date = response[0]

        if existing_questionnaire_date:    
            update = True    
            execute_query(f'UPDATE messaging_attendancequestionnaire SET session_status="{status}", challenge="{challenge}", context="{context}", session_date="{session_date.date()}" WHERE person_id="{person_id}" AND session_date="{existing_questionnaire_date}"')

        else:
            execute_query(f'INSERT INTO messaging_attendancequestionnaire (session_status, challenge, context, session_date, person_id) VALUES ("{status}", "{challenge}", "{context}", "{session_date}", "{person_id}")')
    
        person = telegram_context.user_data['person']
        group_name = person['mastermind_info']['group_name']

        await telegram_context.bot.send_message(
            chat_id='797737829', 
            text=f"""
{person['contact_info']['first_name']} just checked in.

Status: {status}
Challenge: {challenge}
Context: {context}

#attendance #{group_name} #{'update' if update else 'new'}
            """, 
        )

    async def available(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
        attending_message = \
f"""
Awesome, before you go off, help us complete this questionnaire in preparation for the session.

First, state your challenge / problem in one sentence:

_E.g. I'm facing difficulty using email marketing to target my audience_
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=attending_message,
            parse_mode=ParseMode.MARKDOWN 
        )

        # TODO initial update of availability

        person = context.user_data['person']

        questionnaire = {
            'challenge': '',
            'context': '',
            'session_date': person['mastermind_info']['full_date'],
            'session_status': 'WBT'
        }

        person['questionnaire'] = questionnaire
        context.user_data['person'] = person

        return QUESTIONNAIRE

    async def unavailable(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        person = context.user_data['person']

        await self.update_availability(
            'UNA', 
            update.effective_chat.id,
            session_date=context.user_data['person']['mastermind_info']['full_date'], 
            telegram_context=context
        )

        if person['mastermind_info']['similar_groups'] and not person['invited']:
            person['invited'] = True

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Checking other available dates...", 
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Before that, let us know why you can't make it for your core group session so we can plan better:", 
            )

            return ATTENDANCE
        
        else:

            mastermind_unavailable = \
f"""
Unfortunately, we are unable to find other dates. Please keep a lookout for next month's session or request a group change if this issue is recurring.
"""

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=mastermind_unavailable, 
            )   

            return END  

    async def unsure(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        
        # TODO choose option: reminder or invitation
        # TODO invited condition

        return END


    async def questionnaire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['person']['questionnaire']['challenge'] = update.message.text

        mastermind_questionnaire_message = \
f"""
Next, share with us some context about this challenge:

_E.g. I have tried other forms of marketing to raise awareness of my product with the goal of converting sales but all have failed. Recently I tried email due to suggestions from others but I'm not sure how to work it best_
"""
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mastermind_questionnaire_message,
            parse_mode=ParseMode.MARKDOWN 
        )      

        return COMPLETE


    async def complete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mastermind_end_message = \
f"""
Got it, will be sharing this with the facilitator for the session. See you there!
"""
        
        context.user_data['person']['questionnaire']['context'] = update.message.text        
        
        await self.update_availability(
            'WBT', 
            update.effective_chat.id, 
            session_date=context.user_data['person']['mastermind_info']['full_date'], 
            challenge=context.user_data['person']['questionnaire']['challenge'], 
            context=context.user_data['person']['questionnaire']['context'],
            telegram_context=context)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mastermind_end_message
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

        response = read_one_query(f'SELECT first_name, id FROM auth_user WHERE email="{email}"')

        if response:
            first_name = response[0]
            person_id = response[1]

            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"{first_name}, your email has been verified. Feel free to use any of the features in this bot! \n\n/mastermind",
            )

            chat_id = update.effective_chat.id

            execute_query(f'UPDATE messaging_member SET chat_id="{chat_id}" WHERE person_id="{person_id}"')

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
            entry_points=[CommandHandler('mastermind', self.attendance)],
            states={
                ATTENDANCE: [MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^q$")), self.attendance)],
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
        echo_handler = MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex('^q$')), self.echo)

        self.application.add_handler(start_handler)
        self.application.add_handler(mastermind_handler)
        self.application.add_handler(verification_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(echo_handler)
        
        self.application.run_polling()


The100ClubBot().run()




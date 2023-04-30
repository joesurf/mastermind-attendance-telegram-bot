import os
import logging
# import requests
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv


from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters


from database import create_db_connection



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



ATTENDANCE, INVITATION, QUESTIONNAIRE, COMPLETE = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_introduction = \
"""
Welcome to The 100 Club's Telegram Bot!

The 100 Club is an exclusive mastermind community for founders, supporting founders in their journey. Find out more at https://the100club.io.

This bot is used for the following purposes:
• /verify - Verification of membership
• /mastermind - Confirmation of attendance

Cheers,
Joseph
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_introduction)

async def mastermind(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Please wait while we retrieve your information...", 
    )

    chat_id = update.effective_chat.id 
    verified = False

    person = {
        'contact_info': {
            'email': '',
            'first_name': ''     
        },
        'mastermind_info': {
            'group_name': '',
            'date': 'Tuesday, 9th May 2023',
            'time': '7.30pm - 9.30pm',
            'location': 'Klatch @ Jalan Besar'
        }
    }

    connection = create_db_connection(host, user, password, database)
    cursor = connection.cursor()

    cursor.execute(f'SELECT person_id, mastermind_group_id FROM messaging_member WHERE chat_id="{chat_id}"')
    response = cursor.fetchone()

    if response:
        verified = True
        person_id = response[0]
        mastermind_group_id = response[1]

        cursor.execute(f'SELECT first_name, email FROM auth_user WHERE id="{person_id}"')
        response = cursor.fetchone()

        if response:
            person['contact_info']['first_name'] = response[0]
            person['contact_info']['email'] = response[1]

        cursor.execute(f'SELECT group_name FROM messaging_mastermindgroup WHERE id="{mastermind_group_id}"')
        response = cursor.fetchone()

        if response:
            person['mastermind_info']['group_name'] = response[0]

    connection.commit()
    connection.close()

    if verified:
        bot_mastermind_verified = \
f"""
Hello {person['contact_info']['first_name']}, 

{person['mastermind_info']['group_name']}

Here are the details for your mastermind session:
Date: {person['mastermind_info']['date']}
Time: {person['mastermind_info']['time']}
Location: {person['mastermind_info']['location']}
"""
        
        keyboard = [['Will be there', 'Unavailable or unsure']]

        context.user_data['person'] = person
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=bot_mastermind_verified, 
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Can you make it?')
        )

        return ATTENDANCE
    
    bot_mastermind_unverified = \
    f"""
    Hello there, it seems that you haven't been verified. If there is a technical problem, click this and the team will respond shortly.
    """

    keyboard = [['Mastermind assistance', 'Technical support']]

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=bot_mastermind_unverified, 
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Share with us')
    )

    return ConversationHandler.END


async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # TODO only allowed if member has been verified
    
    attending = update.message.text
    person = context.user_data['person']
    group_name = person['mastermind_info']['group_name']

    if attending == 'Will be there':

        attending_message = \
f"""
Awesome, before you go off, help us complete this questionnaire in preparation for the session.

First, state your challenge / problem in one sentence:
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=attending_message, 
        )

        # TODO update availability in database

        return QUESTIONNAIRE

    elif attending == 'Unavailable or unsure':

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Checking other available dates...", 
        )

        connection = create_db_connection(host, user, password, database)
        cursor = connection.cursor()

        cursor.execute(f'SELECT similar_groups FROM messaging_mastermindgroup WHERE group_name="{group_name}"')
        response = cursor.fetchone()

        if response:
            other_groups = response[0]

            # cursor.execute(f'SELECT date, time, location FROM messaging_mastermindgroup WHERE group_name="{other_groups}"')
            # response = cursor.fetchone()

            if response: 

                # TODO update from response
                mastermind_info = {
                    'group_name': other_groups,
                    'date': 'Test',
                    'time': 'Test',
                    'location': 'test'
                }

                person['mastermind_info'] = mastermind_info

                bot_mastermind_other_group = \
f"""
Here's any group's session we think 

{person['mastermind_info']['group_name']}

Here are the details for your mastermind session:
Date: {person['mastermind_info']['date']}
Time: {person['mastermind_info']['time']}
Location: {person['mastermind_info']['location']}
"""

                keyboard = [['Will be there', 'Unavailable or unsure']]

                await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=bot_mastermind_other_group, 
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, input_field_placeholder='Can you make it?')
                )

                return INVITATION


        mastermind_unavailable = \
f"""
Unfortunately, we are unable to find other dates. Please keep a lookout for next month's session or request a group change if this issue is recurring.
"""

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mastermind_unavailable
        )


        return ConversationHandler.END
    
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Option not available"
        )   

        return ConversationHandler.END


async def invitation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    person = context.user_data['person']
    print(person)
    pass
    # TODO message if can make it

    # TODO update invited column 

    # TODO add option to be reminded

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Invitation"
    )      

    return ConversationHandler.END


async def questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mastermind_end_message = \
f"""
See you there!
"""
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=mastermind_end_message
    )

    return ConversationHandler.END


CHECK_EMAIL = range(1)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get identifier from user

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Input your email for verification:",
    )

    return CHECK_EMAIL


async def check_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Something unexpected happened. Report this to The 100 Club team.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.environ.get('TELEGRAM_BOT_TOKEN')).build()

    mastermind_handler = ConversationHandler(
        entry_points=[CommandHandler('mastermind', mastermind)],
        states={
            ATTENDANCE: [MessageHandler(filters.TEXT & (~filters.COMMAND), attendance)],
            INVITATION: [MessageHandler(filters.TEXT & (~filters.COMMAND), invitation)],
            QUESTIONNAIRE: [MessageHandler(filters.TEXT & (~filters.COMMAND), questionnaire)],
            COMPLETE: [MessageHandler(filters.TEXT & (~filters.COMMAND), complete)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    verification_handler = ConversationHandler(
        entry_points=[CommandHandler('verify', verify)],
        states={
            CHECK_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), check_email)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    # add unknown text or command handler

    application.add_handler(start_handler)
    application.add_handler(mastermind_handler)
    application.add_handler(verification_handler)
    application.add_handler(echo_handler)
    
    application.run_polling()



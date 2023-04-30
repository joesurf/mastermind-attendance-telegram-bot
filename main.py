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



ATTENDANCE, INVITATION = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_introduction = \
"""
Welcome to The 100 Club's Telegram Bot!

This bot is used for the following purposes:
• /verify - Verification of membership
• /mastermind - Confirmation of attendance

The 100 Club is an exclusive mastermind community for founders, supporting founders in their journey. Find out more at https://the100club.io.

Cheers,
Joseph
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_introduction)

async def mastermind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id 

    contact_info = {
        'email': '',
        'first_name': ''     
    }

    mastermind_info = {
        'group_name': '',
        'date': 'Tuesday, 9th May 2023',
        'time': '7.30pm - 9.30pm',
        'location': 'Klatch @ Jalan Besar'
    }

    connection = create_db_connection(host, user, password, database)
    cursor = connection.cursor()

    cursor.execute(f'SELECT person_id, mastermind_group_id FROM messaging_member WHERE chat_id="{chat_id}"')
    response = cursor.fetchone()

    if response:
        print(1)

        person_id = response[0]
        mastermind_group_id = response[1]

        cursor.execute(f'SELECT first_name, last_name, email FROM auth_user WHERE id="{person_id}"')
        response = cursor.fetchone()

        if response:
            print(2)
            print(response)

            contact_info['first_name'] = response[0]
            contact_info['email'] = response[2]



        cursor.execute(f'SELECT group_name FROM messaging_mastermindgroup WHERE id="{mastermind_group_id}"')
        response = cursor.fetchone()

        if response:
            print(3)
            print(response)

            mastermind_info['group_name'] = response[0]

    connection.commit()
    connection.close()

    print(contact_info)
    print(mastermind_info)

    if True:
        # TODO from user_info



        # TODO from mastermind table through mastermind_group -> find details of own + help get invitation


        bot_mastermind_verified = \
f"""
Hello {contact_info['first_name']}, 

{mastermind_info['group_name']}

Here are the details for your mastermind session:
Date: {mastermind_info['date']}
Time: {mastermind_info['time']}
Location: {mastermind_info['location']}
"""
        
        keyboard = [['Coming', 'Unavailable', 'Unsure']]
        
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
    attending = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=attending, 
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat_id, text="Please verify your mobile number in the following format: 91234567")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(os.environ.get('TELEGRAM_BOT_TOKEN')).build()

    mastermind_handler = ConversationHandler(
        entry_points=[CommandHandler('mastermind', mastermind)],
        states={
            ATTENDANCE: [MessageHandler(filters.Regex("^(Coming|Unavailable|Unsure)"), attendance)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(mastermind_handler)
    
    application.run_polling()




# # Enable logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)


# DONE, CHECKING_CHOICE, LEAVE = range(3)



# def start(update: Update, context: CallbackContext):
#     """
#     """
#     update.message.reply_text(
#         "Welcome to The 100 Club Bot! Please type your email to verify your membership to The100Club.",
#         reply_markup=reply_markup, 
#     )
    
#     return CHECKING_CHOICE


# def leave(update: Update, context: CallbackContext):
#     """
#     """
#     # Remove chat_id and replace with ex- to indicate
#     chat_id = update.message.chat_id

#     print("checking status")

#     update.message.reply_text(
#         "We're sorry to see you leave. Please let us know how we can serve you better.",
#         # reply_markup=markup, 
#     )

#     return ConversationHandler.END


# def checking_choice(update: Update, context: CallbackContext) -> int:
#     """
#     """
#     # Get identifier from user

#     update.message.reply_text(
#         "Checking email...",
#     )

#     identifier = update.message['text']
#     chat_id = update.message.chat_id

#     update.message.reply_text(
#         "Oh no, there's a problem with this email. Please try again or contact @joesurfrk for assistance.",
#     )

#     return CHECKING_CHOICE


# def done(update: Update, context: CallbackContext) -> int:
#     """
#     End the conversation
#     """
#     return ConversationHandler.END


# def help(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         """
#         Contact @joesurfrk for assistance
#         """
#     ) 


# def unknown_text(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         "Oops, our bot doesn't understand what '%s' means" % update.message.text)


# def unknown(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         "Oops '%s' is not a valid command" % update.message.text)


# def main() -> None:
#     """
#     Run the telegram bot.
#     """

#     updater = Updater(
#         os.environ.get('TELEGRAM_BOT_TOKEN'),
#         use_context=True
#     )

#     # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={
#             CHECKING_CHOICE: [
#                 MessageHandler(
#                     filters.Filters.regex(
#                         "([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"), checking_choice
#                 ),
#                 # MessageHandler(
#                 #     filters.Filters.text & ~(filters.Filters.command | filters.Filters.regex("^Done$")), checking_choice
#                 # )
#             ],
#         },
#         fallbacks=[MessageHandler(filters.Filters.regex("^Done$"), done)],
#     )

#     updater.dispatcher.add_handler(conv_handler)
#     updater.dispatcher.add_handler(CommandHandler('start', start))
#     updater.dispatcher.add_handler(CommandHandler('help', help))
#     updater.dispatcher.add_handler(CommandHandler('leave', leave))

#     # Filters out unknown commands
#     updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))
#     # Filters out unknown messages.
#     updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))

#     # Run the bot until the user presses Ctrl-C
#     updater.start_polling()
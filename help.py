from telegram_imports import *
from unknown import cancel


# help flow
HELP_CONFIRMATION1, HELP_CONFIRMATION2 = range(2)
END = ConversationHandler.END

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Mastermind assistance', 'Technical support', 'Others']]

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text='How can I help you?', 
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

    return HELP_CONFIRMATION1

async def help_confirmation1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['issue'] = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f'Please input your telegram handle:', 
    )
    return HELP_CONFIRMATION2

async def help_confirmation2(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

help_handler = ConversationHandler(
    entry_points=[CommandHandler('help', help)],
    states={
        HELP_CONFIRMATION1: [MessageHandler(filters.TEXT & (~filters.COMMAND), help_confirmation1)],
        HELP_CONFIRMATION2: [MessageHandler(filters.TEXT & (~filters.COMMAND), help_confirmation2)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
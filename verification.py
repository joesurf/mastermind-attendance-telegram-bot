from telegram_imports import *
from supabase_db import supabase
from unknown import cancel


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

    response = supabase.table('profiles').select("firstName").eq("email", email).execute()

    if response.data:
        first_name = response.data[0]['firstName']

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"{first_name}, your email has been verified. Your access is updated. Check out the following features: \n/mastermind: for mastermind registration",
        )

        chat_id = update.effective_chat.id

        try:
            response = supabase.table('profiles').update({"telegram_bot_id": chat_id}).eq("email", email).execute()

            await context.bot.send_message(
                chat_id='797737829', 
                text=f"{first_name} has just been verified by the Telegram Bot. \n\n#verification",
            )

        except Exception as e:

            await context.bot.send_message(
                chat_id='797737829', 
                text=f"{first_name} has failed to be verified by the Telegram Bot. \n\n#verification",
            )

        # TODO do 2FA with phone number
        # TODO allow only one time verification

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"We can't seem to verify your email. Please check with your contact from The 100 Club.\n\nClick or type /verify to start again.",
        )

    return ConversationHandler.END



verification_handler = ConversationHandler(
    entry_points=[CommandHandler('verify', verify)],
    states={
        CHECK_EMAIL: [MessageHandler(filters.TEXT & (~filters.COMMAND), check_email)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
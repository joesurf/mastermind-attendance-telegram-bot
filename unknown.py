from telegram_imports import *


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    user = update.message.from_user
    # logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Something unexpected happened. Report this to The 100 Club team.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
import os
from telegram import (
    Update,
    ReplyKeyboardRemove,
    MessageEntity,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from datetime import datetime
import json

from dify_tm_chat_once import chat_once  # Import the chat_once function

# ex original
# usage: s_p = {'format': 'ex original', 'memory_context': None, 'topic': None}; text = file_transcription; chat_once(s_p, text)
# will return the fixed text with original format
# or refine: s_p = {'format': 'ex refine', 'memory_context': None, 'topic': None}; text = file_transcription; chat_once(s_p, text)

# from audio_whisper import transcribe_audio  # Import the transcribe_audio function
from audio_whisper_openai_api import (
    transcribe_audio,
    reload_txt,
)  # Import the transcribe_audio function, but process the audio not locally but through OpenAI API

USER_DIRECTORY = "user_data"


def save_data(user_id, message_id, data):
    json_path = os.path.join(USER_DIRECTORY, f"{user_id}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            full_data = json.load(file)
    else:
        full_data = {}

    full_data[message_id] = data

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(full_data, file, ensure_ascii=False, indent=4)


def load_or_create_data(user_id):
    json_path = os.path.join(USER_DIRECTORY, f"{user_id}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        return {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Send me an audio file or a voice message, and I will transcribe it for you."
    )


async def save_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    # id
    user_id = update.message.from_user.id
    audio_message_id = update.message.message_id
    # folder
    user_folder = os.path.join(USER_DIRECTORY, str(user_id))
    audio_folder = os.path.join(user_folder, "audio_files")
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Handle audio files
    if update.message.audio:
        audio_file = update.message.audio
        file_type = "audio"
        file_id = audio_file.file_id
        file_extension = (
            os.path.splitext(audio_file.file_name)[1]
            if audio_file.file_name
            else "_unknown.mp3"
        )
        file_name = (
            audio_file.file_name
            if audio_file.file_name
            else f"{file_id}{file_extension}"
        )

    # Handle voice messages
    elif update.message.voice:
        audio_file = update.message.voice
        file_type = "voice"
        file_id = audio_file.file_id
        file_extension = ".mp3"
        timestamp = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
        file_name = f"{timestamp}{file_extension}"
    else:
        await update.message.reply_text("Please send an audio file or a voice message.")
        return

    audio_file = await audio_file.get_file()
    audio_file_path = os.path.join(audio_folder, file_name)
    await audio_file.download_to_drive(audio_file_path)

    info_message = await update.message.reply_text(
        "Processing your audio...", reply_to_message_id=audio_message_id
    )
    info_message_id = info_message.message_id

    # time.sleep(6) # salute
    # Call the transcribe_audio function and get the path to the TXT file
    txt_file_path = transcribe_audio(audio_file_path)

    if txt_file_path:
        with open(txt_file_path, "r", encoding="utf-8") as txt_file:
            transcription = txt_file.read()
            if transcription == "":
                transcription = "Sorry, No content found in the audio file."
                with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                    transcription = "Sorry, No content found in the audio file."

        edit_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Edit: Reply this with your new text",
                        callback_data=f"edit_{user_id}_pass",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "AI Fix", callback_data=f"fix_{user_id}_{info_message_id}"
                    ),
                    InlineKeyboardButton(
                        "Refine", callback_data=f"refine_{user_id}_{info_message_id}"
                    ),
                ],
            ]
        )
        await info_message.edit_text(transcription, reply_markup=edit_button)
        user_data = {
            "audio": audio_file_path,
            "txt_file_path": txt_file_path,
        }
        save_data(user_id, info_message_id, user_data)
    else:
        await info_message.edit_text("Failed to transcribe audio.")


async def update_transcription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:

    info_message_id = str(update.message.reply_to_message.message_id)

    user_id = update.message.chat.id
    user_data = load_or_create_data(user_id)

    if info_message_id in user_data:
        data = user_data[info_message_id]
        new_transcription = update.message.text
        txt_file_path = data["txt_file_path"]

        try:
            with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(new_transcription)
            with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                file_transcription = txt_file.read()  # Ensure it is what it is

            # Update the message with the new transcription
            edit_button = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Edit: Reply this with your new text",
                            callback_data=f"edit_{user_id}_pass",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "AI Fix", callback_data=f"fix_{user_id}_{info_message_id}"
                        ),
                        InlineKeyboardButton(
                            "Refine",
                            callback_data=f"refine_{user_id}_{info_message_id}",
                        ),
                        InlineKeyboardButton(
                            "Reset", callback_data=f"reset_{user_id}_{info_message_id}"
                        ),
                    ],
                ]
            )
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=info_message_id,
                text=file_transcription,
                reply_markup=edit_button,
            )
            # Clear the user message
            await update.message.delete()
        except Exception as e:
            await update.message.reply_text(f"Error updating transcription: {str(e)}")
    else:
        await update.message.reply_text(
            f"No transcription associated with this message."
        )

    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # send message to show we are processing
    temp_message = await query.message.reply_text("Processing...")
    # split the query.data to get the action and user_id and the message_id
    action, user_id, info_message_id = query.data.split("_")
    user_id = int(user_id)
    user_data = load_or_create_data(user_id)
    data = user_data[info_message_id]
    txt_file_path = data["txt_file_path"]
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        file_transcription = txt_file.read()

    if action == "edit":
        pass

    # Use dify fix
    elif action == "fix":
        setted_parameters = {
            "format": "ex original",
            "memory_context": None,
            "topic": None,
        }
        # print(f"\n\nDebugging: \n {setted_parameters}\n{file_transcription}\n")
        response = chat_once(setted_parameters, file_transcription)
        # print(f"Debugging_2: \n {response}\n-----------------")
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(response)

    # Use dify refine
    elif action == "refine":
        setted_parameters = {
            "format": "ex refine",
            "memory_context": None,
            "topic": None,
        }
        # print(f"\n\nDebugging: \n {setted_parameters}\n{file_transcription}\n")
        response = chat_once(setted_parameters, file_transcription)
        # print(f"Debugging_2: \n {response}\n-----------------")
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(response)

    elif action == "reset":
        await query.message.reply_text(
            f"Note: This is the last copy,\ndelete or save it with caution.\n\n{file_transcription}\n"
        )
        reload_txt(data["audio"])

    # Something went wrong
    else:
        await query.edit_message_text("Invalid action")

    # Load the transcription stored
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        file_transcription = txt_file.read()

    # The edit button
    edit_button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Edit: Reply this with your new text",
                    callback_data=f"edit_{user_id}_pass",
                )
            ],
            [
                InlineKeyboardButton(
                    "AI Fix", callback_data=f"fix_{user_id}_{info_message_id}"
                ),
                InlineKeyboardButton(
                    "Refine", callback_data=f"refine_{user_id}_{info_message_id}"
                ),
                InlineKeyboardButton(
                    "Reset", callback_data=f"reset_{user_id}_{info_message_id}"
                ),
            ],
        ]
    )

    # Update the message with the new transcription
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=info_message_id,
        text=file_transcription,
        reply_markup=edit_button,
    )
    # Tell user we done by edit temp_message, then delete
    await temp_message.edit_text(f"Done!")
    await temp_message.delete()


def main() -> None:
    tg_token = ""  # Your Telegram Bot Token
    application = Application.builder().token(tg_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, save_audio))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, update_transcription)
    )
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()


if __name__ == "__main__":
    main()

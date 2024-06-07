import os
import json
from datetime import datetime

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

from dify_tm_chat_once import chat_once
from audio_whisper_openai_api import transcribe_audio_whisper_api
from audio_deepgram import transcribe_audio_deepgram
from the_notebook_tools import reload_txt, pure_text

USER_DIRECTORY = "user_data"


def save_data(user_id, message_id, data):
    if not os.path.exists(USER_DIRECTORY):
        os.makedirs(USER_DIRECTORY)  # Ensure the root directory exists

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
        f"Welcome!\nSend me an audio file or a voice message, and I will transcribe it for you.\nYou can send me plain text - you got the transcription from some where else. Reply to the transcription message to edit it.\nUse /set to change the STT provider.\nUse /notes to add notes."
    )
    # let'r preset the user with deepgram
    user_id = update.message.from_user.id
    load_or_create_data(user_id)
    user_setting = {"STT": "deepgram", "prompt": "Default"}
    save_data(user_id, "user_setting", user_setting)


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

    elif update.message.text:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
        file_name = f"plain{timestamp}.txt"
        txt_file_path = os.path.join(audio_folder, file_name)
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(update.message.text)
        await update.message.reply_text(
            "Text saved, you can reply this message to edit it.\nDelete your message for better looking."
        )
        return
    else:
        await update.message.reply_text("Error message type.")
        return

    audio_file = await audio_file.get_file()
    audio_url = audio_file.file_path  # Faster than download then upload
    audio_file_path = os.path.join(audio_folder, file_name)
    await audio_file.download_to_drive(audio_file_path)

    info_message = await update.message.reply_text(
        "Processing your audio...", reply_to_message_id=audio_message_id
    )
    info_message_id = info_message.message_id

    # load the user setting for what STT to use
    user_setting = load_or_create_data(user_id)["user_setting"]
    if "STT" in user_setting:
        STT = user_setting["STT"]
    else:
        STT = "deepgram"
    if STT == "deepgram":
        txt_file_path = transcribe_audio_deepgram(audio_file_path, audio_url)
    elif STT == "openai":
        txt_file_path = transcribe_audio_whisper_api(audio_file_path)

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
                        callback_data=f"edit_{user_id}_{info_message_id}",
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
                        "Pure Text", callback_data=f"pure_{user_id}_{info_message_id}"
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

        # Leave history after excuting the command
        with open(txt_file_path, "r", encoding="utf-8") as txt_file:
            old = txt_file.read()
        final_copy = await update.message.reply_text(
            f"Note: This is the last copy,\ndelete or save it with caution."
        )
        final_id = final_copy.message_id
        delete_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Delete", callback_data=f"delete_{user_id}_{final_id}"
                    )
                ],
            ]
        )
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=info_message_id,
            text=f"Note: This is the last copy,\ndelete or save it with caution.\n\n{old}\n",
            reply_markup=delete_button,
        )

        # Overwrite the transcription, and print the new one
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
                            "Reply this message with your new transcription",
                            callback_data=f"edit_{user_id}_{info_message_id}",
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
                        InlineKeyboardButton(
                            "Pure Text",
                            callback_data=f"pure_{user_id}_{info_message_id}",
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

            # Clear the user's message for better looking
            await update.message.delete()
        except Exception as e:
            await update.message.reply_text(f"Error updating transcription: {str(e)}")
    else:
        await update.message.reply_text(
            f"No transcription associated with this message."
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # send message to show we are processing
    temp_message = await query.message.reply_text("Processing...")

    # split the query.data to get the action and user_id and the message_id
    action, user_id, info_message_id = query.data.split("_")
    user_id = int(user_id)
    user_data = load_or_create_data(user_id)
    try:
        data = user_data[info_message_id]
    except KeyError:
        if action == "delete":
            # nothing wrong, just continue
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=int(info_message_id)
            )
            await temp_message.delete()
            return

    txt_file_path = data["txt_file_path"]

    # load prompt for the user
    user_setting = load_or_create_data(user_id)["user_setting"]
    if "prompt" in user_setting:
        prompt = user_setting["prompt"]
    else:
        prompt = None
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        file_transcription = txt_file.read()

    # Leave history after excuting the command

    if action != "edit":
        final_copy = await query.message.reply_text(
            f"Note: This is the last copy,\ndelete or save it with caution."
        )
        final_id = final_copy.message_id
        delete_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Delete", callback_data=f"delete_{user_id}_{final_id}"
                    )
                ],
            ]
        )
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=final_id,
            text=f"Note: This is the last copy,\ndelete or save it with caution.\n\n{file_transcription}\n",
            reply_markup=delete_button,
        )

    # Main actions
    if action == "edit":
        # delete the temp_message then exit this function
        await temp_message.delete()
        return

    # Use dify fix
    elif action == "fix":
        setted_parameters = {
            "format": "ex original",
            "memory_context": prompt,
            "topic": None,
        }
        response = chat_once(setted_parameters, file_transcription)
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(response)

    # Use dify refine
    elif action == "refine":
        setted_parameters = {
            "format": "ex refine",
            "memory_context": prompt,
            "topic": None,
        }
        response = chat_once(setted_parameters, file_transcription)
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(response)

    # Restore the original transcription
    elif action == "reset":
        reload_txt(data["txt_file_path"])

    # Remove the timestamp
    elif action == "pure":
        pure_text(data["txt_file_path"])

    # In case something went wrong
    else:
        await query.edit_message_text("Invalid action")

    # Load the transcription stored
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        new_file_transcription = txt_file.read()

    # The edit button
    edit_button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Reply this message with your new transcription",
                    callback_data=f"edit_{user_id}_{info_message_id}",
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
                InlineKeyboardButton(
                    "Pure Text", callback_data=f"pure_{user_id}_{info_message_id}"
                ),
            ],
        ]
    )

    # Update the message with the new transcription
    if new_file_transcription != file_transcription:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=info_message_id,
            text=new_file_transcription,
            reply_markup=edit_button,
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=final_id,
            text=f"No changes made.",
            reply_markup=delete_button,
        )
    # Tell user we done by edit temp_message, then delete
    await temp_message.edit_text(f"Done!")
    await temp_message.delete()


async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    setting_message = await update.message.reply_text("Loading...")
    message_id = setting_message.message_id
    setting_button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Model", callback_data=f"settings_STT_init_{message_id}"
                ),
                InlineKeyboardButton(
                    "View Notes (Prompt)",
                    callback_data=f"settings_prompt_show_{message_id}",
                ),
            ]
        ]
    )
    # update the setting_message with more details
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=f'Setting:\n\nModel: Change Transcription Service Provider\nNotes(Prompt): Add or edit notes, so that AI will know you better and may perform better output for the "AI fix" or "Refine" job.\nClick button to view current notes.\nOr /notes to add or overwrite notes.\nExample: /notes I am a programeer, My friend named Jack appear more than Mike.',
        reply_markup=setting_button,
    )
    # delete the user message for better looking
    await update.message.delete()


async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_data = load_or_create_data(user_id)
    user_setting = user_data["user_setting"]
    old = user_setting["prompt"]

    # Leave something after excuting the command
    final_copy = await update.message.reply_text(
        f"Note: This is the last copy,\ndelete or save it with caution."
    )
    final_id = final_copy.message_id
    delete_button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Delete", callback_data=f"delete_{user_id}_{final_id}"
                )
            ],
        ]
    )
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=final_id,
        text=f"Note: This is the last copy,\ndelete or save it with caution.\n\n{old}\n",
        reply_markup=delete_button,
    )

    # remove /notes command at the front
    prompt = update.message.text[7:]
    user_setting["prompt"] = prompt
    save_data(user_id, "user_setting", user_setting)
    # delete the user message for better looking
    await update.message.delete()


async def setting_buttons_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:

    query = update.callback_query
    await query.answer()

    # split the query.data, store to a list
    test = query.data.split("_")
    set, action, setting, message_id = query.data.split("_")
    message_id = int(message_id)
    # Load the second level setting_message

    user_id = query.from_user.id
    user_data = load_or_create_data(user_id)
    user_setting = user_data["user_setting"]

    if action == "STT" and setting == "init":
        setting_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Deepgram", callback_data=f"settings_STT_deepgram_{message_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "OpenAI", callback_data=f"settings_STT_openai_{message_id}"
                    )
                ],
            ]
        )
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=f"Select your Transcription Service Provider:\nDeepgram: Better and Faster, but may not good at languages other than English\nOpenAI Whisper: Good at most languages, even mix of duo language like English with Chinese\n",
            reply_markup=setting_button,
        )

    elif action == "STT" and setting == "deepgram":
        user_setting["STT"] = "deepgram"
        save_data(user_id, "user_setting", user_setting)
        # delete the user message and the setting_message by chat_id and message_id
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=message_id
        )
    elif action == "STT" and setting == "openai":
        user_setting["STT"] = "openai"
        save_data(user_id, "user_setting", user_setting)
        # delete
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=message_id
        )

    elif action == "prompt" and setting == "show":
        if "prompt" in user_setting:
            prompt = user_setting["prompt"]
        else:
            prompt = "No notes found, use /notes to add or overwrite notes."
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=f"Notes:\n\n{prompt}",
        )
        return


def main() -> None:
    tg_token = ""  # Your Telegram Bot Token
    application = Application.builder().token(tg_token).build()

    application.add_handler(CommandHandler("start", start))
    # Add the set command handler
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("notes", notes_command))

    application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, save_audio))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, update_transcription)
    )
    # Add the conversation handler, for TEXT, but not reply to anything
    application.add_handler(MessageHandler(filters.TEXT & ~filters.REPLY, save_audio))
    application.add_handler(
        CallbackQueryHandler(
            button_handler, pattern="^(fix|refine|reset|edit|pure|delete)_"
        )
    )
    application.add_handler(
        CallbackQueryHandler(setting_buttons_handler, pattern="^settings_")
    )  # Handle settings buttons
    application.run_polling()


if __name__ == "__main__":
    main()

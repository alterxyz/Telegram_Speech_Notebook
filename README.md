# Telegram Speech-to-Text Bot

A simple Telegram bot that converts voice messages to text using Local or OpenAI-API [Whisper](https://github.com/openai/whisper).

Fix or refine the transcribed text with the Dify.

## Features

- Your audio files are stored locally where the bot is hosted (when using Local Whisper)
- Transcribe voice messages to text, and it is editable!

## Usage

1. Send a voice message or audio file to the bot
2. The bot will reply with the transcribed text

## Requirements

- Python 3.x
- Telegram Bot Token
- Dify API
- OpenAI-API key

## Deployment

1. Clone this repository
2. Install the requirements
3. Set up the environment variables
    1. Put your Telegram Bot Token in `bot.py`
    2. Put your Dify API key in `audio_whisper.py`
        1. Import DSL file from the `STT fix chat` in this repository to your Dify account
        2. Get the API key
        3. If you edit or using something else:
            1. Run the `dify_tm_perpare_cli.py` in this repository
            2. Get the Setted_parameters and any other information with the Dify API Secret key
            3. Edit the `setted_parameters` in the bot.py `button_handler` function
    3. Put your OpenAI-API key in `audio_whisper_openai_api.py`
    4. If you want to process the Speech to Text locally, you need
        1. A GPU with CUDA 12.1
        2. Replace `from audio_whisper_openai_api import` with `from audio_whisper import` in `bot.py`
        3. Install by the following command:

            ```bash
            pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
            pip install -U openai-whisper
            ```

- Run `python3 bot.py` or `python bot.py` (run it with tmux to prevent it from stopping when you close the terminal)

## Notes for OpenAI-API users

- OpenAI said "We do not train on your business data (data from ChatGPT Team, ChatGPT Enterprise, or our API Platform)" at <https://openai.com/enterprise-privacy/>
- But they do store it temporarily: "OpenAI may securely retain API inputs and outputs for up to 30 days to provide the services and to identify abuse"
- Use it at your own risk.

## Future Work

- [x] Add GPT refinement to the transcribed text.

GLHF!

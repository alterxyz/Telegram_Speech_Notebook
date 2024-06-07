# Telegram Speech-to-Text Bot

A simple Telegram bot that converts voice messages to text using Local or OpenAI-API[Whisper](https://github.com/openai/whisper), or Deepgram API.

Fix or refine the transcribed text with the Dify work flow.

## Features

- Your audio files are stored locally where the bot is hosted (when using Local Whisper)
- Transcribe voice messages to text, and it is editable!

## Usage

1. Send a voice message or audio file to the bot
2. The bot will reply with the transcribed text
3. Try those buttons!

## Requirements

- Python 3.x
- Telegram Bot Token
- Dify API for process transcribed text
- Speech-to-Text Service
    - Local Whisper
    - OpenAI API
    - Deepgram API

## Deployment

1. Clone this repository
2. Install the requirements by `pip install -r requirements.txt`
3. Set up the environment variables
    1. Put your Telegram Bot Token in `bot.py`
    2. Put your Dify API key in `audio_whisper.py` [view more detail](doc/deployment.md#dify)
    3. Set up the Speech-to-Text Service and update at `bot.py` [view more detail](doc/deployment.md#speech-to-text-service)

- Run `python3 bot.py` or `python bot.py` (run it with tmux to prevent it from stopping when you close the terminal)

## Future Work

- [x] Add GPT refinement to the transcribed text.

GLHF!

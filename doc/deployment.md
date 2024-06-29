# Additional information about the deployment of the application.

## Dify

The Dify was preset with parameters. You can edit the parameters in the `bot.py` file. The parameters are in the `button_handler` function.

For quick start, try import the DSL file from the `STT fix chat` in this repository to your Dify account.

### How to get the parameters

If you edit or using something else:

1. Run the `dify_tm_perpare_cli.py` in this repository
2. Get the Setted_parameters and any other information with the Dify API Secret key
3. Edit the `setted_parameters` in the bot.py `button_handler` function

## Speech-to-Text Service

### Local Whisper

If you want to process the Speech to Text locally, you need:

1. A GPU with CUDA 12.1 (or you can use CPU, but it will be slow)
    1. You can use CPU, but it will be slow
    2. If modify verison of CUDA, then you also need to change the torch version for pip install
2. Replace `from audio_whisper_openai_api import` with `from audio_whisper import` in `bot.py`
3. Install the dependencies by the following command:

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -U openai-whisper
```

### OpenAI API

- Put your OpenAI-API key in `audio_whisper_openai_api.py` file.
- Install the dependencies by `pip install openai`

Notes for OpenAI-API users:

- OpenAI said "We do not train on your business data (data from ChatGPT Team, ChatGPT Enterprise, or our API Platform)" at <https://openai.com/enterprise-privacy/>
- But they do store it temporarily: "OpenAI may securely retain API inputs and outputs for up to 30 days to provide the services and to identify abuse"
- Use it at your own risk.

### Deepgram API

- Put your Deepgram-API key in `audio_deepgram.py` file.
- Install the dependencies by `pip install deepgram-sdk`

### Groq API

- Put your Groq-API key in `audio_groq.py` file.
- Install the dependencies by `pip install groq`
- Set up your Groq API Key `export GROQ_API_KEY=<your-api-key-here>`
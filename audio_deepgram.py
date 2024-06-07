import json
from deepgram import DeepgramClient, PrerecordedOptions
from the_notebook_tools import save_transcript


DEEPGRAM_API_KEY = ""


def transcribe_audio_deepgram(file_path, URL):
    """
    Transcribe an audio file using Deepgram API and save the result as .json and .txt files.
    Using nova-2 model, detect language, punctuate, utterances, and single channel.

    Args:
        file_path (str): Path(for naming) to the audio file.
        AUDIO_URL (str): URL of the audio file.
    """
    AUDIO_URL = {"url": URL}
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        options = PrerecordedOptions(
            model="nova-2",
            language="en-US",
            punctuate=True,
            utterances=True,
        )
        response = deepgram.listen.prerecorded.v("1").transcribe_url(AUDIO_URL, options)
        # Save it as a json file
        json_file_path = file_path + ".api_deepgram.json"
        try:
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(response.to_dict(), json_file, indent=4)
            txt_file_path = save_transcript(
                file_path, json_file_path, "api_deepgram", "tg"
            )
        except Exception as e:
            print(f"Error: Unable to save .json file: {e}")
    except Exception as e:
        print(f"Exception: {e}")

    return txt_file_path


# example usage

import os
import json
import re


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def reload_txt(file_path):
    # Ensure the input file path is correct for an SRT file
    if not file_path.endswith(".srt"):
        file_path = os.path.splitext(file_path)[0] + ".srt"

    txt_file_path = os.path.splitext(file_path)[0] + ".txt"

    with open(file_path, "r", encoding="utf-8") as srt_file:
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            skip_line = False  # Flag to skip sequence number lines
            for line in srt_file:
                if skip_line:
                    if line.strip():  # Write subtitle text lines
                        txt_file.write(f"{line.strip()}\n")
                    skip_line = False
                elif "-->" in line:
                    start_time, end_time = line.strip().split(" --> ")
                    start_time_str = start_time[3:8]  # Slicing to format start time
                    txt_file.write(f"{start_time_str} ")
                    skip_line = True  # Set flag to skip next line (actual subtitle)
    return txt_file_path


def pure_text(txt_file_path):
    # Read the file and clean lines
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        lines = txt_file.readlines()

    cleaned_lines = [
        re.sub(r"^\d{2}:\d{2} ", "", line.strip()) + "\n" for line in lines
    ]

    # Write the cleaned lines back to the file
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        txt_file.writelines(cleaned_lines)


def save_transcript(file_path, json_file_path, input_logo, logo):
    # load the json file
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        transcript_dict = json.load(json_file)

    # Save the transcription as a modified txt file {}_[].srt
    srt_file_path = os.path.join(
        os.path.dirname(file_path),
        f"{logo}[{os.path.basename(file_path).split('.')[0]}].srt",
    )

    # OpenAI Whisper API
    if input_logo == "api_openai_whisper":

        try:
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                transcript_dict = json.load(json_file)

            srt_file_path = os.path.splitext(file_path)[0] + "_modified.srt"
            with open(srt_file_path, "w", encoding="utf-8") as srt_file:
                for index, segment in enumerate(transcript_dict["segments"]):
                    start_time = format_timestamp(segment["start"])
                    end_time = format_timestamp(segment["end"])
                    srt_file.write(
                        f"{index + 1}\n{start_time} --> {end_time}\n{segment['text']}\n\n"
                    )
        except FileNotFoundError:
            print(f"File not found: {json_file_path}")
            return None
        except json.JSONDecodeError:
            print("Invalid JSON file.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    # Deepgram API
    elif input_logo == "api_deepgram":
        try:
            with open(srt_file_path, "w", encoding="utf-8") as srt_file:
                for index, utterance in enumerate(
                    transcript_dict["results"]["utterances"]
                ):
                    start_time = format_timestamp(utterance["start"])
                    end_time = format_timestamp(utterance["end"])
                    text = utterance["transcript"]
                    srt_file.write(
                        f"{index + 1}\n{start_time} --> {end_time}\n{text}\n\n"
                    )
        except Exception as e:
            print(f"Error: error saving .srt file: {e}")
    txt = reload_txt(srt_file_path)
    return txt

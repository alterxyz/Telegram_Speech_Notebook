# OpenAI said "We do not train on your business data (data from ChatGPT Team, ChatGPT Enterprise, or our API Platform)" at https://openai.com/enterprise-privacy/
# Use it at your own risk.
import json
import openai
import os


# Set your OpenAI API key and base URL
CHATGPT_API_KEY = ""  # YOUR_OPENAI_API_KEY
CHATGPT_BASE_URL = "https://api.openai.com/v1"
client = openai.OpenAI(api_key=CHATGPT_API_KEY, base_url=CHATGPT_BASE_URL, timeout=600)


def transcribe_audio(file_path, language="zh", temperature=0.4):
    """
    Transcribe an audio file using OpenAI API and save the result as .json, .srt, and .txt files.

    Args:
        file_path (str): Path to the audio file.
        language (str, optional): Language of the audio. Default is "zh" (Chinese).
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: 文件 {file_path} 不存在。")
        return

    # Open the audio file
    with open(file_path, "rb") as audio_file:
        try:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                language=language,
                temperature=temperature,
            )
            # print(transcript)
        except Exception as e:
            print(f"Error: 转录音频文件时出错：{e}")
            return

    # Convert the transcript to a dictionary
    transcript_dict = transcript.to_dict()
    print(transcript_dict["text"])

    # Save the raw JSON response
    json_file_path = file_path + ".json"
    if temperature != 0.4:
        json_file_path = file_path + str(temperature) + ".json"
    try:
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(transcript_dict, json_file, indent=4)
    except Exception as e:
        print(f"Error: 无法保存 .json 文件：{e}")

    # Save the transcription as a modified txt file tg_[].txt
    tg_file_path = os.path.join(
        os.path.dirname(file_path),
        "tg_[" + os.path.basename(file_path).split(".")[0] + "]",
    )
    txt_file_path = tg_file_path + ".txt"
    if temperature != 0.4:
        txt_file_path = tg_file_path + str(temperature) + ".txt"
    try:
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            for segment in transcript_dict["segments"]:
                start_time = segment["start"]
                text = segment["text"]

                # 格式化时间，只保留分钟和秒
                start_time_str = format_timestamp(start_time)[3:8]
                txt_file.write(f"{start_time_str} {text}\n")
        # print(f"转录结果已保存为 {txt_file_path}")
    except Exception as e:
        print(f"Error: 无法保存 .txt 文件：{e}")

    # Save the transcription as an SRT file
    srt_file_path = os.path.splitext(file_path)[0] + ".srt"
    try:
        with open(srt_file_path, "w", encoding="utf-8") as srt_file:
            for segment in transcript_dict["segments"]:
                start_time = format_timestamp(segment["start"])
                end_time = format_timestamp(segment["end"])
                text = segment["text"]
                srt_file.write(f"{start_time} --> {end_time}\n{text}\n\n")
        # print(f"转录结果已保存为 {srt_file_path}")
    except Exception as e:
        print(f"Error: 无法保存 .srt 文件：{e}")

    # 输出信息
    return txt_file_path


def format_timestamp(seconds):
    """格式化时间戳为 SRT 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def reload_txt(audio_file_path):
    # load from the srt, write to the tg_[].txt 格式化时间，只保留分钟和秒
    srt_file_path = os.path.splitext(audio_file_path)[0] + ".srt"
    tg_file_path = os.path.join(
        os.path.dirname(audio_file_path),
        "tg_[" + os.path.basename(audio_file_path).split(".")[0] + "]",
    )
    txt_file_path = tg_file_path + ".txt"
    with open(srt_file_path, "r", encoding="utf-8") as srt_file:
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            for line in srt_file:
                if "-->" in line:
                    start_time, end_time = line.strip().split(" --> ")
                    start_time_str = start_time[3:8]
                    txt_file.write(f"{start_time_str} ")
                elif line.strip():
                    txt_file.write(f"{line.strip()}\n")


# Test different temperatures
def test_temperatures():
    file = "2021-06-13T23_11_47.m4a"
    while True:
        temperature = input("Enter temperature: ")
        transcribe_audio(file, temperature=float(temperature))


# test_temperatures()

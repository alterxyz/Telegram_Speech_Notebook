# 获取一个音频文件, 然后返回字幕

import os
import whisper
import whisper.utils


def transcribe_audio(file_path, model_size="medium", device="cuda", language="zh"):
    """
    使用 Whisper 模型转录音频文件，并将结果保存为 .txt 和 .srt 文件。

    Args:
        file_path (str): 音频文件的路径。
        model_size (str, optional): Whisper 模型的大小。默认为 "medium"。
        device (str, optional): 使用的设备，可以是 "cuda" 或 "cpu"。默认为 "cuda"。
        language (str, optional): 音频的语言。默认为 "zh" (中文)。
    """
    global total_audio_duration, total_transcription_time

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"Error: 文件 {file_path} 不存在。")
        return

    # 尝试加载 Whisper 模型
    try:
        model = whisper.load_model(model_size, device=device)
    except Exception as e:
        print(f"Error: 无法加载 Whisper 模型：{e}")
        return

    # 转录音频文件
    # print(f"正在使用 Whisper {model_size} 模型在 {device} 上转录 {file_path} ...")
    try:
        result = model.transcribe(file_path, language=language)
    except Exception as e:
        print(f"Error: 转录音频文件时出错：{e}")
        return

    # 使用 whisper.utils 保存转录结果
    output_dir = os.path.dirname(file_path)
    writers = {
        # "txt": whisper.utils.WriteTXT(output_dir),
        "srt": whisper.utils.WriteSRT(output_dir),
        # "vtt": whisper.utils.WriteVTT(output_dir),
    }
    for ext in writers:
        try:
            writers[ext](result, file_path)
            # print(f"转录结果已保存为 {os.path.splitext(file_path)[0]}.{ext}")
        except Exception as e:
            print(f"Error: 无法保存 .{ext} 文件：{e}")

    tg_file_path = os.path.join(
        os.path.dirname(file_path),
        "tg_[" + os.path.basename(file_path).split(".")[0] + "]",
    )
    txt_file_path = tg_file_path + ".txt"
    try:
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            for segment in result["segments"]:
                start_time = segment["start"]
                text = segment["text"]

                # 格式化时间，只保留分钟和秒
                start_time_str = whisper.utils.format_timestamp(start_time)[:5]
                txt_file.write(f"{start_time_str} {text}\n")
        print(f"转录结果已保存为 {txt_file_path}")
    except Exception as e:
        print(f"Error: 无法保存 .txt 文件：{e}")

    # 输出信息
    return txt_file_path

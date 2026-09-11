import whisper


# Load model once when worker starts
model = whisper.load_model("base")


def transcribe_audio(audio_path: str) -> str:
    """
    Convert candidate audio into text using Whisper.
    """

    result = model.transcribe(
        audio_path,
        fp16=False
    )

    return result["text"].strip()
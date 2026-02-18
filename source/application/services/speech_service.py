import io
import logging
import os
from typing import Optional

from deepgram import DeepgramClient

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Сервис для распознавания речи с использованием Deepgram API (SDK v5+).

    Поддерживает pre-recorded аудио из байтов.
    """

    def __init__(
            self,
            api_key: str = os.getenv("SPEECH_API_KEY"),
    ):
        self.client = DeepgramClient(api_key=api_key)

        self.default_options = {
            "model": "nova-2",
            "language": "ru",
            "smart_format": True,
            "punctuate": True,
            "paragraphs": False,
            "diarize": False,
            # Дополнительно: "utterances": True, "numerals": True, "profanity_filter": False и т.д.
        }

    async def transcribe_bytes(
            self,
            audio_bytes: bytes,
            language: Optional[str] = None,
            model: Optional[str] = None,
            **override_options,
    ) -> str:
        """
        Распознавание речи из сырых байтов аудио (ogg, mp3, wav, pcm и т.д.).
        """
        if not audio_bytes:
            raise ValueError("Пустой аудио буфер")

        options = self.default_options.copy()
        if language:
            options["language"] = language
        if model:
            options["model"] = model
        options.update(override_options)

        try:
            # В v5+ передаём байты напрямую в request (без {"buffer": ...})
            response = self.client.listen.v1.media.transcribe_file(
                request=audio_bytes,  # ← просто bytes
                **options  # ← kwargs вместо отдельного словаря
            )

            # Структура ответа в v5+ почти та же
            if (
                    hasattr(response, "results")
                    and response.results.channels
                    and response.results.channels[0].alternatives
            ):
                transcript = response.results.channels[0].alternatives[0].transcript
                return transcript.strip() if transcript else ""

            return ""  # тишина или очень короткий файл

        except Exception as e:
            logger.exception("Ошибка транскрипции Deepgram")
            raise ValueError(f"Не удалось распознать аудио: {str(e)}")

    async def transcribe_file(self, file_path: str | io.BufferedIOBase, **kwargs) -> str:
        if isinstance(file_path, str):
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
        elif isinstance(file_path, io.BufferedIOBase):
            audio_bytes = file_path.read()
        else:
            raise TypeError("Ожидался путь или открытый файл")

        return await self.transcribe_bytes(audio_bytes, **kwargs)

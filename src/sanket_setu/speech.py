"""Speech processing for Sanket Setu: Text-to-Speech (TTS) and Speech-to-Text (STT).

Text-to-speech supports Hindi and English with an in-memory cache to ensure
instant replay of common counter phrases. Audio transcription allows staff speech
to be converted to large, high-contrast text on visitor screens.
"""
from __future__ import annotations

import io
import logging

log = logging.getLogger("sanket_setu.speech")


class SpeechUnavailable(RuntimeError):
    pass


# In-memory LRU-style cache for generated audio bytes: (text, lang) -> bytes
_TTS_CACHE: dict[tuple[str, str], bytes] = {}
_MAX_CACHE_SIZE = 128


def synthesize(text: str, lang: str = "hi") -> bytes:
    """Return MP3 bytes for plain text via gTTS with in-memory caching.
    
    Never sends images or landmarks. Needs internet connection for first synthesis of a phrase.
    """
    clean_text = text.strip()
    if not clean_text:
        raise SpeechUnavailable("Nothing to speak.")

    cache_key = (clean_text, lang)
    if cache_key in _TTS_CACHE:
        return _TTS_CACHE[cache_key]

    try:
        from gtts import gTTS
    except ImportError as exc:
        raise SpeechUnavailable("Audio needs the optional gTTS package: pip install gTTS") from exc

    try:
        buf = io.BytesIO()
        gTTS(text=clean_text, lang=lang).write_to_fp(buf)
        audio_data = buf.getvalue()

        if len(_TTS_CACHE) >= _MAX_CACHE_SIZE:
            # Drop oldest entry
            _TTS_CACHE.pop(next(iter(_TTS_CACHE)))
        _TTS_CACHE[cache_key] = audio_data

        return audio_data
    except Exception as exc:
        log.warning("TTS generation failed for '%s': %s", clean_text, exc)
        raise SpeechUnavailable(
            "Audio could not be generated (internet connection needed). The text above is still valid."
        ) from exc


def transcribe_audio(audio_bytes: bytes, lang: str = "hi-IN") -> str:
    """Transcribe speech audio to text for staff reverse communication."""
    if not audio_bytes:
        raise SpeechUnavailable("No audio received for transcription.")
    # Basic size check (10MB max)
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise SpeechUnavailable("Audio payload exceeds 10MB limit.")
    
    # Try using speech_recognition if installed
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data, language=lang)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            raise SpeechUnavailable("Speech recognition service unavailable.") from exc
    except ImportError:
        # Fallback explanation if optional audio library is absent
        raise SpeechUnavailable(
            "Audio transcription library is not installed on this server. "
            "Staff can type or select quick phrases."
        )

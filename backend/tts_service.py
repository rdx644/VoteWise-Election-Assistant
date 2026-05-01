"""
Google Cloud Text-to-Speech integration for VoteWise.
"""

from __future__ import annotations

import logging

from backend.config import settings

logger = logging.getLogger("votewise.tts")


async def synthesize_speech(
    text: str,
    voice_name: str = "en-US-Neural2-C",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
) -> str | None:
    """Synthesize speech from text using Google Cloud TTS or browser fallback."""
    if settings.tts_mode != "google":
        return None

    try:  # pragma: no cover
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text[:5000])
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
        )
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        import base64

        return base64.b64encode(response.audio_content).decode("utf-8")
    except Exception as e:  # pragma: no cover
        logger.warning(f"TTS synthesis failed: {e}")
        return None

"""
Naver Clova Speech API Integration
Handles Speech-to-Text with speaker diarization
"""

import asyncio
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from pydantic_settings import BaseSettings


class ClovaSettings(BaseSettings):
    """Clova API settings"""
    clova_api_key: str = ""
    clova_api_secret: str = ""
    clova_invoke_url: str = "https://clovaspeech-gw.ncloud.com/recog/v1/stt"
    
    class Config:
        env_file = ".env"


settings = ClovaSettings()


@dataclass
class TranscriptSegment:
    """Single transcript segment"""
    speaker: str
    text: str
    start_time: float  # in seconds
    end_time: float
    confidence: float


@dataclass
class STTResult:
    """Complete STT result"""
    segments: List[TranscriptSegment]
    raw_text: str
    speakers: List[str]
    duration: float


class ClovaSTTClient:
    """
    Client for Naver Clova Speech-to-Text API
    
    Features:
    - Speaker diarization (화자 분리)
    - Korean language optimized
    - Keyword boosting support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        invoke_url: Optional[str] = None,
    ):
        self.api_key = api_key or settings.clova_api_key
        self.api_secret = api_secret or settings.clova_api_secret
        self.invoke_url = invoke_url or settings.clova_invoke_url
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "X-CLOVASPEECH-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def transcribe_url(
        self,
        audio_url: str,
        language: str = "ko-KR",
        enable_diarization: bool = True,
        speaker_count_min: int = 1,
        speaker_count_max: int = 6,
        boosting_words: Optional[List[str]] = None,
    ) -> STTResult:
        """
        Transcribe audio from URL
        
        Args:
            audio_url: URL to the audio file
            language: Language code (default: Korean)
            enable_diarization: Enable speaker separation
            speaker_count_min: Minimum expected speakers
            speaker_count_max: Maximum expected speakers
            boosting_words: Words to boost recognition for
        
        Returns:
            STTResult with transcripts and metadata
        """
        request_body = {
            "url": audio_url,
            "language": language,
            "completion": "sync",  # or "async" for long files
            "diarization": {
                "enable": enable_diarization,
                "speakerCountMin": speaker_count_min,
                "speakerCountMax": speaker_count_max,
            },
        }
        
        # Add keyword boosting if provided
        if boosting_words:
            request_body["boostings"] = [
                {"words": word} for word in boosting_words
            ]
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.invoke_url}/recognizer/url",
                headers=self._get_headers(),
                json=request_body,
            )
            
            response.raise_for_status()
            result = response.json()
        
        return self._parse_result(result)
    
    async def transcribe_file(
        self,
        file_path: str,
        language: str = "ko-KR",
        enable_diarization: bool = True,
        speaker_count_min: int = 1,
        speaker_count_max: int = 6,
        boosting_words: Optional[List[str]] = None,
    ) -> STTResult:
        """
        Transcribe audio from local file
        
        Args:
            file_path: Path to the audio file
            language: Language code
            enable_diarization: Enable speaker separation
            speaker_count_min: Minimum expected speakers
            speaker_count_max: Maximum expected speakers
            boosting_words: Words to boost recognition for
        
        Returns:
            STTResult with transcripts and metadata
        """
        params = {
            "language": language,
            "diarization": json.dumps({
                "enable": enable_diarization,
                "speakerCountMin": speaker_count_min,
                "speakerCountMax": speaker_count_max,
            }),
        }
        
        if boosting_words:
            params["boostings"] = json.dumps([
                {"words": word} for word in boosting_words
            ])
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(file_path, "rb") as f:
                files = {"media": f}
                response = await client.post(
                    f"{self.invoke_url}/recognizer/upload",
                    headers={"X-CLOVASPEECH-API-KEY": self.api_key},
                    params=params,
                    files=files,
                )
            
            response.raise_for_status()
            result = response.json()
        
        return self._parse_result(result)
    
    def _parse_result(self, result: Dict[str, Any]) -> STTResult:
        """
        Parse Clova API response into STTResult
        
        Args:
            result: Raw API response
        
        Returns:
            Structured STTResult
        """
        segments = []
        speakers = set()
        max_end_time = 0.0
        
        # Extract segments from response
        if "segments" in result:
            for seg in result["segments"]:
                # Get speaker label
                speaker = seg.get("speaker", {}).get("label", "Unknown")
                if speaker == "":
                    speaker = "Unknown"
                
                speakers.add(speaker)
                
                # Get timing in seconds
                start_time = seg.get("start", 0) / 1000.0
                end_time = seg.get("end", 0) / 1000.0
                max_end_time = max(max_end_time, end_time)
                
                # Get text and confidence
                text = seg.get("text", "").strip()
                confidence = seg.get("confidence", 0.0)
                
                if text:  # Only add non-empty segments
                    segments.append(TranscriptSegment(
                        speaker=speaker,
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                        confidence=confidence,
                    ))
        
        # Build raw text
        raw_text = " ".join(seg.text for seg in segments)
        
        # Sort speakers for consistent naming
        speaker_list = sorted(list(speakers))
        
        return STTResult(
            segments=segments,
            raw_text=raw_text,
            speakers=speaker_list,
            duration=max_end_time,
        )
    
    def format_transcript(self, result: STTResult) -> str:
        """
        Format transcript for LLM processing
        
        Args:
            result: STTResult from transcription
        
        Returns:
            Formatted transcript string with speaker labels
        """
        lines = []
        current_speaker = None
        current_texts = []
        
        for seg in result.segments:
            if seg.speaker != current_speaker:
                # Save previous speaker's text
                if current_speaker is not None and current_texts:
                    lines.append(f"[{current_speaker}]: {' '.join(current_texts)}")
                
                current_speaker = seg.speaker
                current_texts = [seg.text]
            else:
                current_texts.append(seg.text)
        
        # Don't forget the last speaker
        if current_speaker is not None and current_texts:
            lines.append(f"[{current_speaker}]: {' '.join(current_texts)}")
        
        return "\n\n".join(lines)


# Singleton instance
_clova_client: Optional[ClovaSTTClient] = None


def get_clova_client() -> ClovaSTTClient:
    """Get or create the Clova client singleton"""
    global _clova_client
    if _clova_client is None:
        _clova_client = ClovaSTTClient()
    return _clova_client


async def transcribe_audio(
    audio_url: str,
    boosting_words: Optional[List[str]] = None,
) -> STTResult:
    """
    Convenience function to transcribe audio
    
    Args:
        audio_url: URL to the audio file
        boosting_words: Optional words to boost recognition
    
    Returns:
        STTResult with transcripts
    """
    client = get_clova_client()
    return await client.transcribe_url(
        audio_url=audio_url,
        boosting_words=boosting_words,
    )

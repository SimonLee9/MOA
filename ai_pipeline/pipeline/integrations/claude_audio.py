"""
Claude Audio Integration

Claude API의 오디오 입력 기능을 활용하여 음성 파일을 직접 처리합니다.
Clova STT 없이 Claude만으로 음성 → 트랜스크립트 → 요약을 수행합니다.
"""

import base64
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import BinaryIO

from anthropic import Anthropic, APIError

from app.config import settings

logger = logging.getLogger(__name__)

# 지원하는 오디오 형식
SUPPORTED_AUDIO_FORMATS = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}

# 최대 파일 크기 (25MB)
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024


@dataclass
class AudioTranscriptResult:
    """오디오 처리 결과"""

    transcript: str
    summary: str | None = None
    speakers: list[str] | None = None
    key_points: list[str] | None = None
    action_items: list[dict] | None = None
    duration_seconds: float | None = None
    model: str = ""


class ClaudeAudioProcessor:
    """
    Claude API를 사용한 오디오 처리기

    기능:
    - 오디오 파일을 직접 Claude에 전달
    - 트랜스크립트 생성 (화자 분리 포함)
    - 요약 및 액션 아이템 추출
    - 단일 API 호출로 통합 처리
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """
        Args:
            api_key: Anthropic API 키 (없으면 환경변수에서 로드)
            model: 사용할 Claude 모델
        """
        self.api_key = api_key or getattr(settings, "claude_api_key", None)
        if not self.api_key:
            raise ValueError("Claude API key is required")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def _get_media_type(self, file_path: Path) -> str:
        """파일 확장자로 media type 결정"""
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(
                f"지원하지 않는 오디오 형식: {suffix}. "
                f"지원 형식: {list(SUPPORTED_AUDIO_FORMATS.keys())}"
            )
        return SUPPORTED_AUDIO_FORMATS[suffix]

    def _encode_audio(self, file_path: Path) -> str:
        """오디오 파일을 base64로 인코딩"""
        file_size = file_path.stat().st_size
        if file_size > MAX_AUDIO_SIZE_BYTES:
            raise ValueError(
                f"파일 크기 초과: {file_size / 1024 / 1024:.1f}MB > "
                f"{MAX_AUDIO_SIZE_BYTES / 1024 / 1024}MB"
            )

        with open(file_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _encode_audio_stream(self, audio_stream: BinaryIO) -> str:
        """오디오 스트림을 base64로 인코딩"""
        data = audio_stream.read()
        if len(data) > MAX_AUDIO_SIZE_BYTES:
            raise ValueError(
                f"파일 크기 초과: {len(data) / 1024 / 1024:.1f}MB"
            )
        return base64.standard_b64encode(data).decode("utf-8")

    async def transcribe(
        self,
        audio_path: str | Path,
        language: str = "ko",
        include_timestamps: bool = False,
    ) -> AudioTranscriptResult:
        """
        오디오 파일을 트랜스크립트로 변환

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en 등)
            include_timestamps: 타임스탬프 포함 여부

        Returns:
            AudioTranscriptResult: 트랜스크립트 결과
        """
        audio_path = Path(audio_path)
        media_type = self._get_media_type(audio_path)
        audio_data = self._encode_audio(audio_path)

        timestamp_instruction = ""
        if include_timestamps:
            timestamp_instruction = """
각 발화에 대략적인 타임스탬프를 [MM:SS] 형식으로 포함해주세요.
"""

        prompt = f"""이 오디오 파일의 내용을 정확하게 텍스트로 변환해주세요.

언어: {language}

요구사항:
1. 화자가 여러 명인 경우 "화자 1:", "화자 2:" 등으로 구분해주세요
2. 말한 내용을 그대로 정확하게 받아적어주세요
3. 불명확한 부분은 [불명확] 으로 표시해주세요
{timestamp_instruction}

트랜스크립트만 출력하고, 다른 설명은 하지 마세요."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": audio_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            transcript = message.content[0].text

            # 화자 목록 추출
            speakers = self._extract_speakers(transcript)

            return AudioTranscriptResult(
                transcript=transcript,
                speakers=speakers,
                model=self.model,
            )

        except APIError as e:
            logger.error(f"Claude API 오류: {e}")
            raise

    async def transcribe_and_summarize(
        self,
        audio_path: str | Path,
        meeting_title: str | None = None,
        language: str = "ko",
    ) -> AudioTranscriptResult:
        """
        오디오 파일을 트랜스크립트로 변환하고 요약까지 수행

        단일 API 호출로 STT + 요약 + 액션 아이템 추출을 모두 처리합니다.

        Args:
            audio_path: 오디오 파일 경로
            meeting_title: 회의 제목 (선택)
            language: 언어 코드

        Returns:
            AudioTranscriptResult: 트랜스크립트, 요약, 액션 아이템 포함
        """
        audio_path = Path(audio_path)
        media_type = self._get_media_type(audio_path)
        audio_data = self._encode_audio(audio_path)

        title_context = f"회의 제목: {meeting_title}\n" if meeting_title else ""

        prompt = f"""이 오디오 파일의 회의 내용을 분석해주세요.

{title_context}언어: {language}

다음 형식으로 응답해주세요:

## 트랜스크립트
(화자 구분하여 전체 내용을 정확하게 텍스트로 변환)

## 요약
(회의의 핵심 내용을 3-5문장으로 요약)

## 핵심 포인트
- (중요한 논의 사항 1)
- (중요한 논의 사항 2)
- (중요한 논의 사항 3)

## 액션 아이템
- [ ] (할 일 1) - 담당자: (이름 또는 미정)
- [ ] (할 일 2) - 담당자: (이름 또는 미정)

## 화자 목록
- 화자 1: (역할이나 특징)
- 화자 2: (역할이나 특징)
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": audio_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = message.content[0].text

            # 응답 파싱
            result = self._parse_full_response(response_text)
            result.model = self.model

            return result

        except APIError as e:
            logger.error(f"Claude API 오류: {e}")
            raise

    def _extract_speakers(self, transcript: str) -> list[str]:
        """트랜스크립트에서 화자 목록 추출"""
        import re

        speakers = set()
        # "화자 1:", "화자 2:", "Speaker 1:" 등의 패턴 찾기
        patterns = [
            r"(화자\s*\d+)\s*:",
            r"(Speaker\s*\d+)\s*:",
            r"([가-힣]{2,4})\s*:",  # 한글 이름
        ]

        for pattern in patterns:
            matches = re.findall(pattern, transcript)
            speakers.update(matches)

        return list(speakers) if speakers else []

    def _parse_full_response(self, response: str) -> AudioTranscriptResult:
        """전체 응답을 파싱하여 구조화된 결과 반환"""
        import re

        result = AudioTranscriptResult(transcript="", summary=None)

        # 섹션별로 분리
        sections = {
            "트랜스크립트": "",
            "요약": "",
            "핵심 포인트": [],
            "액션 아이템": [],
            "화자 목록": [],
        }

        current_section = None
        current_content = []

        for line in response.split("\n"):
            # 섹션 헤더 감지
            if line.startswith("## "):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # 마지막 섹션 저장
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        # 결과 구성
        result.transcript = sections.get("트랜스크립트", "")
        result.summary = sections.get("요약", None)

        # 핵심 포인트 파싱
        key_points_text = sections.get("핵심 포인트", "")
        if key_points_text:
            result.key_points = [
                line.lstrip("- ").strip()
                for line in key_points_text.split("\n")
                if line.strip().startswith("-")
            ]

        # 액션 아이템 파싱
        actions_text = sections.get("액션 아이템", "")
        if actions_text:
            result.action_items = []
            for line in actions_text.split("\n"):
                if line.strip().startswith("- ["):
                    # "- [ ] 할 일 - 담당자: 이름" 형식 파싱
                    match = re.match(
                        r"-\s*\[[x\s]?\]\s*(.+?)(?:\s*-\s*담당자:\s*(.+))?$",
                        line.strip(),
                        re.IGNORECASE,
                    )
                    if match:
                        result.action_items.append({
                            "content": match.group(1).strip(),
                            "assignee": match.group(2).strip() if match.group(2) else "미정",
                            "priority": "medium",
                        })

        # 화자 목록 파싱
        speakers_text = sections.get("화자 목록", "")
        if speakers_text:
            result.speakers = [
                line.lstrip("- ").split(":")[0].strip()
                for line in speakers_text.split("\n")
                if line.strip().startswith("-")
            ]
        else:
            result.speakers = self._extract_speakers(result.transcript)

        return result


# 싱글톤 인스턴스 (lazy initialization)
_processor: ClaudeAudioProcessor | None = None


def get_audio_processor() -> ClaudeAudioProcessor:
    """오디오 프로세서 인스턴스 반환"""
    global _processor
    if _processor is None:
        _processor = ClaudeAudioProcessor()
    return _processor

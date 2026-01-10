"""
Claude API Integration
Handles all interactions with Anthropic's Claude API
"""

import json
import re
from typing import Optional, Any, Dict

from anthropic import Anthropic, AsyncAnthropic
from pydantic_settings import BaseSettings


class ClaudeSettings(BaseSettings):
    """Claude API settings"""
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096
    
    class Config:
        env_file = ".env"


settings = ClaudeSettings()


class ClaudeClient:
    """
    Async client for Claude API interactions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.claude_api_key
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self._client: Optional[AsyncAnthropic] = None
    
    @property
    def client(self) -> AsyncAnthropic:
        """Lazy initialization of async client"""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response from Claude
        
        Args:
            user_prompt: The user message
            system_prompt: Optional system message
            temperature: Sampling temperature (0-1)
            max_tokens: Max tokens in response
        
        Returns:
            Claude's text response
        """
        messages = [{"role": "user", "content": user_prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = await self.client.messages.create(**kwargs)
        
        # Extract text from response
        return response.content[0].text
    
    async def generate_json(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from Claude
        
        Args:
            user_prompt: The user message
            system_prompt: Optional system message
            temperature: Sampling temperature (lower for more deterministic)
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response_text = await self.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        
        # Try to extract JSON from response
        json_str = self._extract_json(response_text)
        
        return json.loads(json_str)
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain markdown code blocks
        
        Args:
            text: Raw text that might contain JSON
        
        Returns:
            Cleaned JSON string
        """
        # Try to find JSON in code blocks first
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        
        if matches:
            return matches[0].strip()
        
        # Try to find raw JSON object
        json_pattern = r"\{[\s\S]*\}"
        matches = re.findall(json_pattern, text)
        
        if matches:
            # Return the largest match (likely the full JSON)
            return max(matches, key=len)
        
        # Return original text and let JSON parser handle errors
        return text.strip()
    
    async def close(self):
        """Close the client connection"""
        if self._client:
            await self._client.close()
            self._client = None


# Singleton instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create the Claude client singleton"""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client


async def generate_summary(
    transcript: str,
    meeting_title: str,
    meeting_date: Optional[str],
    speakers: list[str],
) -> Dict[str, Any]:
    """
    Generate meeting summary using Claude
    
    Args:
        transcript: Full meeting transcript
        meeting_title: Title of the meeting
        meeting_date: Date of the meeting
        speakers: List of speaker names
    
    Returns:
        Dictionary with summary, key_points, decisions
    """
    from pipeline.prompts.summarize import (
        SUMMARY_SYSTEM_PROMPT,
        SUMMARY_USER_PROMPT,
    )
    
    client = get_claude_client()
    
    user_prompt = SUMMARY_USER_PROMPT.format(
        meeting_title=meeting_title,
        meeting_date=meeting_date or "미정",
        speakers=", ".join(speakers) if speakers else "미상",
        transcript=transcript,
    )
    
    return await client.generate_json(
        user_prompt=user_prompt,
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        temperature=0.3,
    )


async def extract_actions(
    transcript: str,
    summary: str,
    meeting_title: str,
    meeting_date: Optional[str],
    speakers: list[str],
) -> Dict[str, Any]:
    """
    Extract action items from meeting
    
    Args:
        transcript: Full meeting transcript
        summary: Generated summary
        meeting_title: Title of the meeting
        meeting_date: Date of the meeting
        speakers: List of speaker names
    
    Returns:
        Dictionary with action_items list
    """
    from pipeline.prompts.extract_actions import (
        format_action_system_prompt,
        ACTION_USER_PROMPT,
    )
    
    client = get_claude_client()
    
    user_prompt = ACTION_USER_PROMPT.format(
        meeting_title=meeting_title,
        meeting_date=meeting_date or "미정",
        speakers=", ".join(speakers) if speakers else "미상",
        transcript=transcript,
        summary=summary,
    )
    
    return await client.generate_json(
        user_prompt=user_prompt,
        system_prompt=format_action_system_prompt(),
        temperature=0.2,
    )


async def critique_results(
    transcript: str,
    summary: str,
    key_points: list[str],
    decisions: list[str],
    action_items: list[dict],
) -> Dict[str, Any]:
    """
    Critique and validate the generated results
    
    Args:
        transcript: Original transcript
        summary: Generated summary
        key_points: Extracted key points
        decisions: Extracted decisions
        action_items: Extracted action items
    
    Returns:
        Dictionary with passed, issues, suggestions, critique
    """
    from pipeline.prompts.critique import (
        CRITIQUE_SYSTEM_PROMPT,
        CRITIQUE_USER_PROMPT,
    )
    
    client = get_claude_client()
    
    # Format action items for display
    action_items_str = json.dumps(action_items, ensure_ascii=False, indent=2)
    key_points_str = "\n".join(f"- {kp}" for kp in key_points)
    decisions_str = "\n".join(f"- {d}" for d in decisions) if decisions else "없음"
    
    user_prompt = CRITIQUE_USER_PROMPT.format(
        transcript=transcript,
        summary=summary,
        key_points=key_points_str,
        decisions=decisions_str,
        action_items=action_items_str,
    )
    
    return await client.generate_json(
        user_prompt=user_prompt,
        system_prompt=CRITIQUE_SYSTEM_PROMPT,
        temperature=0.1,  # Low temperature for consistent evaluation
    )

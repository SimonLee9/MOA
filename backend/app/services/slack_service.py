"""
Slack Integration Service
Sends notifications to Slack channels
"""

import logging
from typing import Optional
from datetime import datetime
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Service for sending Slack notifications"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or getattr(settings, 'slack_webhook_url', None)
        self.enabled = bool(self.webhook_url)

    async def send_message(
        self,
        text: str,
        channel: Optional[str] = None,
        username: str = "MOA Bot",
        icon_emoji: str = ":robot_face:",
        attachments: Optional[list] = None,
        blocks: Optional[list] = None,
    ) -> bool:
        """Send a message to Slack"""
        if not self.enabled:
            logger.warning("Slack integration not configured")
            return False

        payload = {
            "text": text,
            "username": username,
            "icon_emoji": icon_emoji,
        }

        if channel:
            payload["channel"] = channel
        if attachments:
            payload["attachments"] = attachments
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info(f"Slack message sent successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    async def send_review_notification(
        self,
        meeting_title: str,
        meeting_id: str,
        meeting_url: str,
    ) -> bool:
        """Send a notification when a meeting needs review"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "회의 검토 요청",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*회의:*\n{meeting_title}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*상태:*\n검토 대기 중",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "AI가 회의 내용을 분석했습니다. 결과를 검토해주세요.",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "검토하기",
                            "emoji": True,
                        },
                        "style": "primary",
                        "url": meeting_url,
                    },
                ],
            },
        ]

        return await self.send_message(
            text=f"회의 '{meeting_title}' 검토가 필요합니다.",
            blocks=blocks,
        )

    async def send_processing_complete(
        self,
        meeting_title: str,
        meeting_url: str,
        summary_preview: Optional[str] = None,
        action_items_count: int = 0,
    ) -> bool:
        """Send notification when meeting processing is complete"""
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*회의:*\n{meeting_title}",
            },
            {
                "type": "mrkdwn",
                "text": f"*액션 아이템:*\n{action_items_count}개",
            },
        ]

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "회의 처리 완료",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": fields,
            },
        ]

        if summary_preview:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*요약:*\n{summary_preview[:300]}...",
                },
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "회의 보기",
                        "emoji": True,
                    },
                    "url": meeting_url,
                },
            ],
        })

        return await self.send_message(
            text=f"회의 '{meeting_title}' 처리가 완료되었습니다.",
            blocks=blocks,
        )

    async def send_processing_failed(
        self,
        meeting_title: str,
        meeting_url: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """Send notification when meeting processing fails"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "회의 처리 실패",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*회의:*\n{meeting_title}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*상태:*\n:x: 처리 실패",
                    },
                ],
            },
        ]

        if error_message:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*오류:*\n```{error_message[:500]}```",
                },
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "회의 확인",
                        "emoji": True,
                    },
                    "url": meeting_url,
                },
            ],
        })

        return await self.send_message(
            text=f"회의 '{meeting_title}' 처리에 실패했습니다.",
            blocks=blocks,
        )

    async def send_action_item_reminder(
        self,
        assignee: str,
        action_content: str,
        due_date: datetime,
        meeting_title: str,
        meeting_url: str,
    ) -> bool:
        """Send reminder for upcoming action item deadline"""
        due_str = due_date.strftime("%Y년 %m월 %d일")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "액션 아이템 마감 알림",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*담당자:*\n{assignee}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*마감일:*\n{due_str}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*액션 아이템:*\n{action_content}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"회의: {meeting_title}",
                    },
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "회의 보기",
                        },
                        "url": meeting_url,
                    },
                ],
            },
        ]

        return await self.send_message(
            text=f"액션 아이템 마감 알림: {action_content}",
            blocks=blocks,
        )


# Singleton instance
slack_service = SlackService()

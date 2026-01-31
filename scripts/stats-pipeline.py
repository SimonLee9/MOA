#!/usr/bin/env python3
"""
AI 파이프라인 성능 통계 분석 스크립트

Usage:
    python scripts/stats-pipeline.py [options]

Options:
    --days       분석할 기간 (일 단위, 기본: 7)
    --output     결과 출력 형식 (text, json)
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 색상 코드
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


@dataclass
class PipelineStats:
    """파이프라인 통계"""

    total_meetings: int = 0
    completed_meetings: int = 0
    failed_meetings: int = 0
    processing_meetings: int = 0

    total_processing_time_seconds: float = 0
    avg_processing_time_seconds: float = 0
    min_processing_time_seconds: float = float("inf")
    max_processing_time_seconds: float = 0

    total_audio_duration_seconds: float = 0
    avg_audio_duration_seconds: float = 0

    stt_success_rate: float = 0
    summarization_success_rate: float = 0
    action_extraction_success_rate: float = 0

    action_items_extracted: int = 0
    avg_action_items_per_meeting: float = 0

    def to_dict(self) -> dict:
        return {
            "meetings": {
                "total": self.total_meetings,
                "completed": self.completed_meetings,
                "failed": self.failed_meetings,
                "processing": self.processing_meetings,
                "completion_rate": round(self.completed_meetings / max(1, self.total_meetings) * 100, 1),
            },
            "processing_time": {
                "total_seconds": round(self.total_processing_time_seconds, 1),
                "avg_seconds": round(self.avg_processing_time_seconds, 1),
                "min_seconds": round(self.min_processing_time_seconds, 1) if self.min_processing_time_seconds != float("inf") else 0,
                "max_seconds": round(self.max_processing_time_seconds, 1),
            },
            "audio": {
                "total_duration_seconds": round(self.total_audio_duration_seconds, 1),
                "total_duration_hours": round(self.total_audio_duration_seconds / 3600, 2),
                "avg_duration_seconds": round(self.avg_audio_duration_seconds, 1),
            },
            "success_rates": {
                "stt": round(self.stt_success_rate, 1),
                "summarization": round(self.summarization_success_rate, 1),
                "action_extraction": round(self.action_extraction_success_rate, 1),
            },
            "action_items": {
                "total": self.action_items_extracted,
                "avg_per_meeting": round(self.avg_action_items_per_meeting, 1),
            },
        }


def load_pipeline_logs(log_dir: Path, days: int) -> list[dict]:
    """파이프라인 로그 로드 (시뮬레이션)"""
    # 실제 구현에서는 데이터베이스나 로그 파일에서 로드
    # 여기서는 샘플 데이터 반환
    cutoff_date = datetime.now() - timedelta(days=days)

    sample_logs = [
        {
            "meeting_id": "m001",
            "status": "completed",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "completed_at": (datetime.now() - timedelta(days=1, hours=-1)).isoformat(),
            "audio_duration_seconds": 3600,
            "processing_time_seconds": 180,
            "stt_status": "success",
            "summarization_status": "success",
            "action_items_count": 5,
        },
        {
            "meeting_id": "m002",
            "status": "completed",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "completed_at": (datetime.now() - timedelta(days=2, hours=-0.5)).isoformat(),
            "audio_duration_seconds": 1800,
            "processing_time_seconds": 90,
            "stt_status": "success",
            "summarization_status": "success",
            "action_items_count": 3,
        },
        {
            "meeting_id": "m003",
            "status": "failed",
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "audio_duration_seconds": 7200,
            "stt_status": "failed",
            "error": "STT API timeout",
        },
        {
            "meeting_id": "m004",
            "status": "processing",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "audio_duration_seconds": 2700,
            "stt_status": "success",
            "summarization_status": "processing",
        },
    ]

    return sample_logs


def calculate_stats(logs: list[dict]) -> PipelineStats:
    """통계 계산"""
    stats = PipelineStats()

    if not logs:
        return stats

    stats.total_meetings = len(logs)

    completed_logs = []
    processing_times = []
    audio_durations = []
    action_counts = []

    stt_success = 0
    summarization_success = 0
    action_success = 0

    for log in logs:
        status = log.get("status", "unknown")

        if status == "completed":
            stats.completed_meetings += 1
            completed_logs.append(log)

            if "processing_time_seconds" in log:
                pt = log["processing_time_seconds"]
                processing_times.append(pt)
                stats.total_processing_time_seconds += pt
                stats.min_processing_time_seconds = min(stats.min_processing_time_seconds, pt)
                stats.max_processing_time_seconds = max(stats.max_processing_time_seconds, pt)

            if log.get("action_items_count"):
                action_counts.append(log["action_items_count"])
                stats.action_items_extracted += log["action_items_count"]

        elif status == "failed":
            stats.failed_meetings += 1
        elif status == "processing":
            stats.processing_meetings += 1

        # 오디오 길이
        if "audio_duration_seconds" in log:
            audio_durations.append(log["audio_duration_seconds"])
            stats.total_audio_duration_seconds += log["audio_duration_seconds"]

        # 단계별 성공률
        if log.get("stt_status") == "success":
            stt_success += 1
        if log.get("summarization_status") == "success":
            summarization_success += 1
        if log.get("action_items_count", 0) > 0:
            action_success += 1

    # 평균 계산
    if processing_times:
        stats.avg_processing_time_seconds = sum(processing_times) / len(processing_times)

    if audio_durations:
        stats.avg_audio_duration_seconds = sum(audio_durations) / len(audio_durations)

    if action_counts:
        stats.avg_action_items_per_meeting = sum(action_counts) / len(action_counts)

    # 성공률 계산
    total = stats.total_meetings
    if total > 0:
        stats.stt_success_rate = (stt_success / total) * 100
        stats.summarization_success_rate = (summarization_success / total) * 100
        stats.action_extraction_success_rate = (action_success / total) * 100

    return stats


def print_stats_text(stats: PipelineStats, days: int) -> None:
    """텍스트 형식으로 통계 출력"""
    print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}           MOA Pipeline Statistics (Last {days} days){RESET}")
    print(f"{BLUE}═══════════════════════════════════════════════════════{RESET}\n")

    # 회의 통계
    print(f"{BOLD}📊 Meetings{RESET}")
    print(f"   Total:      {stats.total_meetings}")
    print(f"   Completed:  {GREEN}{stats.completed_meetings}{RESET}")
    print(f"   Failed:     {RED}{stats.failed_meetings}{RESET}")
    print(f"   Processing: {YELLOW}{stats.processing_meetings}{RESET}")

    completion_rate = stats.completed_meetings / max(1, stats.total_meetings) * 100
    color = GREEN if completion_rate >= 90 else YELLOW if completion_rate >= 70 else RED
    print(f"   Completion: {color}{completion_rate:.1f}%{RESET}")

    # 처리 시간
    print(f"\n{BOLD}⏱️  Processing Time{RESET}")
    print(f"   Average:    {stats.avg_processing_time_seconds:.1f}s")
    if stats.min_processing_time_seconds != float("inf"):
        print(f"   Min:        {stats.min_processing_time_seconds:.1f}s")
    print(f"   Max:        {stats.max_processing_time_seconds:.1f}s")

    # 오디오 통계
    print(f"\n{BOLD}🎙️  Audio{RESET}")
    total_hours = stats.total_audio_duration_seconds / 3600
    print(f"   Total:      {total_hours:.1f} hours")
    print(f"   Avg/meeting: {stats.avg_audio_duration_seconds / 60:.1f} min")

    # 성공률
    print(f"\n{BOLD}✅ Success Rates{RESET}")

    def rate_color(rate: float) -> str:
        if rate >= 95:
            return GREEN
        if rate >= 80:
            return YELLOW
        return RED

    print(f"   STT:           {rate_color(stats.stt_success_rate)}{stats.stt_success_rate:.1f}%{RESET}")
    print(f"   Summarization: {rate_color(stats.summarization_success_rate)}{stats.summarization_success_rate:.1f}%{RESET}")
    print(f"   Action Extract:{rate_color(stats.action_extraction_success_rate)}{stats.action_extraction_success_rate:.1f}%{RESET}")

    # 액션 아이템
    print(f"\n{BOLD}📋 Action Items{RESET}")
    print(f"   Total:      {stats.action_items_extracted}")
    print(f"   Avg/meeting: {stats.avg_action_items_per_meeting:.1f}")

    print(f"\n{BLUE}═══════════════════════════════════════════════════════{RESET}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 파이프라인 성능 통계")
    parser.add_argument("--days", type=int, default=7, help="분석 기간 (일)")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="출력 형식")
    parser.add_argument("--log-dir", type=Path, default=Path("logs/pipeline"),
                       help="로그 디렉토리")
    args = parser.parse_args()

    # 로그 로드
    logs = load_pipeline_logs(args.log_dir, args.days)

    if not logs:
        print(f"{YELLOW}Warning:{RESET} 분석할 로그 데이터가 없습니다.")
        print("(샘플 데이터를 사용하여 데모를 실행합니다)")

    # 통계 계산
    stats = calculate_stats(logs)

    # 출력
    if args.output == "json":
        print(json.dumps(stats.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_stats_text(stats, args.days)

    return 0


if __name__ == "__main__":
    sys.exit(main())

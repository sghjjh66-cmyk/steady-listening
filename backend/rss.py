"""
RSS 피드에서 최신 에피소드 정보를 가져오는 모듈.
PRD.md에 명시된 FT News Briefing Acast RSS 피드를 사용한다.
"""
import feedparser
import requests

RSS_FEED_URL = "https://feeds.acast.com/public/shows/73fe3ede-5c5c-4850-96a8-30db8dbae8bf"


def get_latest_episode() -> dict:
    """RSS 피드를 파싱해서 가장 최신 에피소드 정보를 반환한다.

    신규 에피소드인지 판별하는 로직(처리된 GUID와 비교)은 다음 단계(PLAN.md 4번)에서 추가한다.

    feedparser.parse(url)로 직접 호출하면 요청에 타임아웃이 없어서, 피드 서버가 느려지면
    이 함수가 무한정 멈춰버린다. requests로 먼저 받아서 타임아웃을 걸고,
    받은 내용만 feedparser에 넘겨서 파싱한다 (2026-07-24, 실제 배포 후 발견된 문제 대응).
    """
    response = requests.get(RSS_FEED_URL, timeout=20)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    if not feed.entries:
        raise ValueError("RSS 피드에서 에피소드를 찾을 수 없음")

    latest = feed.entries[0]  # RSS는 최신 에피소드가 맨 앞에 오도록 정렬되어 있음
    audio_url = latest.enclosures[0].href if latest.enclosures else None

    return {
        "guid": latest.get("id") or latest.get("guid"),
        "title": latest.get("title"),
        "audio_url": audio_url,
        "published": latest.get("published"),
    }

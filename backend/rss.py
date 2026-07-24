"""
RSS 피드에서 최신 에피소드 정보를 가져오는 모듈.
PRD.md에 명시된 FT News Briefing Acast RSS 피드를 사용한다.
"""
import feedparser

RSS_FEED_URL = "https://feeds.acast.com/public/shows/73fe3ede-5c5c-4850-96a8-30db8dbae8bf"


def get_latest_episode() -> dict:
    """RSS 피드를 파싱해서 가장 최신 에피소드 정보를 반환한다.

    신규 에피소드인지 판별하는 로직(처리된 GUID와 비교)은 다음 단계(PLAN.md 4번)에서 추가한다.
    """
    feed = feedparser.parse(RSS_FEED_URL)
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

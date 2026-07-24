"""
RSS에서 가져온 최신 에피소드가 이미 처리된 것인지 판별하는 모듈.
DESIGN.md 데이터흐름 A: "신규 에피소드 없음 -> 가장 최근 처리본 유지" 규칙을 따른다.
"""
from db import get_client
from rss import get_latest_episode


def check_new_episode() -> dict:
    """RSS 최신 에피소드의 GUID가 이미 처리된 것인지 확인한다.

    반환값:
      - 신규가 아니면: {"is_new": False, "episode": <가장 최근 처리된 에피소드 row>}
      - 신규이면: {"is_new": True, "rss": <RSS에서 가져온 최신 에피소드 정보>}
    """
    latest = get_latest_episode()
    client = get_client()

    existing = (
        client.table("episodes")
        .select("*")
        .eq("guid", latest["guid"])
        .limit(1)
        .execute()
    )

    if existing.data:
        return {"is_new": False, "episode": existing.data[0]}

    # 이 RSS 에피소드는 아직 처리된 적이 없음(신규).
    # 실제 다운로드·전사·표현 추출은 다음 단계(PLAN.md 5~10번)에서 처리한다.
    # 화면에는 신규 처리가 끝나기 전까지, DB에 있는 가장 최근 처리본을 계속 보여준다.
    most_recent = (
        client.table("episodes")
        .select("*")
        .order("processed_at", desc=True)
        .limit(1)
        .execute()
    )

    return {
        "is_new": True,
        "rss": latest,
        "current_displayed_episode": most_recent.data[0] if most_recent.data else None,
    }

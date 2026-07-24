"""
학습 완료 세션을 기록하는 모듈.
같은 날 이미 기록이 있으면 새로 기록하지 않아서, 최초 완료 시점의 모드가 그대로 유지된다
(sessions.session_date UNIQUE 제약 + ON CONFLICT DO NOTHING).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from db import get_client

# 서버가 배포되면 UTC 등 다른 시간대에서 돌 수 있으므로, "오늘"은 항상 한국 시간(KST) 기준으로 고정한다.
# (서버 로컬 시간에 맡기면, 자정 근처에 한국 기준 날짜와 하루씩 어긋날 수 있다.)
KST = ZoneInfo("Asia/Seoul")


def _current_episode_date(client) -> str:
    """지금 학습 화면에 노출 중인(가장 최근 처리된) 에피소드의 날짜를 KST 기준으로 반환한다.

    새 에피소드가 아직 안 올라온 시간대(예: 오전)에는 어제 처리분이 계속 표시되므로,
    이때 완료를 눌러도 "오늘"이 아니라 그 에피소드가 실제 처리된 날짜로 기록해야
    아직 공부하지 않은 오늘 칸이 잘못 체크되지 않는다.
    """
    result = (
        client.table("episodes")
        .select("processed_at")
        .order("processed_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return datetime.now(KST).date().isoformat()
    processed_at = datetime.fromisoformat(result.data[0]["processed_at"])
    return processed_at.astimezone(KST).date().isoformat()


def complete_session(mode: str) -> dict:
    """현재 노출 중인 에피소드 날짜(KST) 기준으로 학습 완료를 기록한다. 이미 그날 기록이 있으면 그대로 둔다."""
    client = get_client()
    session_date = _current_episode_date(client)

    client.table("sessions").upsert(
        {"session_date": session_date, "mode": mode},
        on_conflict="session_date",
        ignore_duplicates=True,
    ).execute()

    # ON CONFLICT DO NOTHING이면 upsert 응답이 비어있을 수 있어, 실제 저장된 값을 다시 조회한다.
    result = client.table("sessions").select("*").eq("session_date", session_date).execute()
    return result.data[0]


def get_all_sessions() -> list[dict]:
    """달력 화면에서 쓸, 완료 기록 전체(날짜+모드)를 반환한다."""
    client = get_client()
    result = client.table("sessions").select("session_date, mode").execute()
    return result.data

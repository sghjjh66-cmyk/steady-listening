"""
전체 처리 파이프라인을 에러 처리와 함께 감싸는 모듈.
프론트엔드 홈 화면은 앱 실행 시 get_episode_status() 하나만 호출하면 된다.

상태 3가지:
- "ready": 정상. 보여줄 에피소드가 있음
- "error": RSS·전사·OpenAI·저장 중 실패. 배너 + 재시도 버튼을 보여주고, RSS 실패 시에는
  직전에 처리된 최신 에피소드를 그대로 보여준다.
- "not_ready": 오디오 파일 자체가 아직 안 올라온 경우 (RSS에 에피소드는 있지만 다운로드 불가).
  실패가 아니므로 재시도 버튼 없이 "아직 준비되지 않음"만 보여주고, 다음 앱 실행 때 다시 확인한다.
"""
from audio import cache_audio
from db import get_client
from episodes import check_new_episode
from expressions_ai import extract_expressions
from save import save_episode, save_expressions
from transcribe import transcribe_from_url


def _get_most_recent_episode():
    """DB에 저장된 것 중 가장 최근에 처리된 에피소드를 반환한다 (없으면 None)."""
    client = get_client()
    result = (
        client.table("episodes")
        .select("*")
        .order("processed_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_episode_status() -> dict:
    """앱 실행 시 호출하는 상태 확인 함수."""
    try:
        check = check_new_episode()
    except Exception:
        # RSS 자체를 못 가져온 경우: 에러 배너+재시도, 직전 최신 에피소드는 그대로 유지
        return {"status": "error", "reason": "rss", "episode": _get_most_recent_episode()}

    if not check["is_new"]:
        return {"status": "ready", "episode": check["episode"]}

    rss = check["rss"]
    fallback_episode = check.get("current_displayed_episode")

    try:
        cached_url = cache_audio(rss["guid"], rss["audio_url"])
    except Exception:
        # 오디오가 아직 안 올라온 경우: 실패가 아니라 "준비 안됨" (재시도 버튼 없음, 다음 실행 때 재확인)
        return {"status": "not_ready", "episode": fallback_episode}

    try:
        transcript = transcribe_from_url(cached_url)
        expressions = extract_expressions(transcript)
    except Exception:
        return {"status": "error", "reason": "transcribe_or_extract", "episode": fallback_episode}

    try:
        episode_id = save_episode(rss["guid"], rss["title"], cached_url, transcript)
        save_expressions(episode_id, expressions)
    except Exception:
        return {"status": "error", "reason": "save", "episode": fallback_episode}

    return {
        "status": "ready",
        "episode": {
            "id": episode_id,
            "guid": rss["guid"],
            "title": rss["title"],
            "audio_storage_path": cached_url,
            "transcript": transcript,
        },
    }

"""
전체 처리 파이프라인을 에러 처리와 함께 감싸는 모듈.
프론트엔드 홈 화면은 앱 실행 시 get_episode_status() 하나만 호출하면 된다.

설계 (2026-07-24 개선):
- Render 무료 인스턴스는 접속이 뜸하면 잠들어서 재기동에 50초+가 걸리고, RSS 조회도 15~20초가 든다.
  그래서 매 요청마다 RSS를 동기로 조회하면 첫 로딩이 너무 느리거나 아예 멈춘 것처럼 보인다.
- 그래서 get_episode_status()는 **저장된 최신 에피소드를 DB에서 즉시 돌려주고**,
  새 에피소드 확인·처리(RSS 조회 + 다운로드 + 전사 + 추출 + 저장)는 응답을 보낸 뒤
  백그라운드(process_new_episode_safely)에서 한다. 새 에피소드는 처리 완료 후 다음 접속 때 보인다.
- 저장된 에피소드가 하나도 없는 최초 실행일 때만, 보여줄 것을 만들기 위해 동기로 처리한다.

상태 값:
- "ready": 보여줄 에피소드가 있음
- "error": (최초 실행 한정) RSS·전사·저장 중 실패해서 아직 보여줄 게 없음
- "not_ready": (최초 실행 한정) 오디오가 아직 안 올라온 경우
"""
import threading

from audio import cache_audio
from db import get_client
from episodes import check_new_episode
from expressions_ai import extract_expressions
from save import save_episode, save_expressions
from transcribe import transcribe_from_bytes, transcribe_from_url

# 백그라운드에서 새 에피소드를 처리하는 동안, 다른 요청이 같은 처리를 중복으로 시작하지 않도록 막는다.
_processing_lock = threading.Lock()


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


def _process_new_episode() -> dict:
    """RSS를 확인해서 신규 에피소드가 있으면 다운로드~저장까지 처리한다.

    처리 결과를 상태 dict로 반환한다. 최초 실행(보여줄 캐시가 없을 때)의 동기 처리와
    백그라운드 처리 양쪽에서 공용으로 쓴다.
    """
    check = check_new_episode()

    if not check["is_new"]:
        return {"status": "ready", "episode": check["episode"]}

    rss = check["rss"]
    fallback_episode = check.get("current_displayed_episode")

    try:
        cached_url, audio_bytes = cache_audio(rss["guid"], rss["audio_url"])
    except Exception:
        # 오디오가 아직 안 올라온 경우: 실패가 아니라 "준비 안됨"
        return {"status": "not_ready", "episode": fallback_episode}

    # 방금 다운로드한 바이트가 있으면 재사용하고, 없으면(이미 캐싱돼 있던 경우) URL에서 받는다.
    transcript = (
        transcribe_from_bytes(audio_bytes) if audio_bytes is not None else transcribe_from_url(cached_url)
    )
    expressions = extract_expressions(transcript)

    episode_id = save_episode(rss["guid"], rss["title"], cached_url, transcript)
    save_expressions(episode_id, expressions)

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


def process_new_episode_safely() -> None:
    """백그라운드 실행용: 새 에피소드가 있으면 처리한다. 어떤 예외도 밖으로 던지지 않는다.

    이미 다른 요청이 처리 중이면(락 획득 실패) 조용히 넘어간다 (중복 처리 방지).
    실패해도 조용히 넘어가고, 다음 접속 때 다시 시도된다.
    """
    if not _processing_lock.acquire(blocking=False):
        return
    try:
        _process_new_episode()
    except Exception:
        pass
    finally:
        _processing_lock.release()


def get_episode_status() -> dict:
    """앱 실행 시 호출. 저장된 최신 에피소드를 즉시 반환한다 (RSS 조회로 사용자를 붙잡지 않음).

    새 에피소드 확인·처리는 호출부(main.py)가 응답을 보낸 뒤 백그라운드로 돌린다.
    저장된 에피소드가 하나도 없는 최초 실행일 때만, 보여줄 것을 만들기 위해 동기로 처리한다.
    """
    recent = _get_most_recent_episode()
    if recent is not None:
        return {"status": "ready", "episode": recent}

    # 최초 실행: 아직 보여줄 게 없으니 어쩔 수 없이 동기로 처리한다.
    if not _processing_lock.acquire(blocking=False):
        # 다른 요청이 이미 처리 중이면, 잠시 후 다시 확인하라는 의미로 준비중 상태를 준다.
        return {"status": "not_ready", "episode": None}
    try:
        return _process_new_episode()
    except Exception:
        return {"status": "error", "reason": "rss", "episode": None}
    finally:
        _processing_lock.release()

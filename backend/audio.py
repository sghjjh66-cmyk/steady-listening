"""
에피소드 오디오를 다운로드해서 Supabase Storage에 캐싱하는 모듈.
같은 에피소드를 재다운로드하지 않도록, 이미 캐싱된 파일이 있으면 그대로 재사용한다.
"""
import requests

from db import get_client

BUCKET = "episode-audio"


def _ensure_bucket():
    """오디오 캐시용 Storage 버킷이 없으면 만든다."""
    client = get_client()
    existing = [b.name for b in client.storage.list_buckets()]
    if BUCKET not in existing:
        client.storage.create_bucket(BUCKET, options={"public": True})


def cache_audio(guid: str, audio_url: str) -> tuple[str, bytes | None]:
    """오디오를 다운로드해서 Storage에 캐싱하고 (공개 URL, 새로 받은 원본 바이트)를 반환한다.

    이미 캐싱된 파일이 있으면 재다운로드하지 않고 바이트는 None으로 반환한다
    (백엔드 재배포·재시작에도 캐시가 유지된다는 PRD 요구사항을 만족한다).
    바이트를 함께 돌려주는 이유는, 전사 단계에서 같은 오디오를 또 한 번
    Storage에서 재다운로드하지 않고 재사용하기 위함이다 (메모리·시간 절약).
    """
    _ensure_bucket()
    client = get_client()
    bucket = client.storage.from_(BUCKET)
    storage_path = f"{guid}.mp3"

    if bucket.exists(storage_path):
        return bucket.get_public_url(storage_path), None

    # 기본 User-Agent(python-requests)는 일부 CDN에서 403으로 막혀서 팟캐스트 플레이어처럼 보이는 값으로 바꾼다.
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SteadyListeningBot/1.0)"}
    response = requests.get(audio_url, headers=headers, timeout=60)
    response.raise_for_status()
    bucket.upload(
        storage_path,
        response.content,
        {"content-type": "audio/mpeg"},
    )

    return bucket.get_public_url(storage_path), response.content

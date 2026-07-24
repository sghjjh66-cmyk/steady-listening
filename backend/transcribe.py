"""
faster-whisper(tiny 모델)로 오디오를 전사하는 모듈.
FT.com 공식 스크립트는 구독 로그인이 있어야 열람 가능해서, 직접 전사로 대체한다 (PRD.md 43행).
"""
import os
import tempfile

import requests
from faster_whisper import WhisperModel

_model = None


def _get_model() -> WhisperModel:
    """whisper 모델은 로딩이 오래 걸리므로 한 번만 만들어 재사용한다."""
    global _model
    if _model is None:
        # tiny.en(영어 전용) 모델 사용 — FT 팟캐스트는 항상 영어라 다국어 지원이 필요 없고,
        # Render 무료 플랜(512MB) 메모리 부담을 조금이라도 줄이기 위한 선택.
        _model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    return _model


def transcribe_from_bytes(audio_bytes: bytes) -> str:
    """이미 메모리에 있는 오디오 바이트를 바로 전사한다 (재다운로드 없이).

    beam_size=1(그리디 디코딩)과 vad_filter=True(무음 구간 스킵)로 메모리·연산량을 줄인다
    — Render 무료 플랜에서 전사 중 메모리 부족으로 프로세스가 죽는 문제 대응 (2026-07-24).
    """
    # Windows에서는 파일이 열려 있는 채로 다른 프로세스(av)가 접근하면 PermissionError가 나서,
    # 파일을 닫은 뒤 경로만 넘기고 끝나면 직접 지운다.
    fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    try:
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(audio_bytes)

        model = _get_model()
        segments, _info = model.transcribe(tmp_path, beam_size=1, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments)
    finally:
        os.remove(tmp_path)


def transcribe_from_url(audio_url: str) -> str:
    """공개 오디오 URL을 다운로드해서 전사문 텍스트를 반환한다."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SteadyListeningBot/1.0)"}
    response = requests.get(audio_url, headers=headers, timeout=60)
    response.raise_for_status()
    return transcribe_from_bytes(response.content)

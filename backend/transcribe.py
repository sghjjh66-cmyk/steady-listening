"""
OpenAI Whisper API로 오디오를 전사하는 모듈.
FT.com 공식 스크립트는 구독 로그인이 있어야 열람 가능해서, 직접 전사로 대체한다 (PRD.md 43행).

원래는 faster-whisper로 Render 서버 안에서 직접 전사했으나, Render 무료 플랜(512MB)
메모리로는 전사 도중 프로세스가 종종 죽는 문제가 있었다 (2026-07-24~28). 그래서 전사 자체를
OpenAI의 Whisper API에 맡기도록 바꿨다 (2026-07-28) — Render는 오디오를 API로 보내기만
하면 되고, 무거운 연산은 OpenAI 서버에서 처리되어 메모리 문제가 근본적으로 사라진다.
"""
import os

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def transcribe_from_bytes(audio_bytes: bytes) -> str:
    """이미 메모리에 있는 오디오 바이트를 OpenAI Whisper API로 전사한다 (재다운로드 없이)."""
    client = _get_client()
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=("episode.mp3", audio_bytes),
    )
    return result.text


def transcribe_from_url(audio_url: str) -> str:
    """공개 오디오 URL을 다운로드해서 전사문 텍스트를 반환한다."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SteadyListeningBot/1.0)"}
    response = requests.get(audio_url, headers=headers, timeout=60)
    response.raise_for_status()
    return transcribe_from_bytes(response.content)

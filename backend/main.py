"""
Steady Listening 백엔드 진입점.
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rss import get_latest_episode
from episodes import check_new_episode
from audio import cache_audio
from transcribe import transcribe_from_url
from expressions_ai import extract_expressions
from save import save_episode, save_expressions, get_repeat_counts, get_all_expressions_for_review
from pipeline import get_episode_status
from current_episode import get_current_episode_with_expressions
from session import complete_session, get_all_sessions

APP_SHARED_SECRET = os.environ.get("APP_SHARED_SECRET")
IS_PROD = os.environ.get("ENVIRONMENT") == "production"

# 배포 후 공개 API가 크롤러·링크 미리보기봇 등에 의해 무심코 두드려져
# OpenAI·whisper 비용이 새 나가는 것을 막기 위한 인증 없이 열어둘 경로 목록.
OPEN_PATHS = ("/health", "/docs", "/redoc", "/openapi.json")

app = FastAPI(
    title="Steady Listening API",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

# 프론트엔드 배포 주소를 ALLOWED_ORIGINS 환경변수(쉼표 구분)로 등록한다.
# 로컬 개발 기본값은 Next.js 기본 포트(3000)만 허용.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_app_key(request: Request, call_next):
    """공유 비밀 헤더(X-App-Key)가 없으면 요청을 거절한다 (/health, 문서 경로, CORS 프리플라이트는 예외).

    브라우저의 CORS 프리플라이트(OPTIONS) 요청에는 커스텀 헤더가 실려오지 않으므로,
    여기서 막으면 CORSMiddleware가 응답할 기회조차 없이 401이 먼저 나가 실제 요청이 아예 막힌다.
    """
    if request.method != "OPTIONS" and request.url.path not in OPEN_PATHS:
        if not APP_SHARED_SECRET or request.headers.get("x-app-key") != APP_SHARED_SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.get("/health")
def health_check():
    """서버가 살아있는지 확인하는 헬스체크 엔드포인트."""
    return {"status": "ok"}


@app.get("/episodes/latest-check")
def latest_check():
    """RSS에서 가장 최근 에피소드의 GUID를 확인한다."""
    return get_latest_episode()


@app.get("/episodes/check")
def check_episode():
    """RSS 최신 에피소드가 이미 처리된 것인지(신규가 아닌지) 판별한다."""
    return check_new_episode()


@app.get("/episodes/cache-audio")
def cache_latest_audio():
    """RSS 최신 에피소드의 오디오를 다운로드해서 Storage에 캐싱하고 공개 URL을 돌려준다."""
    latest = get_latest_episode()
    public_url = cache_audio(latest["guid"], latest["audio_url"])
    return {"guid": latest["guid"], "cached_audio_url": public_url}


@app.get("/episodes/transcribe")
def transcribe_latest():
    """RSS 최신 에피소드의 오디오를 faster-whisper(tiny)로 전사한다."""
    latest = get_latest_episode()
    cached_url = cache_audio(latest["guid"], latest["audio_url"])  # Storage 캐시본을 재사용 (원본 CDN 재요청 방지)
    transcript = transcribe_from_url(cached_url)
    return {"guid": latest["guid"], "transcript": transcript}


@app.get("/episodes/extract-expressions")
def extract_latest_expressions():
    """RSS 최신 에피소드를 전사하고, 핵심 표현과 예문을 추출한다."""
    latest = get_latest_episode()
    cached_url = cache_audio(latest["guid"], latest["audio_url"])
    transcript = transcribe_from_url(cached_url)
    expressions = extract_expressions(transcript)
    return {"guid": latest["guid"], "expressions": expressions}


@app.get("/episodes/process")
def process_latest_episode():
    """RSS 최신 에피소드를 확인하고, 신규면 다운로드->전사->추출->저장까지 전체 파이프라인을 실행한다."""
    check = check_new_episode()
    if not check["is_new"]:
        return {"processed": False, "episode": check["episode"]}

    rss = check["rss"]
    cached_url = cache_audio(rss["guid"], rss["audio_url"])
    transcript = transcribe_from_url(cached_url)
    expressions = extract_expressions(transcript)

    episode_id = save_episode(rss["guid"], rss["title"], cached_url, transcript)
    save_expressions(episode_id, expressions)

    return {"processed": True, "episode_id": episode_id, "expression_count": len(expressions)}


@app.get("/expressions/repeat-counts")
def repeat_counts():
    """기본형 기준 반복 등장 횟수를 확인한다 (검증용)."""
    return get_repeat_counts()


@app.get("/episodes/status")
def episode_status():
    """프론트엔드 홈 화면이 앱 실행 시 호출하는 상태 확인 엔드포인트 (ready/error/not_ready)."""
    return get_episode_status()


@app.get("/episodes/current")
def current_episode():
    """학습 화면에서 쓸, 가장 최근 처리된 에피소드와 표현 목록을 반환한다."""
    result = get_current_episode_with_expressions()
    if result is None:
        return {"episode": None, "expressions": []}
    return result


class CompleteRequest(BaseModel):
    mode: str


@app.post("/sessions/complete")
def complete(payload: CompleteRequest):
    """완료 버튼 클릭 시 호출. 오늘 학습 세션을 기록한다 (같은 날 재완료는 최초 모드 유지)."""
    return complete_session(payload.mode)


@app.get("/expressions/review")
def expressions_review():
    """복습 화면에서 쓸, 기본형 기준으로 중복 제거된 전체 표현 목록(반복횟수 포함)을 반환한다."""
    return get_all_expressions_for_review()


@app.get("/sessions/calendar")
def sessions_calendar():
    """달력 화면에서 쓸, 완료 기록 전체(날짜+모드)를 반환한다."""
    return get_all_sessions()

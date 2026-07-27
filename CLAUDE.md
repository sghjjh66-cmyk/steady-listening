# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 현황

PLAN.md 전체 구현 완료 후 배포까지 끝난 상태다 (2026-07-24). `frontend/`(Next.js), `backend/`(FastAPI)
저장소가 모두 존재하고, GitHub 비공개 저장소([sghjjh66-cmyk/steady-listening](https://github.com/sghjjh66-cmyk/steady-listening))에
푸시돼 있으며 Vercel·Render에 배포돼 있다 (아래 "기술 스택" 절의 배포 주소 참고).

두 PRD 문서 사이에 일부 내용이 다르다 (전사 방식, 표현 추출 API). `PRD.md`가 더 나중에 작성된 상세본이고
기술적 제약(FT.com 스크립트는 구독 로그인 필요)에 대한 이유가 명시되어 있으므로, 충돌 시 `PRD.md`를 우선한다.
`prd_lite.md`는 기획 초기 요약본이라 오래된 내용(Anthropic API 등)이 남아있을 수 있어 참고용으로만 본다.

설계 대비 Gap 점검·보안 점검·배포 트러블슈팅 이력은 `CHECK.md`에 정리돼 있다.

## 무엇을 만드는가

Steady Listening — FT News Briefing 팟캐스트로 매일 영어 리스닝 습관을 만드는 1인용 개인 앱.
회원가입/계정 시스템 없음. 프론트엔드는 Vercel 환경변수 `BASIC_AUTH_USER`/`BASIC_AUTH_PASSWORD`로
브라우저 기본 로그인창(Basic Auth, `frontend/src/middleware.ts`)을 걸어 본인만 접근 가능하고,
백엔드는 모든 요청에 공유 비밀 헤더(`APP_SHARED_SECRET`/`X-App-Key`)를 요구해 URL을 알아도 API를 못 두드린다.
자세한 배경·성공 기준은 `PRD.md` 1~3절 참고.

## 기술 스택

- 프론트엔드: Next.js (React), 모바일 우선 (320~430px), 세이지 그린/톤다운 블루 톤
- 백엔드: FastAPI (Python)
- 오디오 전사: OpenAI Whisper API (`whisper-1`) — FT.com 공식 스크립트는 로그인 필요해 자동 수집 불가 → 직접 전사로 대체. 원래 faster-whisper로 Render 서버 안에서 직접 전사했으나 무료 플랜(512MB) 메모리로는 전사 중 프로세스가 종종 죽는 문제가 반복돼서(2026-07-24~28), 전사를 API 호출로 바꿔 Render의 메모리 부담을 없앴다 (2026-07-28)
- 표현/예문 생성: OpenAI API (gpt-4o-mini), 응답은 고정 JSON 스키마로 파싱
- 데이터 저장: Supabase (PostgreSQL) — 로컬 SQLite 사용 금지
- 오디오 캐시: Supabase Storage (백엔드 재배포/재시작에도 유지, 자동 삭제 없음)
- 배포: Vercel(프론트, https://steady-listening.vercel.app) / Render 무료 플랜(백엔드, https://steady-listening-backend.onrender.com) — Render 콜드 스타트로 인한 첫 로딩 지연은 감수. 백엔드는 `render.yaml` 블루프린트로 구성됨

## 핵심 아키텍처 규칙 (여러 파일에 걸쳐 지켜야 하는 것들)

앱 실행 시 백엔드가 RSS(`https://feeds.acast.com/public/shows/73fe3ede-5c5c-4850-96a8-30db8dbae8bf`)를
확인하는 흐름 하나로 신규 에피소드 처리 전체가 트리거된다. 이 파이프라인을 건드릴 때는 다음을 함께 지켜야 한다:

- **멱등성**: RSS GUID로 이미 처리된 에피소드인지 판단하고, 처리된 것이면 다운로드·전사·API 분석을 전부 스킵한다.
- **캐싱 순서**: 오디오는 Supabase Storage에 캐싱 후 재사용 (재다운로드 금지). 신규 에피소드가 없으면 가장 최근 처리본을 계속 보여준다.
- **표현 데이터 모델**: 표현마다 실제 사용형 + 기본형을 함께 저장하고, 반복 등장 횟수는 기본형 기준으로 집계한다. 카테고리(정책·재정/통화·금리/경제지표·시장/무역·외교/기업·AI/인구·사회/불확실성/기타)는 하나만 선택해 저장한다.
- **컨디션 모드(높음/보통/낮음)**는 학습 분량만 다르게 노출할 뿐, 완료 처리 로직은 공통이다: 완료 버튼을 누른 시점의 모드만 기록하고, 같은 날 중복 클릭해도 세션이 중복 기록되지 않아야 한다. "낮음" 모드는 100초 지점에서 자동 정지.
- **장애 처리**: RSS·OpenAI API 실패 시 앱이 멈추지 않고 상단 배너 + 재시도 버튼으로 표시하며, RSS 실패 시에는 이전에 처리된 최신 에피소드를 그대로 보여준다. 공식 스크립트 미게시 상태는 재시도 로직 없이 앱 실행마다 재확인한다.
- **API 키**는 환경변수/설정파일로만 관리 (OpenAI, Supabase 접속 정보).

## 이번 범위에 없는 것 (구현 시 임의로 추가하지 말 것)

받아쓰기(딕테이션), 스피킹/발음 평가, 다른 팟캐스트·언어 확장, 스트릭 게이미피케이션 UI,
오프라인 지원, PWA 홈 화면 추가, 새 에피소드 알림(이메일·푸시). 전체 목록과 사유는 `PRD.md` 6절 참고.

## 빌드·테스트 명령

별도 자동화 테스트(pytest 등)는 없음 — 이 프로젝트는 "작업 절차(검증 루프)"에 따라 실제 브라우저/API 호출로 검증한다.

- 프론트엔드 개발 서버: `cd frontend && npm run dev` (http://localhost:3000)
- 프론트엔드 프로덕션 빌드 확인: `cd frontend && npm run build` (배포 전 반드시 로컬에서 먼저 통과시킬 것 — `next dev`에서는 안 걸리고 빌드에서만 걸리는 TS 에러가 실제로 있었음)
- 백엔드 개발 서버: `cd backend && ./venv/Scripts/python -m uvicorn main:app --port 8000` (http://127.0.0.1:8000, `/health` 확인)
- 백엔드 의존성 설치: `cd backend && ./venv/Scripts/pip install -r requirements.txt`

## 작업 규칙

- 모든 설명과 주석은 한국어로 작성한다.
- 새 파일은 `my-app` 폴더 안에만 만든다.
- 코드를 바꾸면 반드시 무엇을 왜 바꿨는지 한 줄로 알려준다.
- `.env` 등 비밀 정보 파일은 `.gitignore`에 등록해 두고, 절대 커밋하지 않는다.
- 파일을 지워야 할 때는 바로 삭제하지 말고, `trash-can` 폴더를 만들어 그 안으로 옮겨만 둔다. 작업이 끝난 뒤 사용자가 직접 확인하고 삭제한다.
- 이미 설치된 서브에이전트(bkit의 gap-detector 등)는 필요할 때마다 적극 활용한다.

## 반복 방지 규칙 (2026-07-24, 실제로 겪은 문제에서 추가)

- 인증/보안 미들웨어를 추가할 때는 CORS 프리플라이트(OPTIONS 요청)는 항상 예외 처리한다 — 안 그러면 브라우저가 실제 요청조차 못 보내고 조용히 실패한다.
- `.env.example`에는 절대 실제 값을 넣지 않는다 (키 이름만 적고 값은 항상 비움) — 실수로 반복된 적 있음.
- 프론트엔드에서 새 API 호출을 추가할 때는 `frontend/src/lib/api.ts`의 `apiFetch` 헬퍼를 통해서만 한다 (비밀 헤더 자동 첨부됨). 직접 `fetch()`를 쓰지 않는다.
- OpenAI 등 LLM에게 "이 필드엔 마크다운·서식을 넣지 마라"고 프롬프트로 지시해도 지켜지지 않을 수 있다 — 중요한 경우 코드에서 후처리로 확실히 제거/검증한다.
- Supabase 컬럼 추가 마이그레이션은 `alter table ... add column if not exists`로 작성해서, 실수로 두 번 실행해도 에러 없이 안전하게 만든다.

## 작업 절차 (검증 루프)

코드를 바꿀 때는 아래 루프를 통과할 때까지 반복한다.

1. **변경한다** — 계획한 수정을 적용한다.
2. **결과를 직접 확인한다** — 브라우저로 열거나 실행해서 실제로 동작하는지 확인한다. (겉으로 보이는 화면/API가 아니면 실행 로그로 확인한다.)
3. **스스로 코드 리뷰한다** — 바뀐 코드를 다시 읽고 문제(버그, 누락, 규칙 위반)가 없는지 점검한다.
4. **문제가 있으면 고치고 1)로 돌아간다.**
5. **통과하면** 무엇을 왜 바꿨는지 한 줄로 요약한다.

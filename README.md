# Steady Listening

FT News Briefing 팟캐스트로 매일 영어 리스닝 습관을 만드는 1인용 개인 앱.
회원가입/인증 없이, 배포 URL을 비공개로 유지해 접근을 제한한다.

자세한 기획 배경은 [`PRD.md`](PRD.md), 설계는 [`DESIGN.md`](DESIGN.md), 작업 규칙은 [`CLAUDE.md`](CLAUDE.md) 참고.

## 기술 스택

- 프론트엔드: Next.js (App Router, React, Tailwind)
- 백엔드: FastAPI (Python)
- 오디오 전사: faster-whisper `tiny` 모델
- 표현/예문 생성: OpenAI API (gpt-4o-mini)
- 데이터 저장: Supabase (PostgreSQL + Storage)

## 로컬 실행 방법

### 1. 백엔드 (FastAPI)

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows
# source venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
```

`backend/.env.example`을 복사해 `backend/.env`를 만들고 실제 값을 채운다 (커밋 금지):

```
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
APP_SHARED_SECRET=       # 임의의 무작위 문자열
ENVIRONMENT=             # 배포 시 "production", 로컬은 비워둠
```

실행:

```bash
./venv/Scripts/python -m uvicorn main:app --port 8000
```

`http://127.0.0.1:8000/health` 가 `{"status":"ok"}`를 반환하면 정상.

### 2. 프론트엔드 (Next.js)

```bash
cd frontend
npm install
```

`frontend/.env.example`을 복사해 `frontend/.env.local`을 만든다 (커밋 금지):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_KEY=     # 백엔드 APP_SHARED_SECRET과 반드시 같은 값
```

실행:

```bash
npm run dev
```

`http://localhost:3000` 접속.

## 데이터베이스

Supabase 프로젝트에 `backend/supabase_schema.sql`을 SQL Editor에서 실행해 테이블(`episodes`, `expressions`, `sessions`)을 만든다.
이후 스키마 변경분은 `backend/migration_*.sql` 파일들을 순서대로 실행한다 (전부 `add column if not exists` 형태라 두 번 실행해도 안전함).

## 현재 상태

`PLAN.md`의 18단계 구현이 전부 끝났고, `CHECK.md`에 설계 대비 Gap 점검·보안 점검 결과가 정리돼 있다.
배포 전 남은 필수 조치(키 재발급, CORS 프로덕션 주소 설정 등)도 `CHECK.md` 하단 우선순위 목록에 있다.

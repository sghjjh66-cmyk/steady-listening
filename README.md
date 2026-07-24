# Steady Listening

FT News Briefing 팟캐스트로 매일 영어 리스닝 습관을 만드는 1인용 개인 앱.
회원가입/인증 없이, 배포 URL을 비공개로 유지해 접근을 제한한다.

자세한 기획 배경은 [`PRD.md`](PRD.md), 설계는 [`DESIGN.md`](DESIGN.md), 작업 규칙은 [`CLAUDE.md`](CLAUDE.md),
배포·Gap·보안 점검 이력은 [`CHECK.md`](CHECK.md) 참고.

## 배포 주소

- 프론트엔드: https://steady-listening.vercel.app
- 백엔드: https://steady-listening-backend.onrender.com (Render 무료 플랜 — 접속이 뜸하면 잠들어서 첫 로딩이 느릴 수 있음)
- GitHub 저장소: [sghjjh66-cmyk/steady-listening](https://github.com/sghjjh66-cmyk/steady-listening) (비공개)

## 기술 스택

- 프론트엔드: Next.js (App Router, React, Tailwind)
- 백엔드: FastAPI (Python)
- 오디오 전사: faster-whisper `tiny.en` 모델 (영어 전용, `vad_filter=True`)
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
ALLOWED_ORIGINS=         # 프론트엔드 배포 주소 (쉼표로 여러 개 가능). 로컬은 http://localhost:3000
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

## 배포

- **프론트엔드(Vercel)**: `frontend/` 디렉터리를 Vercel 프로젝트로 연결하고, `NEXT_PUBLIC_API_URL`(백엔드 배포 주소)과 `NEXT_PUBLIC_APP_KEY`(백엔드 `APP_SHARED_SECRET`과 동일한 값)를 프로덕션 환경변수로 등록한다.
- **백엔드(Render)**: 저장소 루트의 `render.yaml` 블루프린트를 사용한다. Render 대시보드에서 New + → Blueprint → 이 저장소 선택 → 위 "환경변수" 목록의 값 입력 → 배포. `ALLOWED_ORIGINS`는 Vercel 배포 주소로 설정해야 CORS가 통과한다.
- 두 배포가 서로의 주소를 참조하므로(프론트엔드는 백엔드 URL을, 백엔드는 프론트엔드 URL을 CORS 허용 목록에 필요), 처음 배포할 때는 한쪽을 먼저 올리고 나온 주소를 다른 쪽에 채운 뒤 재배포하는 순서가 된다.

## 현재 상태

`PLAN.md`의 구현이 전부 끝났고 실제로 배포까지 완료됐다 (위 "배포 주소" 참고). `CHECK.md`에 설계 대비 Gap 점검·보안 점검·배포 트러블슈팅 이력이 정리돼 있다.
아직 남은 것: OpenAI·Supabase 키 재발급 권고(대화 중 노출된 이력이 있어 안전을 위해 권장, 미완) — `CHECK.md` 참고.

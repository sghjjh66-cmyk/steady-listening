-- Steady Listening 테이블 설계 (DESIGN.md 데이터 모델 기준)
-- Supabase 대시보드 > SQL Editor 에서 이 파일 전체를 붙여넣고 실행(Run)하면 된다.

-- episodes: RSS로 확인한 에피소드와 처리 결과(오디오 캐시 경로, 전사문)
create table episodes (
  id uuid primary key default gen_random_uuid(),
  guid text unique not null,               -- RSS GUID. 신규 에피소드 여부 판별 기준
  title text not null,
  audio_storage_path text,                 -- Supabase Storage 캐시 경로 (재다운로드 방지)
  transcript text,                         -- faster-whisper 전사문
  processed_at timestamptz not null default now()
);

-- expressions: 에피소드별 핵심 표현과 예문
create table expressions (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid not null references episodes(id) on delete cascade,
  surface_form text not null,              -- 원형(사전형). 과거형/진행형 등 활용형으로 저장하지 않음 (2026-07-23부터)
  surface_form_ko text,                    -- 표현의 한국어 번역 (2026-07-23 추가, 이전 저장분은 NULL)
  usage_note text,                         -- 뜻이 여러 개라 헷갈릴 때만 채우는 짧은 영어 맥락 설명 (2026-07-23 추가)
  related jsonb default '[]'::jsonb,       -- 관련 표현/동의어 목록 (2026-07-23 추가)
  base_form text not null,                 -- surface_form과 동일한 값. 반복 등장 횟수는 이 값 기준으로 집계
  category text not null check (
    category in ('정책·재정', '통화·금리', '경제지표·시장', '무역·외교', '기업·AI', '인구·사회', '불확실성', '기타')
  ),
  examples jsonb not null,                 -- AI가 새로 생성한 예문 2개, 각 {"en": "...", "ko": "..."} (2026-07-23: 3개->2개, 한국어 번역 추가)
  created_at timestamptz not null default now()
);

-- sessions: 하루 학습 완료 기록.
-- session_date를 unique로 두고 서버에서 INSERT ... ON CONFLICT DO NOTHING으로 넣으면
-- 같은 날 재완료 시 최초 완료 시점의 모드가 그대로 유지된다 (DESIGN.md 데이터흐름 B 규칙).
create table sessions (
  id uuid primary key default gen_random_uuid(),
  session_date date unique not null,
  mode text not null check (mode in ('high', 'medium', 'low')),
  completed_at timestamptz not null default now()
);

-- 반복 등장 횟수 집계는 별도 컬럼 없이 base_form 기준 group by로 조회 시점에 계산한다.
-- 예: select base_form, count(*) from expressions group by base_form order by count(*) desc;

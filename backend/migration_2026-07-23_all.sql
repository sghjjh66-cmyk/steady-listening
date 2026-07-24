-- 2026-07-23: expressions 테이블에 한국어 번역·의미 구분·관련 표현 컬럼 추가
-- Supabase 대시보드 > SQL Editor 에서 이 파일 내용을 붙여넣고 실행(Run)하면 된다.
alter table expressions add column if not exists surface_form_ko text;
alter table expressions add column if not exists usage_note text;
alter table expressions add column if not exists related jsonb default '[]'::jsonb;

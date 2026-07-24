"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Expression, ExpressionCard } from "@/components/ExpressionCard";
import { apiFetch } from "@/lib/api";

type Mode = "high" | "medium" | "low";

type Episode = {
  title: string;
  audio_storage_path: string;
  transcript: string;
};

// 컨디션 모드별로 보여줄 표현 개수 (PRD: 높음=10개, 보통=5개, 낮음=1개)
function pickExpressionsForMode(expressions: Expression[], mode: Mode): Expression[] {
  if (mode === "high") return expressions;
  if (mode === "medium") return expressions.slice(0, 5);

  // 낮음 모드의 "오늘의 표현 1개": 반복 등장 횟수가 가장 높은 표현 (동률이면 목록 순서상 첫 번째)
  if (expressions.length === 0) return [];
  return [
    expressions.reduce((best, cur) =>
      (cur.repeat_count ?? 0) > (best.repeat_count ?? 0) ? cur : best
    ),
  ];
}

// 스크립트 원문에서 지금 학습 중인 표현이 등장하는 부분을 강조한다.
// surface_form은 사전형(원형)이라 전사문에 활용형(과거형 등)으로 나온 경우는 못 잡아낸다 —
// 오탐(엉뚱한 단어 강조)보다 일부 놓치는 쪽이 안전해서, 원형 그대로 등장하는 경우만 강조한다.
function renderTranscriptWithHighlights(transcript: string, expressions: Expression[]) {
  const terms = Array.from(new Set(expressions.map((e) => e.surface_form).filter(Boolean))).sort(
    (a, b) => b.length - a.length
  );
  if (terms.length === 0) return transcript;

  const pattern = new RegExp(`(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  const parts = transcript.split(pattern);
  const termSet = new Set(terms.map((t) => t.toLowerCase()));

  return parts.map((part, i) =>
    termSet.has(part.toLowerCase()) ? (
      <span key={i} className="font-semibold text-[#4a7a5a]">
        {part}
      </span>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

function LearnContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = (searchParams.get("mode") as Mode) ?? "medium";

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [expressions, setExpressions] = useState<Expression[]>([]);
  const [completing, setCompleting] = useState(false);
  const [completeDone, setCompleteDone] = useState(false);
  const [completeError, setCompleteError] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  const fetchEpisode = () => {
    setLoadError(false);
    apiFetch("/episodes/current")
      .then((res) => res.json())
      .then((data) => {
        setEpisode(data.episode);
        setExpressions(data.expressions ?? []);
      })
      .catch(() => setLoadError(true));
  };

  useEffect(fetchEpisode, []);

  // 낮음 모드는 100초 지점에서 오디오를 자동으로 정지한다 (PLAN.md 13번).
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || mode !== "low") return;

    const handleTimeUpdate = () => {
      if (audio.currentTime >= 100) {
        audio.pause();
      }
    };
    audio.addEventListener("timeupdate", handleTimeUpdate);
    return () => audio.removeEventListener("timeupdate", handleTimeUpdate);
  }, [mode, episode]);

  // 오디오 재생 진행률에 맞춰, 지금 재생 구간에 해당할 것으로 보이는 표현 카드를 하이라이트한다.
  // (전사문 등장 순서 = 카드 순서라는 점을 이용한 근사치이며, 단어 단위 정밀 동기화는 아니다.)
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleProgress = () => {
      setCurrentTime(audio.currentTime);
      setDuration(audio.duration || 0);
    };
    audio.addEventListener("timeupdate", handleProgress);
    audio.addEventListener("loadedmetadata", handleProgress);
    return () => {
      audio.removeEventListener("timeupdate", handleProgress);
      audio.removeEventListener("loadedmetadata", handleProgress);
    };
  }, [episode]);

  const displayedExpressions = pickExpressionsForMode(expressions, mode);

  const activeIndex =
    duration > 0 && displayedExpressions.length > 0
      ? Math.min(
          displayedExpressions.length - 1,
          Math.floor((currentTime / duration) * displayedExpressions.length)
        )
      : -1;

  const handleComplete = async () => {
    // 중복 클릭 방지: 요청이 끝나기 전까지 버튼을 비활성화한다.
    // (같은 날 재완료는 백엔드의 session_date UNIQUE 제약으로도 한 번 더 막힌다.)
    setCompleting(true);
    setCompleteError(false);
    try {
      const res = await apiFetch("/sessions/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      if (!res.ok) throw new Error("complete failed");
      // 저장됐다는 걸 눈으로 확인할 수 있게 잠깐 보여준 뒤 홈으로 이동한다.
      setCompleteDone(true);
      setTimeout(() => router.push("/"), 900);
    } catch {
      setCompleting(false);
      setCompleteError(true);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center bg-[#f4f7f4] px-6 pb-32 pt-12">
      <div className="flex w-full max-w-sm justify-end">
        <Link href="/" className="text-sm text-zinc-500 underline">
          홈으로
        </Link>
      </div>

      {episode ? (
        <>
          <p className="text-center text-lg font-medium text-zinc-800">{episode.title}</p>
          <audio
            ref={audioRef}
            controls
            controlsList="nodownload"
            disablePictureInPicture
            src={episode.audio_storage_path}
            className="mt-6 w-full max-w-sm"
          />

          {/* 전사 스크립트: 평소엔 접혀 있고 버튼으로 펼쳐서 본다 */}
          <button
            onClick={() => setShowTranscript((v) => !v)}
            className="mt-2 w-full max-w-sm text-left text-sm text-[#4a7a5a] underline"
          >
            {showTranscript ? "스크립트 숨기기" : "스크립트 보기"}
          </button>
          {showTranscript && (
            <div className="mt-2 max-h-64 w-full max-w-sm overflow-y-auto rounded-lg border border-zinc-200 bg-white p-4 text-sm leading-relaxed text-zinc-600">
              {renderTranscriptWithHighlights(episode.transcript, displayedExpressions)}
            </div>
          )}

          {displayedExpressions.length > 0 && (
            <p className="mt-8 w-full max-w-sm text-right text-xs text-zinc-400">
              {Math.max(activeIndex, 0) + 1} / {displayedExpressions.length}
            </p>
          )}

          <div className="mt-2 flex w-full max-w-sm flex-col gap-4">
            {displayedExpressions.map((expr, i) => (
              <ExpressionCard
                key={expr.surface_form}
                expr={expr}
                highlighted={i === activeIndex}
              />
            ))}
          </div>

          <div className="fixed inset-x-0 bottom-0 flex flex-col items-center gap-2 bg-gradient-to-t from-[#f4f7f4] from-60% to-transparent px-6 pb-6 pt-10">
            {completeError && (
              <p className="w-full max-w-sm rounded-lg bg-red-100 px-4 py-2 text-center text-sm text-red-700">
                저장에 실패했습니다. 다시 시도해주세요.
              </p>
            )}
            <button
              onClick={handleComplete}
              disabled={completing || completeDone}
              className="w-full max-w-sm rounded-full bg-[#4a7a5a] py-3 font-medium text-white shadow-lg disabled:opacity-50"
            >
              {completeDone ? "완료 저장됨 ✓" : completing ? "저장 중..." : "완료"}
            </button>
          </div>
        </>
      ) : loadError ? (
        <div className="mt-6 w-full max-w-sm rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700">
          <p>학습 내용을 불러오는 중 문제가 생겼습니다.</p>
          <button onClick={fetchEpisode} className="mt-2 rounded bg-red-600 px-3 py-1 text-white">
            다시 시도
          </button>
        </div>
      ) : (
        <p className="mt-6 text-zinc-500">불러오는 중...</p>
      )}
    </div>
  );
}

export default function LearnPage() {
  return (
    <Suspense>
      <LearnContent />
    </Suspense>
  );
}

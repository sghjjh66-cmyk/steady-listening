"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Mode = "high" | "medium" | "low";

type EpisodeStatus = {
  status: "ready" | "error" | "not_ready";
  reason?: string;
  episode: { title?: string; processed_at?: string } | null;
};

const MODES: { mode: Mode; icon: string; label: string; description: string }[] = [
  { mode: "high", icon: "☀️", label: "높음", description: "전체 듣기 · 표현 10개" },
  { mode: "medium", icon: "⛅", label: "보통", description: "전체 듣기 · 표현 5개" },
  { mode: "low", icon: "🌙", label: "낮음", description: "100초만 듣기 · 표현 1개" },
];

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<EpisodeStatus | null>(null);

  const fetchStatus = () => {
    setLoading(true);
    apiFetch("/episodes/status")
      .then((res) => res.json())
      .then(setData)
      .catch(() => setData({ status: "error", reason: "network", episode: null }))
      .finally(() => setLoading(false));
  };

  useEffect(fetchStatus, []);

  return (
    <div className="flex min-h-screen flex-col items-center bg-[#f4f7f4] px-6 py-12">
      {/* 실패 상태: 배너 + 재시도 버튼 */}
      {data?.status === "error" && (
        <div className="mb-6 w-full max-w-sm rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700">
          <p>에피소드를 불러오는 중 문제가 생겼습니다.</p>
          <button
            onClick={fetchStatus}
            className="mt-2 rounded bg-red-600 px-3 py-1 text-white"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 준비 안됨 상태: 재시도 버튼 없음 */}
      {data?.status === "not_ready" && (
        <div className="mb-6 w-full max-w-sm rounded-lg bg-amber-100 px-4 py-3 text-sm text-amber-800">
          오늘 에피소드가 아직 준비되지 않았습니다.
        </div>
      )}

      <div className="w-full max-w-sm text-center">
        <span className="text-4xl">🎧</span>
        <h1 className="mt-2 text-2xl font-bold text-[#4a7a5a]">Steady Listening</h1>
        <p className="mt-1 text-sm text-zinc-500">매일 조금씩, 영어 리스닝 습관</p>
      </div>

      {loading ? (
        <p className="mt-10 text-zinc-500">불러오는 중...</p>
      ) : (
        <>
          {data?.episode && (
            <div className="mt-8 w-full max-w-sm rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium text-[#4a7a5a]">오늘의 에피소드</p>
              <p className="mt-1 font-medium text-zinc-800">{data.episode.title}</p>
              {data.episode.processed_at && (
                <p className="mt-0.5 text-xs text-zinc-400">
                  {new Date(data.episode.processed_at).toLocaleDateString("ko-KR")}
                </p>
              )}
            </div>
          )}

          <p className="mt-8 w-full max-w-sm text-sm font-medium text-zinc-600">
            오늘 컨디션에 맞게 골라보세요
          </p>

          <div className="mt-3 flex w-full max-w-sm flex-col gap-3">
            {MODES.map(({ mode, icon, label, description }) => (
              <button
                key={mode}
                onClick={() => router.push(`/learn?mode=${mode}`)}
                className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-left shadow-sm transition-colors hover:border-[#4a7a5a] hover:bg-[#f4f9f5]"
              >
                <span className="text-2xl">{icon}</span>
                <span className="flex-1">
                  <span className="block font-semibold text-zinc-800">{label}</span>
                  <span className="block text-xs text-zinc-500">{description}</span>
                </span>
                <span className="text-[#4a7a5a]">→</span>
              </button>
            ))}
          </div>

          <div className="mt-8 flex gap-6">
            <Link
              href="/calendar"
              className="text-sm font-medium text-[#4a7a5a] underline underline-offset-4"
            >
              달력 보기
            </Link>
            <Link
              href="/review"
              className="text-sm font-medium text-[#4a7a5a] underline underline-offset-4"
            >
              지난 표현 복습하러 가기
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

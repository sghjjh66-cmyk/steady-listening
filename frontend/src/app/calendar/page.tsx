"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Session = { session_date: string; mode: string };

const WEEKDAY_LABELS = ["일", "월", "화", "수", "목", "금", "토"];

function toIsoDate(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export default function CalendarPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [viewDate, setViewDate] = useState(() => new Date());
  const [loadError, setLoadError] = useState(false);

  const fetchSessions = () => {
    setLoadError(false);
    apiFetch("/sessions/calendar")
      .then((res) => res.json())
      .then(setSessions)
      .catch(() => setLoadError(true));
  };

  useEffect(fetchSessions, []);

  const sessionDates = new Set(sessions.map((s) => s.session_date));

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth(); // 0-indexed
  const startWeekday = new Date(year, month, 1).getDay(); // 0=일요일
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (number | null)[] = [
    ...Array(startWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  // 목표는 "매일(주말 제외)"이므로, 지난 평일 대비 완료 횟수를 계산한다.
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let weekdayTotal = 0;
  let weekdayCompleted = 0;
  for (let day = 1; day <= daysInMonth; day++) {
    const dateObj = new Date(year, month, day);
    const weekday = dateObj.getDay();
    if (weekday === 0 || weekday === 6) continue; // 주말 제외
    if (dateObj > today) continue; // 아직 오지 않은 날은 통계에서 제외
    weekdayTotal += 1;
    if (sessionDates.has(toIsoDate(year, month, day))) weekdayCompleted += 1;
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-[#f4f7f4] px-6 py-12">
      <div className="flex w-full max-w-sm items-center justify-between">
        <h1 className="text-xl font-semibold text-[#4a7a5a]">달력</h1>
        <Link href="/" className="text-sm text-zinc-500 underline">
          홈으로
        </Link>
      </div>

      <div className="mt-6 flex w-full max-w-sm items-center justify-between">
        <button
          onClick={() => setViewDate(new Date(year, month - 1, 1))}
          className="px-3 py-1 text-lg text-[#4a7a5a]"
        >
          ←
        </button>
        <p className="font-medium text-zinc-700">
          {year}년 {month + 1}월
        </p>
        <button
          onClick={() => setViewDate(new Date(year, month + 1, 1))}
          className="px-3 py-1 text-lg text-[#4a7a5a]"
        >
          →
        </button>
      </div>

      {loadError && (
        <div className="mt-6 w-full max-w-sm rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700">
          <p>완료 기록을 불러오는 중 문제가 생겼습니다.</p>
          <button onClick={fetchSessions} className="mt-2 rounded bg-red-600 px-3 py-1 text-white">
            다시 시도
          </button>
        </div>
      )}

      <div className="mt-4 grid w-full max-w-sm grid-cols-7 gap-1 text-center text-xs">
        {WEEKDAY_LABELS.map((label, i) => (
          <div key={label} className={i === 0 || i === 6 ? "text-zinc-300" : "text-zinc-400"}>
            {label}
          </div>
        ))}
      </div>

      <div className="mt-1 grid w-full max-w-sm grid-cols-7 gap-1">
        {cells.map((day, i) => {
          if (day === null) return <div key={i} />;
          const isWeekend = i % 7 === 0 || i % 7 === 6;
          const completed = sessionDates.has(toIsoDate(year, month, day));
          return (
            <div
              key={i}
              className={`flex aspect-square items-center justify-center rounded-md text-sm ${
                completed
                  ? "bg-[#4a7a5a] font-semibold text-white"
                  : isWeekend
                    ? "text-zinc-300"
                    : "text-zinc-600"
              }`}
            >
              {completed ? "✓" : day}
            </div>
          );
        })}
      </div>

      <p className="mt-6 text-sm text-zinc-500">
        이번 달 평일 완료 {weekdayCompleted} / {weekdayTotal}일
      </p>
    </div>
  );
}

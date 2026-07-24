"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Expression, ExpressionCard } from "@/components/ExpressionCard";
import { apiFetch } from "@/lib/api";

const CATEGORIES = [
  "정책·재정",
  "통화·금리",
  "경제지표·시장",
  "무역·외교",
  "기업·AI",
  "인구·사회",
  "불확실성",
  "기타",
];

export default function ReviewPage() {
  const [expressions, setExpressions] = useState<Expression[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  const fetchExpressions = () => {
    setLoadError(false);
    apiFetch("/expressions/review")
      .then((res) => res.json())
      .then(setExpressions)
      .catch(() => setLoadError(true));
  };

  useEffect(fetchExpressions, []);

  // 카테고리 필터는 이미 받아둔 전체 목록에서 클라이언트가 바로 걸러내므로, 별도 로딩 없이 즉시 갱신된다.
  const filtered = selectedCategory
    ? expressions.filter((e) => e.category === selectedCategory)
    : expressions;

  return (
    <div className="flex min-h-screen flex-col items-center bg-[#f4f7f4] px-6 py-12">
      <div className="flex w-full max-w-sm items-center justify-between">
        <h1 className="text-xl font-semibold text-[#4a7a5a]">복습</h1>
        <Link href="/" className="text-sm text-zinc-500 underline">
          홈으로
        </Link>
      </div>

      <div className="mt-6 flex w-full max-w-sm flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`rounded-full px-3 py-1 text-xs ${
            selectedCategory === null
              ? "bg-[#4a7a5a] text-white"
              : "bg-white text-[#4a7a5a] border border-[#4a7a5a]"
          }`}
        >
          전체
        </button>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`rounded-full px-3 py-1 text-xs ${
              selectedCategory === cat
                ? "bg-[#4a7a5a] text-white"
                : "bg-white text-[#4a7a5a] border border-[#4a7a5a]"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {loadError && (
        <div className="mt-6 w-full max-w-sm rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700">
          <p>표현 목록을 불러오는 중 문제가 생겼습니다.</p>
          <button
            onClick={fetchExpressions}
            className="mt-2 rounded bg-red-600 px-3 py-1 text-white"
          >
            다시 시도
          </button>
        </div>
      )}

      <div className="mt-6 flex w-full max-w-sm flex-col gap-3">
        {loadError ? null : filtered.length === 0 ? (
          <p className="text-center text-sm text-zinc-500">표현이 없습니다.</p>
        ) : (
          filtered.map((expr) => (
            <ExpressionCard key={expr.surface_form} expr={expr} showRepeatCount />
          ))
        )}
      </div>
    </div>
  );
}

export type ExampleSentence = {
  en: string;
  ko: string;
  highlight?: string;
};

export type Expression = {
  surface_form: string;
  surface_form_ko: string | null;
  usage_note?: string | null;
  related?: string[] | null;
  category: string;
  examples: (ExampleSentence | string)[]; // 2026-07-23 이전 데이터는 문자열 배열이었음 (하위 호환)
  repeat_count?: number;
};

// 2026-07-23 이전에 저장된 표현은 examples가 문자열 배열이었다. 두 형태를 모두 지원한다.
function normalizeExample(ex: ExampleSentence | string): ExampleSentence {
  return typeof ex === "string" ? { en: ex, ko: "" } : ex;
}

// 예문 문장에서 highlight 구간을 찾아 강조 색으로 표시한다. 못 찾으면 그냥 원문을 보여준다.
function renderHighlighted(text: string, highlight?: string) {
  if (!highlight) return text;
  const idx = text.toLowerCase().indexOf(highlight.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <span className="font-semibold text-[#4a7a5a]">
        {text.slice(idx, idx + highlight.length)}
      </span>
      {text.slice(idx + highlight.length)}
    </>
  );
}

export function ExpressionCard({
  expr,
  showRepeatCount = false,
  highlighted = false,
}: {
  expr: Expression;
  showRepeatCount?: boolean;
  /** 오디오 재생 중 지금 구간에 해당하는 카드인지 (근사치 — 단어 단위 정밀 동기화는 아님) */
  highlighted?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border bg-white p-5 transition-colors ${
        highlighted ? "border-[#4a7a5a] ring-2 ring-[#4a7a5a]/30" : "border-zinc-200"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-xl font-bold text-[#4a7a5a]">
          {expr.surface_form}
          {highlighted && <span className="ml-2 align-middle text-sm">🔊</span>}
        </h3>
        <div className="flex shrink-0 flex-col items-end gap-0.5 text-right">
          <span className="text-xs text-zinc-300">{expr.category}</span>
          {expr.surface_form_ko && (
            <span className="text-sm text-zinc-400">{expr.surface_form_ko}</span>
          )}
          {showRepeatCount && (
            <span className="text-xs text-zinc-300">{expr.repeat_count ?? 0}회 등장</span>
          )}
        </div>
      </div>

      {expr.related && expr.related.length > 0 && (
        <p className="mt-2 text-sm text-zinc-400">Related expressions: {expr.related.join(", ")}</p>
      )}

      <div className="mt-4 flex flex-col gap-3">
        {expr.examples.map(normalizeExample).map((ex, i) => (
          <div key={i} className="flex gap-2 rounded-lg bg-zinc-50 px-4 py-3">
            <span className="mt-0.5 text-zinc-300">•</span>
            <div>
              <p className="text-zinc-800">{renderHighlighted(ex.en, ex.highlight)}</p>
              {ex.ko && <p className="mt-1 text-sm text-zinc-400">{ex.ko}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

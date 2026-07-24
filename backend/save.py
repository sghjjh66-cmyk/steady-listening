"""
에피소드와 표현을 Supabase에 저장하는 모듈.
반복 등장 횟수는 별도 컬럼 없이, 저장된 표현들을 기본형 기준으로 묶어서 계산한다.
"""
from db import get_client


def save_episode(guid: str, title: str, audio_storage_path: str, transcript: str) -> str:
    """에피소드를 저장하고 새로 생긴 episode id를 반환한다."""
    client = get_client()
    result = (
        client.table("episodes")
        .insert(
            {
                "guid": guid,
                "title": title,
                "audio_storage_path": audio_storage_path,
                "transcript": transcript,
            }
        )
        .execute()
    )
    return result.data[0]["id"]


def save_expressions(episode_id: str, expressions: list[dict]) -> None:
    """표현들을 episode_id와 함께 저장한다.

    surface_form은 이제 항상 원형(사전형)으로 추출되므로, base_form도 같은 값으로 채운다
    (base_form 컬럼은 반복 등장 횟수 집계용으로 계속 사용).
    """
    client = get_client()
    rows = [
        {
            "episode_id": episode_id,
            "surface_form": e["surface_form"],
            "surface_form_ko": e.get("surface_form_ko"),
            "base_form": e["surface_form"],
            "usage_note": e.get("usage_note") or None,
            "related": e.get("related") or [],
            "category": e["category"],
            "examples": e["examples"],
        }
        for e in expressions
    ]
    client.table("expressions").insert(rows).execute()


def get_all_expressions_for_review() -> list[dict]:
    """복습 화면에서 쓸, 저장된 모든 표현을 기본형 기준으로 중복 제거하고 반복 등장 횟수를 붙여 반환한다.

    같은 기본형이 여러 에피소드에 걸쳐 여러 번 저장돼 있어도 한 항목으로 합치고,
    반복 등장 횟수가 많은 순으로 정렬해서 복습 우선순위를 알 수 있게 한다.
    """
    client = get_client()
    rows = (
        client.table("expressions").select("*").order("created_at", desc=True).execute().data
    )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["base_form"]] = counts.get(row["base_form"], 0) + 1

    seen: set[str] = set()
    deduped = []
    for row in rows:  # created_at 내림차순이라, 가장 처음 만나는 게 가장 최근 저장분이다.
        if row["base_form"] in seen:
            continue
        seen.add(row["base_form"])
        row["repeat_count"] = counts[row["base_form"]]
        deduped.append(row)

    deduped.sort(key=lambda e: e["repeat_count"], reverse=True)
    return deduped


def get_repeat_counts() -> list[dict]:
    """기본형(base_form) 기준 반복 등장 횟수를 많은 순으로 반환한다."""
    client = get_client()
    result = client.table("expressions").select("base_form").execute()

    counts: dict[str, int] = {}
    for row in result.data:
        counts[row["base_form"]] = counts.get(row["base_form"], 0) + 1

    return sorted(
        ({"base_form": k, "count": v} for k, v in counts.items()),
        key=lambda item: item["count"],
        reverse=True,
    )

"""
학습 화면에서 쓸, 가장 최근 처리된 에피소드와 그 표현 목록을 함께 조회하는 모듈.
"""
from db import get_client
from save import get_repeat_counts


def get_current_episode_with_expressions() -> dict | None:
    """가장 최근 처리된 에피소드와 그 표현 전체를 반환한다 (모드별 개수 제한은 프론트에서 처리).

    표현마다 기본형 기준 전체 반복 등장 횟수(repeat_count)를 함께 내려줘서,
    낮음 모드의 "오늘의 표현 1개"(반복 최다) 선택을 프론트에서 바로 계산할 수 있게 한다.
    """
    client = get_client()

    episode_result = (
        client.table("episodes").select("*").order("processed_at", desc=True).limit(1).execute()
    )
    if not episode_result.data:
        return None

    episode = episode_result.data[0]
    expressions_result = (
        client.table("expressions")
        .select("*")
        .eq("episode_id", episode["id"])
        .order("created_at")
        .execute()
    )
    expressions = expressions_result.data

    counts = {item["base_form"]: item["count"] for item in get_repeat_counts()}
    for expression in expressions:
        expression["repeat_count"] = counts.get(expression["base_form"], 0)

    return {"episode": episode, "expressions": expressions}

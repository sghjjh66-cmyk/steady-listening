"""
OpenAI API(gpt-4o-mini)로 전사문에서 핵심 표현·예문을 추출하는 모듈.
"""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Supabase expressions 테이블의 category CHECK 제약과 정확히 같은 8개 값이어야 한다.
CATEGORIES = ["정책·재정", "통화·금리", "경제지표·시장", "무역·외교", "기업·AI", "인구·사회", "불확실성", "기타"]

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def extract_expressions(transcript: str) -> list[dict]:
    """전사문에서 핵심 표현을 최대 10개(기준에 맞는 후보가 부족하면 더 적게) 뽑아,
    표현별 원형·카테고리·관련 표현·새 예문 2개(한국어 번역+강조 표시 포함)를 생성한다.

    반환값 형식: [{"surface_form", "surface_form_ko", "category",
                   "related": [...], "examples": [{"en", "ko", "highlight"} x2]}, ...]
    """
    client = _get_client()

    system_prompt = (
        "너는 영어 뉴스 전사문에서 '중상급 이상' 영어 학습자에게 유용한 핵심 표현을 뽑는 도우미다. "
        "반드시 지정된 JSON 스키마로만 응답한다."
    )
    user_prompt = f"""다음 전사문에서 핵심 표현을 최대 10개까지 뽑아라.
아래 기준에 맞는 후보가 10개가 안 되면 그보다 적게 뽑아도 된다 — 기준에 안 맞는 표현을 억지로 채우지 마라.

표현 선정 기준 (모두 지킬 것):
- 대상은 중상급 이상 학습자다. 초보자도 이미 아는 기초 단어·표현(예: rough, keep up, help, big)은 제외한다.
- 아래 유형을 우선한다:
  - 동사+명사구로 이루어진 콜로케이션 (예: raise concerns, tap into reserves)
  - 관용적으로 함께 굳어져 쓰이는 set expression
  - 명사+명사로 이루어진 복합명사 (예: cash burn, regulatory credit, capital expenditure)
  - 외신(해외 뉴스)에서 자주 등장하는 세련되고 격식 있는 표현
- 사람 이름, 회사명, 매체명, 날짜 같은 고유명사는 표현으로 뽑지 않는다.
- 같은 핵심 어근·동사를 공유하는 표현을 중복해서 뽑지 않는다 (예: "tensions escalated"와 "surged since tensions escalated"를 동시에 뽑지 말고 더 유용한 하나만 선택). 뽑는 표현은 서로 겹치지 않는 별개의 표현이어야 한다.
- **surface_form은 반드시 사전에 실릴 원형으로 적는다.** 전사문에 과거형·진행형·수동태 등으로 활용되어 나왔더라도 그대로 옮기지 말고 원형으로 바꿔서 적는다.
  (예: 전사문에 "profits dropped unexpectedly"로 나왔다면 surface_form은 "drop unexpectedly", "scrapped incentives"로 나왔다면 "scrap incentives")
  예문(examples) 안에서는 자연스러운 실제 문장이 되도록 시제를 자유롭게 활용해도 된다 — 원형 제약은 surface_form 필드에만 적용된다.

각 표현마다 아래 항목을 채워라:
- surface_form: 위 원형 규칙을 지킨 표현
- surface_form_ko: surface_form의 자연스러운 한국어 번역(뜻). 뜻이 여러 개면 쉼표로 나열한다. 한자를 섞지 말고 한글로만 작성한다.
- category: 다음 8개 중 가장 관련성 높은 것 하나만 선택. 여러 개에 걸쳐도 하나만 고르고, 어디에도 안 맞으면 "기타"로 분류한다.
  카테고리 목록: {", ".join(CATEGORIES)}
- related: 이 표현과 비슷한 뜻으로 바꿔 쓸 수 있는 관련 표현·동의어를 최소 1개, 가능하면 2~3개 배열로 제공한다. 정말 대체할 표현이 없는 극히 드문 경우에만 빈 배열([])로 둔다.
- examples: 전사문 문장을 그대로 베끼지 말고, 그 표현을 활용해 새로 만든 예문 정확히 2개.
  각 예문은 {{"en": "영어 문장", "ko": "그 문장의 자연스러운 한국어 번역", "highlight": "en 문장 안에서 표현이 실제로 활용된 부분을 en에 등장한 형태 그대로 옮긴 것"}} 형태로 작성한다.
  (예: surface_form이 "settle on"이고 예문이 "The cabinet settled on a compromise."라면 highlight는 "settled on")
  주의: en과 ko 문자열 안에는 별표(*) 1개든 2개든 절대 넣지 않는다. 강조하고 싶은 부분도 en/ko 안에서는 그냥 평범한 글자로 놔둔다. 강조 표시는 오직 highlight 필드 하나로만 전달한다. en/ko에 *가 하나라도 들어가면 잘못된 응답이다.
  한국어 번역은 한자를 섞지 말고 한글로만 작성한다.

JSON 형식으로만 응답:
{{"expressions": [{{"surface_form": "...", "surface_form_ko": "...", "category": "...", "related": ["...", "..."], "examples": [{{"en": "...", "ko": "...", "highlight": "..."}}, {{"en": "...", "ko": "...", "highlight": "..."}}]}}]}}

전사문:
{transcript}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return [_strip_markdown(e) for e in data["expressions"]]


def _strip_markdown(expression: dict) -> dict:
    """모델이 지시를 무시하고 en/ko 문장에 별표(강조 마크다운)를 넣는 경우가 있어, 후처리로 확실히 제거한다."""
    expression["examples"] = [
        {
            **ex,
            "en": ex["en"].replace("*", ""),
            "ko": ex["ko"].replace("*", ""),
            "highlight": ex.get("highlight", "").replace("*", ""),
        }
        for ex in expression["examples"]
    ]
    return expression

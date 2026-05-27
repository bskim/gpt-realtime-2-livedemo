import demo_state


def _check_points(inp: dict) -> str:
    state = demo_state.get()
    cid = inp.get("customer_id", state["customer_id"])
    tier = state["customer_tier"]

    points_map = {
        "vip":     f"[{cid}] 적립 포인트: 25,800P. VIP 등급 혜택: 2배 적립 중. 유효기간: 2025-12-31.",
        "regular": f"[{cid}] 적립 포인트: 8,400P. 유효기간: 2025-12-31.",
    }
    return points_map.get(tier, f"[{cid}] 포인트 정보를 불러올 수 없습니다.")


def _register_membership(inp: dict) -> str:
    state = demo_state.get()
    cid = inp.get("customer_id", state["customer_id"])
    membership_type = inp.get("membership_type", "STANDARD").upper()

    plans = {
        "VIP":      "월 9,900원 / 무료배송 + 2배 포인트 + 전용 CS 라인",
        "PREMIUM":  "월 4,900원 / 무료배송 + 1.5배 포인트",
        "STANDARD": "무료 / 기본 적립 혜택",
    }
    benefits = plans.get(membership_type, "알 수 없는 등급")
    return (
        f"[{cid}] 멤버십 {membership_type} 신청 완료. "
        f"혜택: {benefits}. 다음 주문부터 적용됩니다."
    )


membership_assistant = {
    "id": "Assistant_MembershipAssistant",
    "name": "회원/포인트",
    "description": """Call this if:
        - Customer asks about their points balance or expiry
        - Customer wants to join or upgrade their membership plan
        - Customer asks about membership tier benefits
        DO NOT CALL THIS IF:
        - Customer asks about a specific order, delivery, or refund
        - Customer wants to apply a coupon to an order (route to refund agent)""",
    "system_message": """당신은 회원 및 포인트 관리 전문 상담원입니다.

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 포인트 잔액 및 유효기간을 안내합니다.
    - 멤버십 등급별 혜택을 설명하고 신규 가입 또는 업그레이드를 처리합니다.
    - VIP 고객에게는 전용 혜택을 강조해 안내합니다.

    ## 멤버십 등급
    - STANDARD: 무료 / 기본 적립
    - PREMIUM: 월 4,900원 / 무료배송 + 1.5배 포인트
    - VIP: 월 9,900원 / 무료배송 + 2배 포인트 + 전용 CS
    """,
    "tools": [
        {
            "name": "check_points",
            "description": "고객의 포인트 잔액과 유효기간을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "고객 코드",
                    },
                },
            },
            "returns": lambda inp: _check_points(inp),
        },
        {
            "name": "register_membership",
            "description": "멤버십 신규 가입 또는 등급 업그레이드를 처리합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "고객 코드"},
                    "membership_type": {
                        "type": "string",
                        "description": "멤버십 등급: STANDARD / PREMIUM / VIP",
                    },
                },
            },
            "returns": lambda inp: _register_membership(inp),
        },
    ],
}

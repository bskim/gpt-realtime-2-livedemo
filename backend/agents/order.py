import demo_state


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at", "미확인")
    return oid, oat


def _lookup_order(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]
    tier = state["customer_tier"]

    base = f"[주문번호: {oid} / 주문일시: {oat}]"
    if status == "normal":
        eta = "내일 오후 3시 예정"
        if tier == "vip":
            eta = "오늘 오후 6시 예정 (VIP 당일배송)"
        return f"{base} 정상 처리 중. 배송 예정: {eta}. 상품: 무선 이어폰 1개."
    if status == "delayed":
        return f"{base} 배송 지연 중. 원인: 물류센터 적체. 예상 도착: 2일 후. 불편드려 죄송합니다."
    if status == "lost":
        return f"{base} 배송 분실 접수됨. 담당 물류사 조사 중. 재발송 또는 환불 처리 가능합니다."
    if status == "refund_requested":
        return f"{base} 환불 요청 접수 상태. 검토 중 (영업일 1-3일 소요)."
    return f"{base} 상태를 확인할 수 없습니다."


def _cancel_order(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]
    if status in ("delayed", "lost"):
        return f"[주문번호: {oid} / 주문일시: {oat}] 취소 처리 완료. 결제 금액은 3-5 영업일 내 환불됩니다."
    if status == "refund_requested":
        return f"[주문번호: {oid} / 주문일시: {oat}] 이미 환불 요청 상태입니다. 환불팀으로 연결해드리겠습니다."
    return f"[주문번호: {oid} / 주문일시: {oat}] 취소 처리 완료. 결제 금액은 3-5 영업일 내 환불됩니다."


order_assistant = {
    "id": "Assistant_OrderAssistant",
    "name": "주문 관리",
    "description": """Call this if:
        - Customer wants to check order status
        - Customer wants to change or cancel an order
        - Customer asks about their purchase
        DO NOT CALL THIS IF:
        - Customer asks about delivery address or shipping status
        - Customer asks about refunds or exchanges""",
    "system_message": """당신은 주문 관리 전문 상담원입니다.

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 주문 상태를 조회하고 고객에게 안내합니다.
    - 주문 변경 또는 취소를 처리합니다.
    - 복합 의도(주문변경 + 기타 요청)의 경우 단계적으로 처리합니다.

    ## 주의사항
    - 주문 지연이나 분실 건에는 먼저 공감 표현 후 해결책을 안내하세요.
    - 세션 컨텍스트에 최근 주문번호/주문일시가 있으면 이를 기본 주문으로 바로 안내하고, 없을 때만 주문번호를 요청하세요.
    """,
    "tools": [
        {
            "name": "lookup_order",
            "description": "주문 상태 및 상세 정보를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "주문 번호 또는 고객 코드",
                    },
                },
            },
            "returns": lambda inp: _lookup_order(inp),
        },
        {
            "name": "cancel_order",
            "description": "주문을 취소하고 환불을 접수합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                    "reason": {"type": "string", "description": "취소 사유"},
                },
            },
            "returns": lambda inp: _cancel_order(inp),
        },
    ],
}

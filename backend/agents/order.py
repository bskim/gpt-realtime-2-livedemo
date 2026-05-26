import demo_state


def _lookup_order(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    status = state["order_status"]
    tier = state["customer_tier"]

    base = f"[주문번호: {oid}]"
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
    oid = inp.get("order_id", state["customer_id"])
    status = state["order_status"]
    if status in ("delayed", "lost"):
        return f"[주문번호: {oid}] 취소 처리 완료. 결제 금액은 3-5 영업일 내 환불됩니다."
    if status == "refund_requested":
        return f"[주문번호: {oid}] 이미 환불 요청 상태입니다. 환불팀으로 연결해드리겠습니다."
    return f"[주문번호: {oid}] 취소 처리 완료. 결제 금액은 3-5 영업일 내 환불됩니다."


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
    Keep sentences short and simple, suitable for a voice conversation. Use polite Korean (존댓말).

    Your tasks are:
    - 주문 상태를 조회하고 고객에게 안내합니다.
    - 주문 변경 또는 취소를 처리합니다.
    - 복합 의도(주문변경 + 기타 요청)의 경우 단계적으로 처리합니다.

    Make sure to be empathetic and professional, especially for delayed or lost orders.
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

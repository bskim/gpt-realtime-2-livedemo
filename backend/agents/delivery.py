import demo_state


def _lookup_delivery(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    status = state["order_status"]
    tier = state["customer_tier"]

    if status == "normal":
        eta = "내일 오후 3시"
        if tier == "vip":
            eta = "오늘 오후 6시 (VIP 당일배송)"
        return f"[주문번호: {oid}] 배송 중. 현재 위치: 서울 물류센터 출발. 예상 도착: {eta}."
    if status == "delayed":
        return (
            f"[주문번호: {oid}] 배송 지연 발생. 원인: 연휴 물류 적체. "
            "예상 도착: 2일 후. 배송지 변경은 오늘 오후 5시까지 가능합니다."
        )
    if status == "lost":
        return f"[주문번호: {oid}] 배송 분실 신고 접수됨. 물류사 조사 중 (1-2 영업일)."
    return f"[주문번호: {oid}] 배송 정보를 확인할 수 없습니다. 주문팀으로 연결해드리겠습니다."


def _update_address(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    new_addr = inp.get("new_address", "")
    status = state["order_status"]

    if status == "delayed":
        return (
            f"[주문번호: {oid}] 배송지 변경 처리됨: '{new_addr}'. "
            "변경된 주소로 재배송됩니다. 1-2 영업일 추가 소요됩니다."
        )
    if status in ("lost",):
        return f"[주문번호: {oid}] 현재 배송 분실 처리 중으로 주소 변경이 불가합니다. 재발송 시 주소를 업데이트하겠습니다."
    return f"[주문번호: {oid}] 배송지 변경 완료: '{new_addr}'. 다음 발송부터 적용됩니다."


delivery_assistant = {
    "id": "Assistant_DeliveryAssistant",
    "name": "배송 관리",
    "description": """Call this if:
        - Customer asks about delivery status or tracking
        - Customer wants to change delivery address
        - Customer reports delayed or missing delivery
        DO NOT CALL THIS IF:
        - Customer asks about order contents or order cancellation
        - Customer asks about refunds""",
    "system_message": """당신은 배송 관리 전문 상담원입니다.
    Keep sentences short and simple, suitable for a voice conversation. Use polite Korean (존댓말).

    Your tasks are:
    - 배송 현황을 조회하고 고객에게 안내합니다.
    - 배송지 변경 요청을 처리합니다.
    - 배송 지연 또는 분실 시 공감하며 해결책을 안내합니다.

    IMPORTANT: For delayed or lost deliveries, always acknowledge the customer's frustration first,
    then provide the solution. Use empathetic language.
    """,
    "tools": [
        {
            "name": "lookup_delivery",
            "description": "배송 현황 및 예상 도착 시간을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                },
            },
            "returns": lambda inp: _lookup_delivery(inp),
        },
        {
            "name": "update_address",
            "description": "배송지 주소를 변경합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                    "new_address": {"type": "string", "description": "새 배송지 주소"},
                },
            },
            "returns": lambda inp: _update_address(inp),
        },
    ],
}

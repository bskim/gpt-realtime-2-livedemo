import demo_state


def _report_defect(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    description = inp.get("description", "불량 내용 미입력")
    tier = state["customer_tier"]

    ticket_id = f"AS-{oid[-4:]}-{abs(hash(description)) % 10000:04d}"
    priority = "긴급 처리" if tier in ("vip", "urgent") else "일반 처리"
    return (
        f"[{ticket_id}] A/S 접수 완료. {priority}. 증상: {description}. "
        "담당 기사 배정 후 영업일 1-2일 내 연락드립니다."
    )


def _check_warranty(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    status = state["order_status"]

    if status == "refund_requested":
        return (
            f"[주문번호: {oid}] 해당 상품은 환불 요청 상태입니다. "
            "환불팀과 연계하여 처리해드리겠습니다."
        )
    return (
        f"[주문번호: {oid}] 보증 기간: 구매일로부터 1년. "
        "현재 보증 기간 내. 무상 수리 또는 교환 가능합니다."
    )


afterservice_assistant = {
    "id": "Assistant_AfterServiceAssistant",
    "name": "A/S 불량",
    "description": """Call this if:
        - Customer reports a defective, broken, or damaged product
        - Customer wants to check warranty coverage or status
        - Customer needs product repair or replacement due to a defect
        DO NOT CALL THIS IF:
        - Customer wants a refund for a non-defective item (route to refund agent)
        - Customer asks about delivery status""",
    "system_message": """당신은 A/S 및 상품 불량 처리 전문 상담원입니다.
    Keep sentences short and simple, suitable for a voice conversation. Use polite Korean (존댓말).

    Your tasks are:
    - 상품 불량 증상을 접수하고 A/S 티켓을 발행합니다.
    - 보증 기간 및 무상 수리 가능 여부를 안내합니다.
    - VIP / 긴급 고객은 우선 처리합니다.

    IMPORTANT:
    - Always empathize with the customer's inconvenience before proceeding.
    - Ask for order number and defect description before processing.
    - If warranty has expired, offer paid repair options.
    """,
    "tools": [
        {
            "name": "report_defect",
            "description": "상품 불량/파손을 접수하고 A/S 티켓을 발행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                    "description": {
                        "type": "string",
                        "description": "불량 증상 설명",
                    },
                },
            },
            "returns": lambda inp: _report_defect(inp),
        },
        {
            "name": "check_warranty",
            "description": "보증 기간 및 무상 수리 가능 여부를 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                },
            },
            "returns": lambda inp: _check_warranty(inp),
        },
    ],
}

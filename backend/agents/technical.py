import demo_state


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at", "미확인")
    return oid, oat


def _report_defect(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    description = inp.get("description", "불량 내용 미입력")
    tier = state["customer_tier"]
    tone = state.get("request_tone", "normal")

    ticket_id = f"AS-{oid[-4:]}-{abs(hash(description)) % 10000:04d}"
    priority = "긴급 처리" if tier == "vip" or tone == "urgent" else "일반 처리"
    return (
        f"[{ticket_id}] A/S 접수 완료. {priority}. 주문번호: {oid} / 주문일시: {oat}. 증상: {description}. "
        "담당 기사 배정 후 영업일 1-2일 내 연락드립니다."
    )


def _check_warranty(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]

    if status == "refund_requested":
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 해당 상품은 환불 요청 상태입니다. "
            "환불팀과 연계하여 처리해드리겠습니다."
        )
    return (
        f"[주문번호: {oid} / 주문일시: {oat}] 보증 기간: 구매일로부터 1년. "
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

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 상품 불량 증상을 접수하고 A/S 티켓을 발행합니다.
    - 보증 기간 및 무상 수리 가능 여부를 안내합니다.
    - VIP / 긴급 고객은 우선 처리합니다.

    ## 주의사항
    - 불편 사항에 먼저 공감 표현 후 접수를 진행하세요.
    - 세션 컨텍스트에 최근 주문번호/주문일시가 있으면 이를 기본 주문으로 바로 안내하고, 없을 때만 주문번호를 요청하세요.
    - 보증 기간 만료 시 유상 수리 옵션을 안내하세요.
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

import demo_state


def _process_refund(inp: dict) -> str:
    state = demo_state.get()
    oid = inp.get("order_id", state["customer_id"])
    reason = inp.get("reason", "고객 요청")
    tier = state["customer_tier"]
    status = state["order_status"]

    if tier == "vip":
        return (
            f"[주문번호: {oid}] VIP 고객 환불 즉시 승인. 사유: {reason}. "
            "결제 금액 전액이 1 영업일 내 환불됩니다. 반송 택배 무료 제공."
        )
    if status == "lost":
        return (
            f"[주문번호: {oid}] 분실 건 환불 처리 완료. 사유: 배송 분실. "
            "결제 금액 전액 환불 + 보상 쿠폰 5,000원 지급 예정."
        )
    return (
        f"[주문번호: {oid}] 환불 접수 완료. 사유: {reason}. "
        "반품 운송장 번호를 문자로 발송합니다. 확인 후 3-5 영업일 내 환불됩니다."
    )


def _apply_coupon(inp: dict) -> str:
    state = demo_state.get()
    code = inp.get("coupon_code", "")
    oid = inp.get("order_id", state["customer_id"])
    has_coupon = state["has_coupon"]

    if not has_coupon:
        return f"[주문번호: {oid}] 쿠폰 코드 '{code}'는 유효하지 않거나 이미 사용된 코드입니다."
    return (
        f"[주문번호: {oid}] 쿠폰 '{code}' 적용 완료. "
        "할인 금액: 5,000원. 다음 주문에 자동 적용됩니다."
    )


refund_assistant = {
    "id": "Assistant_RefundAssistant",
    "name": "환불/교환",
    "description": """Call this if:
        - Customer wants to request a refund or exchange
        - Customer wants to apply a coupon or discount
        - Customer has a complaint about a product
        DO NOT CALL THIS IF:
        - Customer asks about delivery status
        - Customer asks about order status only""",
    "system_message": """당신은 환불·교환 전문 상담원입니다.
    Keep sentences short and simple, suitable for a voice conversation. Use polite Korean (존댓말).

    Your tasks are:
    - 환불 또는 교환 요청을 접수하고 처리합니다.
    - 쿠폰 적용 요청을 처리합니다.
    - 고객의 불만 사항에 공감하며 최선의 해결책을 안내합니다.

    IMPORTANT:
    - Always empathize with the customer first before providing solutions.
    - For VIP customers, offer expedited processing.
    - Confirm customer's identity (full name) before processing refunds.
    """,
    "tools": [
        {
            "name": "process_refund",
            "description": "환불 또는 교환 요청을 접수하고 처리합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                    "reason": {"type": "string", "description": "환불/교환 사유"},
                    "type": {
                        "type": "string",
                        "description": "refund 또는 exchange",
                    },
                },
            },
            "returns": lambda inp: _process_refund(inp),
        },
        {
            "name": "apply_coupon",
            "description": "쿠폰 코드를 적용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "주문 번호"},
                    "coupon_code": {"type": "string", "description": "쿠폰 코드"},
                },
            },
            "returns": lambda inp: _apply_coupon(inp),
        },
    ],
}

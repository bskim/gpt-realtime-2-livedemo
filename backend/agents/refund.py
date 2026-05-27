import demo_state
from datetime import datetime


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at", "미확인")
    return oid, oat


def _days_since_order(order_at: str) -> int | None:
    try:
        dt = datetime.strptime(order_at.replace(" KST", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return None
    delta_days = (datetime.now() - dt).days
    return max(delta_days, 0)


def _process_refund(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    reason = inp.get("reason", "고객 요청")
    reason_lower = reason.lower()
    tier = state["customer_tier"]
    status = state["order_status"]
    days_since = _days_since_order(oat)

    # Structured hints from upstream workflow/tool routing for deterministic branching.
    repeat_count = inp.get("repeat_count")
    if not isinstance(repeat_count, int):
        try:
            repeat_count = int(repeat_count) if repeat_count is not None else 0
        except Exception:
            repeat_count = 0
    seller_fault = bool(inp.get("seller_fault", False))
    history = inp.get("order_status_history")
    history_text = " ".join(str(x).lower() for x in history) if isinstance(history, list) else ""

    auto_comp = days_since is not None and days_since >= 3
    repeated_issue = (
        repeat_count >= 2
        or seller_fault
        or any(k in reason_lower for k in ("반복", "재차", "계속", "repeated", "again", "품절", "취소"))
        or any(k in history_text for k in ("delayed", "cancelled", "품절", "취소", "배송준비"))
    )
    severe_delay = (
        (days_since is not None and days_since >= 14)
        or any(k in reason_lower for k in ("2주", "14일"))
        or any(k in history_text for k in ("14", "2주"))
    )
    damage_signal = any(k in reason_lower for k in ("파손", "깨", "불량", "손상", "broken", "damaged"))
    asks_extra_comp = any(k in reason_lower for k in ("보상", "쿠폰", "compensation"))
    vip_discretionary_comp = tier == "vip" and (
        severe_delay or repeated_issue or damage_signal or status in ("lost",) or asks_extra_comp
    )
    regular_discretionary_comp = tier == "regular" and seller_fault and repeated_issue

    if vip_discretionary_comp:
        elapsed = f"주문일 기준 {days_since}일 경과" if days_since is not None else "장기/반복 이슈 기준"
        repeat_notice = (
            f"확인해보니 최근 문제가 {repeat_count}회 반복된 것으로 확인되어 추가 보상 요건을 충족합니다. "
            if repeat_count >= 2
            else "확인해보니 최근 반복/지연 이슈가 확인되어 추가 보상 요건을 충족합니다. "
        )
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] VIP 우선 환불 접수 완료. 사유: {reason}. "
            f"{repeat_notice}{elapsed} 또는 품질 이슈가 확인되어 에이전트 자율 보상 10,000원 쿠폰 추가 제공을 결정했습니다. "
            "환불은 1영업일 내 우선 처리되며, 추가 보상 쿠폰은 계정에 순차 반영됩니다."
        )

    if regular_discretionary_comp:
        elapsed = f"주문일 기준 {days_since}일 경과" if days_since is not None else "반복 이슈 기준"
        repeat_notice = (
            f"확인해보니 최근 문제가 {repeat_count}회 반복된 것으로 확인되어 추가 보상 요건을 충족합니다. "
            if repeat_count >= 2
            else "확인해보니 최근 반복 이슈가 확인되어 추가 보상 요건을 충족합니다. "
        )
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 일반 고객 환불 접수 완료. 사유: {reason}. "
            f"{repeat_notice}판매자 책임 반복 이슈({elapsed})가 확인되어 에이전트 재량 보상 5,000원 쿠폰 추가 제공을 결정했습니다. "
            "환불은 기준 일정에 따라 진행되며, 추가 보상 쿠폰은 계정에 순차 반영됩니다."
        )

    if tier == "vip":
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] VIP 고객 환불 즉시 승인. 사유: {reason}. "
            "결제 금액 전액이 1 영업일 내 환불됩니다. 반송 택배 무료 제공."
        )
    if status == "lost":
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 분실 건 환불 처리 완료. 사유: 배송 분실. "
            "결제 금액 전액 환불 + 보상 쿠폰 5,000원 지급 예정."
        )
    if auto_comp or status == "delayed" or any(k in reason_lower for k in ("지연", "늦", "delay", "late")):
        elapsed = f"주문일 기준 {days_since}일 경과" if days_since is not None else "주문일 기준 3일 이상 지연 기준"
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 배송 지연 건으로 환불/보상 기준을 안내드립니다. 사유: {reason}. "
            f"{elapsed}로 배송비 상당 3,000원 보상 쿠폰이 자동 지급됩니다. "
            "환불이 필요하면 즉시 환불 접수로 진행하겠습니다."
        )
    return (
        f"[주문번호: {oid} / 주문일시: {oat}] 환불 접수 완료. 사유: {reason}. "
        "반품 운송장 번호를 문자로 발송합니다. 확인 후 3-5 영업일 내 환불됩니다."
    )


def _apply_coupon(inp: dict) -> str:
    state = demo_state.get()
    code = inp.get("coupon_code", "")
    oid, oat = _resolved_order(state, inp)
    has_coupon = state["has_coupon"]

    if not has_coupon:
        return f"[주문번호: {oid} / 주문일시: {oat}] 쿠폰 코드 '{code}'는 유효하지 않거나 이미 사용된 코드입니다."
    return (
        f"[주문번호: {oid} / 주문일시: {oat}] 쿠폰 '{code}' 적용 완료. "
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

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 환불 또는 교환 요청을 접수하고 처리합니다.
    - 쿠폰 적용 요청을 처리합니다.
    - 고객의 불만 사항에 공감하며 최선의 해결책을 안내합니다.
    - 배송 지연 보상 문의 시 정형 정책 기준을 먼저 명확하게 안내합니다.

    ## 주의사항
    - 해결책을 제시하기 전에 먼저 고객에게 공감하세요.
    - VIP 고객은 우선 처리(즉시 승인)를 안내하세요.
    - 세션 컨텍스트에 최근 주문번호/주문일시가 있으면 이를 기본 주문으로 바로 안내하고, 없을 때만 주문번호를 요청하세요.
    - 정책 기준이 충족되면 다른 에이전트로 재전환하지 말고 현재 응답에서 기준과 보상 금액을 바로 안내하세요.
    - 데모 정책: 주문일 기준 3일 이상 경과 건은 배송비 상당 3,000원 쿠폰을 자동 지급합니다.
    - VIP 고객은 과도한 지연(예: 14일 이상), 반복 지연/반복 품절취소, 파손/불량 이슈가 감지되면 에이전트 자율 보상 10,000원 쿠폰을 선제적으로 안내할 수 있습니다.
    - 일반 고객도 판매자 책임(seller_fault=true) + 반복 이슈(repeat_count>=2 등) 조건이면 에이전트 재량으로 5,000원 추가 보상을 안내할 수 있습니다.
    - `process_refund` 호출 시 `repeat_count`, `seller_fault`, `order_status_history`가 제공되면 이를 우선 사용해 보상 분기를 결정하세요.
    - 고객이 상담원 연결을 요청하면 거절하지 말고 `request_human_followup` function을 호출해 연락 접수를 진행하세요.
    - "담당 부서 연결", "정책 확인 후 안내"처럼 연결/대기 안내만 하고 끝내지 마세요.
    - 보상 문의가 들어오면 최소 1회는 기준(3일), 보상 방식(쿠폰), 금액(3,000원)을 한 문장 안에 명시하세요.
    - 현재 세션 컨텍스트(주문번호/주문일시/상태)를 최우선으로 활용해 답변하세요.
    - 다만 환불/교환 접수에 필수인 정보(예: 파손 부위, 수량)가 없을 때만, 최소 질문 1개로 추가 정보를 요청하세요.
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
                    "repeat_count": {
                        "type": "integer",
                        "description": "동일 이슈 반복 횟수(예: 판매자 품절취소 반복)",
                    },
                    "seller_fault": {
                        "type": "boolean",
                        "description": "판매자 책임 사유(재고 오판매 등) 여부",
                    },
                    "order_status_history": {
                        "type": "array",
                        "description": "주문 상태 이력(예: ['배송준비','품절취소','재주문','배송지연'])",
                        "items": {"type": "string"},
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

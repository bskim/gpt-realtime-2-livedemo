import demo_state
from datetime import datetime


def _resolved_order(state: dict, inp: dict) -> tuple[str, str]:
    oid = inp.get("order_id") or state.get("recent_order_id") or state["customer_id"]
    oat = state.get("recent_order_at", "미확인")
    return oid, oat


def _days_since_order(order_at: str) -> int | None:
    # Expected demo format: "YYYY-MM-DD HH:mm KST"
    try:
        dt = datetime.strptime(order_at.replace(" KST", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return None
    delta_days = (datetime.now() - dt).days
    return max(delta_days, 0)


def _lookup_delivery(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    status = state["order_status"]
    tier = state["customer_tier"]
    days_since = _days_since_order(oat)
    auto_comp = days_since is not None and days_since >= 3

    if auto_comp:
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 주문일 기준 {days_since}일 경과로 지연 보상 대상입니다. "
            "배송비 상당 3,000원 쿠폰이 자동 지급됩니다. "
            "현재 배송 상태 확인과 별도로 보상은 즉시 적용됩니다."
        )

    if status == "normal":
        eta = "내일 오후 3시"
        if tier == "vip":
            eta = "오늘 오후 6시 (VIP 당일배송)"
        return f"[주문번호: {oid} / 주문일시: {oat}] 배송 중. 현재 위치: 서울 물류센터 출발. 예상 도착: {eta}."
    if status == "delayed":
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 배송 지연 발생. 원인: 연휴 물류 적체. "
            "예상 도착: 2일 후. 배송지 변경은 오늘 오후 5시까지 가능합니다. "
            "정책 기준(3일 이상 지연) 충족 건으로 배송비 상당 3,000원 보상 쿠폰이 자동 지급됩니다."
        )
    if status == "lost":
        return f"[주문번호: {oid} / 주문일시: {oat}] 배송 분실 신고 접수됨. 물류사 조사 중 (1-2 영업일)."
    return f"[주문번호: {oid} / 주문일시: {oat}] 배송 정보를 확인할 수 없습니다. 주문팀으로 연결해드리겠습니다."


def _update_address(inp: dict) -> str:
    state = demo_state.get()
    oid, oat = _resolved_order(state, inp)
    new_addr = str(inp.get("new_address", "")).strip()
    customer_confirmed = bool(inp.get("customer_confirmed", False))
    status = state["order_status"]

    if not new_addr or len(new_addr) < 5:
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 배송지 변경 전 새 배송지를 정확히 확인해야 합니다. "
            "변경할 주소를 정확히 말씀해 주세요."
        )

    if not customer_confirmed:
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 고객 확인 전 단계입니다. "
            f"요청 주소('{new_addr}')로 진행해도 되는지 고객의 명시 확인 후 다시 처리하겠습니다."
        )

    if status == "delayed":
        return (
            f"[주문번호: {oid} / 주문일시: {oat}] 배송지 변경 요청이 접수되었습니다: '{new_addr}'. "
            "출고/재배송 단계 확인 후 반영 결과를 안내드리며, 1-2 영업일 추가 소요될 수 있습니다."
        )
    if status in ("lost",):
        return f"[주문번호: {oid} / 주문일시: {oat}] 현재 배송 분실 처리 중으로 주소 변경이 불가합니다. 재발송 시 주소를 업데이트하겠습니다."
    return (
        f"[주문번호: {oid} / 주문일시: {oat}] 배송지 변경 요청이 접수되었습니다: '{new_addr}'. "
        "이미 출고된 경우 반영 여부가 달라질 수 있어 최종 반영 결과를 확인 후 안내드립니다."
    )


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

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 배송 현황을 조회하고 고객에게 안내합니다.
    - 배송지 변경 요청을 처리합니다.
    - 배송 지연 또는 분실 시 공감하며 해결책을 안내합니다.
    - 정형 정책 기준을 충족하면(예: 3일 이상 배송 지연) 보상 기준을 즉시 안내합니다.
    - 고객이 추가 보상/쿠폰 증액/반복 이슈 보상을 요구하면 환불·보상 전문 에이전트(`Assistant_RefundAssistant`)로 즉시 전환해 처리합니다.

    ## 주의사항
    - 배송 지연이나 분실 건에는 반드시 고객의 불편함에 먼저 공감한 후 해결책을 안내하세요.
    - 세션 컨텍스트에 최근 주문번호/주문일시가 있으면 이를 기본 주문으로 바로 안내하고, 없을 때만 주문번호를 요청하세요.
    - 정책 기준이 충족된 경우에는 반복 라우팅하지 말고 보상 기준을 명확히 안내하세요.
    - 데모 정책: 주문일 기준 3일 이상 경과 건은 배송비 상당 3,000원 쿠폰을 자동 지급합니다.
    - 보상 문의를 받았을 때 "담당 부서 연결"로만 응답하지 말고, 최소한 정책 기준과 금액은 현재 응답에서 먼저 안내하세요.
    - 고객이 "상담원 연결", "담당자 연락"을 명시적으로 요청하기 전에는 `request_human_followup`를 먼저 호출하지 마세요.
    - 추가 보상 요구(예: 자동보상으로 부족, 반복 이슈 다회, 판매자 품절취소 반복)가 들어오면 `Assistant_RefundAssistant` 전환을 우선하세요.
    - 현재 세션 컨텍스트(주문번호/주문일시/상태)를 최우선으로 활용해 답변하세요.
    - 배송지 변경 요청은 고객이 새 주소를 직접 말한 경우에만 진행하세요. 주소가 없으면 반드시 주소를 먼저 질문하세요.
    - `update_address` 호출 시 `customer_confirmed=true`가 없으면 확정 처리하지 마세요. 확인 전에는 접수/확인 단계로 안내하세요.
    - 사용자가 말하지 않은 임의 주소(예시값)를 넣어 처리하지 마세요.
    - 다만 제품 파손 상태 확인처럼 해결에 필수인 정보가 없을 때만, 최소 질문 1개로 추가 정보를 요청하세요.
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
                    "customer_confirmed": {
                        "type": "boolean",
                        "description": "고객이 해당 주소로 진행을 명시적으로 확인했는지 여부",
                    },
                },
            },
            "returns": lambda inp: _update_address(inp),
        },
    ],
}

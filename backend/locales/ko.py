"""i18n string table — Korean (default)."""

STRINGS: dict = {
    # ── AssistantService / language tag for agent system_message ──
    "assistant.language": "Korean",
    # ── Azure realtime session input transcription language code ──
    "realtime.transcription_language": "ko",
    # ── Forced closing line on user end-gesture ──
    "realtime.forced_closing_line": "문의 주셔서 감사합니다. 상담을 마무리하겠습니다.",
    # End-of-session detection regex patterns (list of regex strings).
    "realtime.end_session_patterns": [
        r"감사(합니다|해요|해)",
        r"이제\s*됐(어요|습니다)",
        r"괜찮(아요|습니다)",
        r"더\s*상담\s*(필요\s*없|안\s*해)",
        r"그만\s*할게",
        r"종료\s*할게",
        r"여기까지\s*할게",
        r"연락\s*기다리겠습니다",
        r"기다릴게요",
        r"확인해\s*보고.*다시\s*연락드릴게요",
        r"문제\s*있으면.*다시\s*연락드릴게요",
        r"알겠습니다.*다시\s*연락드릴게요",
        r"수고\s*하세요",
        r"고맙습니다",
    ],
    "realtime.forced_closing_instruction": "고객이 상담 종료 의사를 밝혔습니다. 다음 한 문장만 응답하세요: '{line}'",
    "realtime.auto_end_reason": "고객 종료 의사 감지",

    # ── Labels for state values ──
    "label.tier.vip": "VIP",
    "label.tier.regular": "일반",
    "label.tone.normal": "일반",
    "label.tone.urgent": "긴급",
    "label.tone.complaint": "불만",
    "label.order.normal": "정상",
    "label.order.delayed": "배송 지연 중",
    "label.order.lost": "배송 분실",
    "label.order.refund_requested": "환불 요청 중",
    "label.inquiry.simple": "단순 문의",
    "label.inquiry.complex": "복합 의도",
    "label.inquiry.ambiguous": "모호 요청",
    "label.workflow.unresolved": "사전 Workflow 미처리(Fallback)",
    "label.workflow.resolved": "Workflow 처리 가능",
    "label.yes": "예",
    "label.no": "아니오",
    "label.has": "있음",
    "label.has_not": "없음",
    "label.unknown": "미확인",
    "label.none": "없음",

    # ── Demo presets ──
    "preset.S1.label": "S1 단순 FAQ",
    "preset.S2.label": "S2 복합 의도",
    "preset.S3.label": "S3 불만 고객",
    "preset.S4.label": "S4 모호 요청",
    "preset.S3.history": ["배송준비", "품절취소", "재주문", "배송지연"],
    "preset.S4.history": ["배송준비", "취소요청"],

    # ── Transfer context (build_transfer_context) ──
    "transfer.header": (
        "[전환 컨텍스트 — Workflow 미처리 → GPT-Realtime-2 세션 시작]\n"
        "- 고객 코드: {cid} / 등급: {tier}\n"
        "- 요청 형태: {tone}\n"
        "- 최근 주문번호: {recent_order_id} / 주문일시: {recent_order_at}\n"
        "- 주문 상태: {order_status}\n"
    ),
    "transfer.body.complex": (
        "- Workflow 처리 시간: 약 2분 30초\n"
        "- 전환 사유: 복합 의도 처리 불가\n"
        "- 고객 요청 내용: 주문 변경 + 배송지 수정 + 쿠폰 적용 동시 요청\n"
        "- 쿠폰 보유: {has_coupon}\n"
        "- 지시사항: 복합 요청을 단계적으로 처리하고 각 단계마다 고객 확인을 받으세요.\n"
    ),
    "transfer.body.ambiguous": (
        "- Workflow 처리 시간: 약 1분\n"
        "- 전환 사유: 고객 의도 파악 불가 (3회 실패)\n"
        "- 고객 발화 패턴: 말을 바꾸거나 번복하는 경향 있음\n"
        "- 확인된 정보: 없음\n"
        "- 지시사항: 차분하게 고객의 의도를 다시 파악하세요. "
        "예/아니오로 답할 수 있는 간단한 질문을 활용하세요.\n"
    ),
    "transfer.body.default": "- 전환 사유: Workflow 처리 불가\n",
    "transfer.body.complaint_suffix": "- 고객 정서: 불만 상태. 첫 답변에서 공감/사과를 먼저 제시하세요.\n",
    "transfer.body.urgent_suffix": "- 고객 요청 긴급도: 높음. 핵심 조치와 결과를 먼저 짧게 안내하세요.\n",

    # ── Opening greeting ──
    "greeting.default": "안녕하세요, 무엇을 도와드릴까요?",
    "greeting.workflow_unresolved": (
        "이전 상담이 만족스럽지 않으셨나 보군요. "
        "상담 내역을 확인하고 추가적인 지원이 가능한지 확인 후 안내드리겠습니다."
    ),
    "greeting.complaint": "안녕하세요. 먼저 불편을 드려 죄송합니다. 현재 주문 상태를 바로 확인하고 가능한 조치를 빠르게 안내드리겠습니다.",
    "greeting.urgent": "안녕하세요. 긴급 문의로 접수해 우선 처리하겠습니다. 핵심 상태부터 바로 확인해드릴게요.",
    "greeting.delayed": "안녕하세요. 배송 지연 관련 문의를 도와드리겠습니다. 현재 상태를 먼저 확인해볼게요.",
    "greeting.lost": "안녕하세요. 배송 분실 건 확인을 도와드리겠습니다. 주문 상태부터 바로 조회하겠습니다.",
    "greeting.refund_requested": "안녕하세요. 환불 요청 진행 상황을 도와드리겠습니다. 현재 접수 상태부터 확인하겠습니다.",
    "greeting.normal": "안녕하세요. 배송이나 주문 관련 문의를 도와드릴게요. 궁금하신 내용을 편하게 말씀해 주세요.",

    # ── Session preamble (build_session_preamble) ──
    "preamble.template": (
        "[세션 컨텍스트 — 데모 사전 주입 정보]\n"
        "- 고객 코드: {customer_id}\n"
        "- 최근 주문번호: {recent_order_id}\n"
        "- 최근 주문일시: {recent_order_at}\n"
        "- 반복 이슈 횟수: {repeat_count}\n"
        "- 판매자 책임 사유: {seller_fault}\n"
        "- 주문 상태 이력: {order_status_history}\n"
        "- 고객 등급: {tier}\n"
        "- 요청 형태: {tone}\n"
        "- 주문 상태: {order_status}\n"
        "- 문의 유형: {inquiry}\n"
        "- 쿠폰 보유: {has_coupon}\n"
        "- 현재 상태: {workflow}\n\n"
        "[첫 응답 규칙]\n"
        "- 세션의 첫 음성 응답은 아래 첫 인사 문안을 기준으로 시작하세요.\n"
        "- 아래 첫 인사 문안을 우선적으로 따르되, 어색하면 자연스럽게 다듬어도 됩니다.\n"
        "- 이미 assistant가 한 번이라도 응답했다면 반복 인사하지 마세요.\n"
        "- 첫 인사 문안: {greeting}\n"
    ),

    # ── Order labels & mock responses (agents/order.py) ──
    "order.label.order_meta": "[주문번호: {oid} / 주문일시: {oat}]",
    "order.eta.normal_regular": "내일 오후 3시 예정",
    "order.eta.normal_vip": "오늘 오후 6시 예정 (VIP 당일배송)",
    "order.lookup.normal": "{meta} 정상 처리 중. 배송 예정: {eta}. 상품: 무선 이어폰 1개.",
    "order.lookup.delayed": "{meta} 배송 지연 중. 원인: 물류센터 적체. 예상 도착: 2일 후. 불편드려 죄송합니다.",
    "order.lookup.lost": "{meta} 배송 분실 접수됨. 담당 물류사 조사 중. 재발송 또는 환불 처리 가능합니다.",
    "order.lookup.refund_requested": "{meta} 환불 요청 접수 상태. 검토 중 (영업일 1-3일 소요).",
    "order.lookup.unknown": "{meta} 상태를 확인할 수 없습니다.",
    "order.cancel.done": "{meta} 취소 처리 완료. 결제 금액은 3-5 영업일 내 환불됩니다.",
    "order.cancel.already_refund": "{meta} 이미 환불 요청 상태입니다. 환불팀으로 연결해드리겠습니다.",

    # ── Delivery (agents/delivery.py) ──
    "delivery.eta.normal_regular": "내일 오후 3시",
    "delivery.eta.normal_vip": "오늘 오후 6시 (VIP 당일배송)",
    "delivery.lookup.auto_comp": (
        "{meta} 주문일 기준 {days}일 경과로 지연 보상 대상입니다. "
        "배송비 상당 3,000원 쿠폰이 자동 지급됩니다. "
        "현재 배송 상태 확인과 별도로 보상은 즉시 적용됩니다."
    ),
    "delivery.lookup.normal": "{meta} 배송 중. 현재 위치: 서울 물류센터 출발. 예상 도착: {eta}.",
    "delivery.lookup.delayed": (
        "{meta} 배송 지연 발생. 원인: 연휴 물류 적체. "
        "예상 도착: 2일 후. 배송지 변경은 오늘 오후 5시까지 가능합니다. "
        "정책 기준(3일 이상 지연) 충족 건으로 배송비 상당 3,000원 보상 쿠폰이 자동 지급됩니다."
    ),
    "delivery.lookup.lost": "{meta} 배송 분실 신고 접수됨. 물류사 조사 중 (1-2 영업일).",
    "delivery.lookup.unknown": "{meta} 배송 정보를 확인할 수 없습니다. 주문팀으로 연결해드리겠습니다.",
    "delivery.address.need_input": (
        "{meta} 배송지 변경 전 새 배송지를 정확히 확인해야 합니다. "
        "변경할 주소를 정확히 말씀해 주세요."
    ),
    "delivery.address.need_confirm": (
        "{meta} 고객 확인 전 단계입니다. "
        "요청 주소('{addr}')로 진행해도 되는지 고객의 명시 확인 후 다시 처리하겠습니다."
    ),
    "delivery.address.delayed": (
        "{meta} 배송지 변경 요청이 접수되었습니다: '{addr}'. "
        "출고/재배송 단계 확인 후 반영 결과를 안내드리며, 1-2 영업일 추가 소요될 수 있습니다."
    ),
    "delivery.address.lost": "{meta} 현재 배송 분실 처리 중으로 주소 변경이 불가합니다. 재발송 시 주소를 업데이트하겠습니다.",
    "delivery.address.normal": (
        "{meta} 배송지 변경 요청이 접수되었습니다: '{addr}'. "
        "이미 출고된 경우 반영 여부가 달라질 수 있어 최종 반영 결과를 확인 후 안내드립니다."
    ),

    # ── Refund (agents/refund.py) ──
    "refund.elapsed.with_days": "주문일 기준 {days}일 경과",
    "refund.elapsed.long_repeat": "장기/반복 이슈 기준",
    "refund.elapsed.repeat": "반복 이슈 기준",
    "refund.elapsed.delay_default": "주문일 기준 3일 이상 지연 기준",
    "refund.repeat_notice.with_count": "확인해보니 최근 문제가 {count}회 반복된 것으로 확인되어 추가 보상 요건을 충족합니다. ",
    "refund.repeat_notice.vip_generic": "확인해보니 최근 반복/지연 이슈가 확인되어 추가 보상 요건을 충족합니다. ",
    "refund.repeat_notice.regular_generic": "확인해보니 최근 반복 이슈가 확인되어 추가 보상 요건을 충족합니다. ",
    "refund.vip_discretionary": (
        "{meta} VIP 우선 환불 접수 완료. 사유: {reason}. "
        "{repeat_notice}{elapsed} 또는 품질 이슈가 확인되어 에이전트 자율 보상 10,000원 쿠폰 추가 제공을 결정했습니다. "
        "환불은 1영업일 내 우선 처리되며, 추가 보상 쿠폰은 계정에 순차 반영됩니다."
    ),
    "refund.regular_discretionary": (
        "{meta} 일반 고객 환불 접수 완료. 사유: {reason}. "
        "{repeat_notice}판매자 책임 반복 이슈({elapsed})가 확인되어 에이전트 재량 보상 5,000원 쿠폰 추가 제공을 결정했습니다. "
        "환불은 기준 일정에 따라 진행되며, 추가 보상 쿠폰은 계정에 순차 반영됩니다."
    ),
    "refund.vip_immediate": (
        "{meta} VIP 고객 환불 즉시 승인. 사유: {reason}. "
        "결제 금액 전액이 1 영업일 내 환불됩니다. 반송 택배 무료 제공."
    ),
    "refund.lost": (
        "{meta} 분실 건 환불 처리 완료. 사유: 배송 분실. "
        "결제 금액 전액 환불 + 보상 쿠폰 5,000원 지급 예정."
    ),
    "refund.delayed": (
        "{meta} 배송 지연 건으로 환불/보상 기준을 안내드립니다. 사유: {reason}. "
        "{elapsed}로 배송비 상당 3,000원 보상 쿠폰이 자동 지급됩니다. "
        "환불이 필요하면 즉시 환불 접수로 진행하겠습니다."
    ),
    "refund.default": (
        "{meta} 환불 접수 완료. 사유: {reason}. "
        "반품 운송장 번호를 문자로 발송합니다. 확인 후 3-5 영업일 내 환불됩니다."
    ),
    "refund.coupon.invalid": "{meta} 쿠폰 코드 '{code}'는 유효하지 않거나 이미 사용된 코드입니다.",
    "refund.coupon.applied": (
        "{meta} 쿠폰 '{code}' 적용 완료. "
        "할인 금액: 5,000원. 다음 주문에 자동 적용됩니다."
    ),

    # ── Sales / product (agents/sales.py) ──
    "product.EARPHONE.name": "무선 이어폰 Pro X",
    "product.EARPHONE.price": "89,000원",
    "product.EARPHONE.stock": "재고 있음",
    "product.EARPHONE.spec": "Bluetooth 5.3, ANC, 배터리 30시간",
    "product.CHARGER.name": "65W GaN 고속 충전기",
    "product.CHARGER.price": "34,000원",
    "product.CHARGER.stock": "재고 있음",
    "product.CHARGER.spec": "USB-C × 2 + USB-A × 1, 폴딩형",
    "product.CABLE.name": "USB-C 케이블 1m",
    "product.CABLE.price": "9,900원",
    "product.CABLE.stock": "품절",
    "product.CABLE.spec": "USB 2.0, 최대 60W 충전 지원",
    "product.lookup.not_found": "상품 코드 '{pid}'를 찾을 수 없습니다. 확인 후 다시 문의해 주세요.",
    "product.lookup.vip_note": " (VIP 고객 5% 추가 할인 적용 가능)",
    "product.lookup.template": "[{name}] 가격: {price}{vip_note} / 재고: {stock} / 사양: {spec}",
    "product.stock.EARPHONE": "재고 있음 (서울 물류센터 당일 출고 가능)",
    "product.stock.CHARGER": "재고 있음 (당일 출고 가능)",
    "product.stock.CABLE": "품절 (재입고 예정: 영업일 기준 3일 후)",
    "product.stock.unknown": "상품 코드 '{pid}' 재고를 확인할 수 없습니다.",

    # ── Membership (agents/activation.py) ──
    "membership.points.vip": "[{cid}] 적립 포인트: 25,800P. VIP 등급 혜택: 2배 적립 중. 유효기간: 2025-12-31.",
    "membership.points.regular": "[{cid}] 적립 포인트: 8,400P. 유효기간: 2025-12-31.",
    "membership.points.unknown": "[{cid}] 포인트 정보를 불러올 수 없습니다.",
    "membership.plan.VIP": "월 9,900원 / 무료배송 + 2배 포인트 + 전용 CS 라인",
    "membership.plan.PREMIUM": "월 4,900원 / 무료배송 + 1.5배 포인트",
    "membership.plan.STANDARD": "무료 / 기본 적립 혜택",
    "membership.plan.unknown": "알 수 없는 등급",
    "membership.register.done": "[{cid}] 멤버십 {plan} 신청 완료. 혜택: {benefits}. 다음 주문부터 적용됩니다.",

    # ── A/S (agents/technical.py) ──
    "as.priority.urgent": "긴급 처리",
    "as.priority.normal": "일반 처리",
    "as.report.done": (
        "[{ticket}] A/S 접수 완료. {priority}. 주문번호: {oid} / 주문일시: {oat}. 증상: {description}. "
        "담당 기사 배정 후 영업일 1-2일 내 연락드립니다."
    ),
    "as.report.description_default": "불량 내용 미입력",
    "as.warranty.refund_requested": (
        "[주문번호: {oid} / 주문일시: {oat}] 해당 상품은 환불 요청 상태입니다. "
        "환불팀과 연계하여 처리해드리겠습니다."
    ),
    "as.warranty.normal": (
        "[주문번호: {oid} / 주문일시: {oat}] 보증 기간: 구매일로부터 1년. "
        "현재 보증 기간 내. 무상 수리 또는 교환 가능합니다."
    ),

    # ── Human followup (assistant_service.py) ──
    "human_followup.with_phone": (
        "바로 연결은 어렵습니다. 상담 내용은 안전하게 기록되어 확인 후 상담원이 순차적으로 연락드리거나 문자로 안내드릴 예정입니다. "
        "요청하신 연락처({phone})로 접수했고, 접수 사유는 '{summary}'입니다. "
        "불편 사항을 즉시 해결해드리지 못해 죄송합니다."
    ),
    "human_followup.without_phone": (
        "바로 연결은 어렵습니다. 상담 내용은 안전하게 기록되어 확인 후 상담원이 순차적으로 연락드리거나 문자로 안내드릴 예정입니다. "
        "고객 프로파일에 있는 전화번호로 연락드릴 예정인데, 혹시 다른 번호로 연락받아야 하신다면 말씀해 주세요. "
        "불편 사항을 즉시 해결해드리지 못해 죄송합니다."
    ),
    "human_followup.summary_default": "현재 상담 내용",
    "human_followup.tool.description": "고객이 상담원 연결/재연락을 요청할 때 연락 접수를 진행합니다. callback_phone이 있으면 해당 번호로 접수합니다.",
    "human_followup.param.callback_phone": "고객이 요청한 회신 전화번호(선택)",
    "human_followup.param.issue_summary": "현재 상담 요약",

    # ── Global agent rules (assistant_service.py) ──
    "agent.global_rules": """

## 공통 운영 규칙
- 고객이 상담원 연결/재연락/담당자 연락을 요청하면, 추가 대기 멘트를 반복하지 말고 같은 턴에서 즉시 `request_human_followup` function을 호출하세요.
- `request_human_followup` 결과를 전달할 때는 다른 번호 수신이 필요한지만 간단히 확인하세요.
- 배송지/연락처/개인정보 변경 요청은 사용자가 새 값을 직접 말하고 명시적으로 확인하기 전까지 함수 호출로 확정 처리하지 마세요.
- 사용자가 제공하지 않은 주소/번호를 임의로 추정하거나 예시값으로 입력해 처리하지 마세요.
- 보상/추가보상/쿠폰 증액 요청은 우선 현재 에이전트의 보상 정책 처리(또는 환불/보상 에이전트 전환)를 먼저 수행하세요.
- 사용자가 명시적으로 상담원 연결/담당자 연락을 요구한 경우에만 `request_human_followup`를 호출하세요. 단순 보상 문의만으로는 먼저 호출하지 마세요.
""",

    # ── Root agent ──
    "agent.root.name": "상담 안내",
    "agent.root.system_message": """당신은 쇼핑몰 고객센터 AI 라우터입니다.

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 핵심 규칙
    1. 세션 상단에 [세션 컨텍스트] 또는 [전환 컨텍스트]가 주어졌다면, 첫 응답에서 그 배경정보를 반영한 맞춤형 인사로 시작하세요.
    2. 고객이 이미 요청을 말했다면, 인사 없이 즉시 해당 전문 에이전트 function을 호출하세요.
    3. 고객 요청이 아직 명시되지 않았더라도 사전주입된 배경정보가 있으면 일반적인 "무엇을 도와드릴까요?" 대신 그 맥락을 짧게 짚어 주세요.
    3. 절대 직접 답변하지 마세요. 반드시 function call로 전문 에이전트에게 라우팅하세요.
    4. 전문 에이전트가 처리를 완료한 후, "다른 문의가 있으신가요?"라고 물으세요.
    5. 고객이 더 이상 문의가 없다고 하면 "감사합니다. 좋은 하루 되세요."로 마무리하세요.
    6. 고객이 상담원 연결/재연락을 요청하면 거절하지 말고 `request_human_followup` function을 호출해 연락 접수를 진행하세요.

    ## 라우팅 대상
    - 주문 조회/변경/취소 → Assistant_OrderAssistant
    - 배송 현황/배송지 변경/분실 → Assistant_DeliveryAssistant
    - 환불/교환/쿠폰 → Assistant_RefundAssistant
    - 상품 스펙/재고/가격 → Assistant_ProductAssistant
    - 포인트/멤버십 → Assistant_MembershipAssistant
    - 상품 불량/A/S → Assistant_AfterServiceAssistant

    ## 금지사항
    - "TERMINATE" 같은 내부 키워드를 절대 말하지 마세요.
    - "에이전트로 연결하겠습니다" 같은 설명 없이, 바로 function call을 실행하세요.
    - Root 단계에서는 배송/주문/환불의 구체 정책을 직접 제공하지 마세요. 반드시 해당 전문 에이전트로 라우팅하세요.
    """,

    # ── Order agent ──
    "agent.order.name": "주문 관리",
    "agent.order.system_message": """당신은 주문 관리 전문 상담원입니다.

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
    "agent.order.tool.lookup_order.description": "주문 상태 및 상세 정보를 조회합니다.",
    "agent.order.tool.lookup_order.param.order_id": "주문 번호 또는 고객 코드",
    "agent.order.tool.cancel_order.description": "주문을 취소하고 환불을 접수합니다.",
    "agent.order.tool.cancel_order.param.order_id": "주문 번호",
    "agent.order.tool.cancel_order.param.reason": "취소 사유",

    # ── Delivery agent ──
    "agent.delivery.name": "배송 관리",
    "agent.delivery.system_message": """당신은 배송 관리 전문 상담원입니다.

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
    "agent.delivery.tool.lookup_delivery.description": "배송 현황 및 예상 도착 시간을 조회합니다.",
    "agent.delivery.tool.lookup_delivery.param.order_id": "주문 번호",
    "agent.delivery.tool.update_address.description": "배송지 주소를 변경합니다.",
    "agent.delivery.tool.update_address.param.order_id": "주문 번호",
    "agent.delivery.tool.update_address.param.new_address": "새 배송지 주소",
    "agent.delivery.tool.update_address.param.customer_confirmed": "고객이 해당 주소로 진행을 명시적으로 확인했는지 여부",

    # ── Refund agent ──
    "agent.refund.name": "환불/교환",
    "agent.refund.system_message": """당신은 환불·교환 전문 상담원입니다.

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
    "agent.refund.tool.process_refund.description": "환불 또는 교환 요청을 접수하고 처리합니다.",
    "agent.refund.tool.process_refund.param.order_id": "주문 번호",
    "agent.refund.tool.process_refund.param.reason": "환불/교환 사유",
    "agent.refund.tool.process_refund.param.type": "refund 또는 exchange",
    "agent.refund.tool.process_refund.param.repeat_count": "동일 이슈 반복 횟수(예: 판매자 품절취소 반복)",
    "agent.refund.tool.process_refund.param.seller_fault": "판매자 책임 사유(재고 오판매 등) 여부",
    "agent.refund.tool.process_refund.param.order_status_history": "주문 상태 이력(예: ['배송준비','품절취소','재주문','배송지연'])",
    "agent.refund.tool.apply_coupon.description": "쿠폰 코드를 적용합니다.",
    "agent.refund.tool.apply_coupon.param.order_id": "주문 번호",
    "agent.refund.tool.apply_coupon.param.coupon_code": "쿠폰 코드",

    # ── Sales / product agent ──
    "agent.product.name": "상품 문의",
    "agent.product.system_message": """당신은 상품 문의 전문 상담원입니다.

    ## 음성 스타일
    - 한국어로 대화하세요.
    - 짧고 간결하게, 한 번에 2~3문장 이내로 말하세요.
    - 따뜻하고 친절한 상담원처럼 말하세요.

    ## 업무
    - 상품 스펙, 가격, 재고 정보를 정확하게 안내합니다.
    - 고객의 필요에 맞는 상품을 추천합니다.
    - VIP 고객에게는 추가 할인 혜택을 안내합니다.

    ## 취급 상품 코드
    EARPHONE, CHARGER, CABLE
    """,
    "agent.product.tool.lookup_product.description": "상품 상세 정보(가격, 재고, 사양)를 조회합니다.",
    "agent.product.tool.lookup_product.param.product_id": "상품 코드 (예: EARPHONE, CHARGER, CABLE)",
    "agent.product.tool.check_stock.description": "상품 재고 및 출고 가능 여부를 확인합니다.",
    "agent.product.tool.check_stock.param.product_id": "상품 코드",

    # ── Membership agent ──
    "agent.membership.name": "회원/포인트",
    "agent.membership.system_message": """당신은 회원 및 포인트 관리 전문 상담원입니다.

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
    "agent.membership.tool.check_points.description": "고객의 포인트 잔액과 유효기간을 조회합니다.",
    "agent.membership.tool.check_points.param.customer_id": "고객 코드",
    "agent.membership.tool.register_membership.description": "멤버십 신규 가입 또는 등급 업그레이드를 처리합니다.",
    "agent.membership.tool.register_membership.param.customer_id": "고객 코드",
    "agent.membership.tool.register_membership.param.membership_type": "멤버십 등급: STANDARD / PREMIUM / VIP",

    # ── A/S agent ──
    "agent.afterservice.name": "A/S 불량",
    "agent.afterservice.system_message": """당신은 A/S 및 상품 불량 처리 전문 상담원입니다.

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
    "agent.afterservice.tool.report_defect.description": "상품 불량/파손을 접수하고 A/S 티켓을 발행합니다.",
    "agent.afterservice.tool.report_defect.param.order_id": "주문 번호",
    "agent.afterservice.tool.report_defect.param.description": "불량 증상 설명",
    "agent.afterservice.tool.check_warranty.description": "보증 기간 및 무상 수리 가능 여부를 확인합니다.",
    "agent.afterservice.tool.check_warranty.param.order_id": "주문 번호",
}

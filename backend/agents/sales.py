import demo_state

_PRODUCTS = {
    "EARPHONE": {
        "name": "무선 이어폰 Pro X",
        "price": "89,000원",
        "stock": "재고 있음",
        "spec": "Bluetooth 5.3, ANC, 배터리 30시간",
    },
    "CHARGER": {
        "name": "65W GaN 고속 충전기",
        "price": "34,000원",
        "stock": "재고 있음",
        "spec": "USB-C × 2 + USB-A × 1, 폴딩형",
    },
    "CABLE": {
        "name": "USB-C 케이블 1m",
        "price": "9,900원",
        "stock": "품절",
        "spec": "USB 2.0, 최대 60W 충전 지원",
    },
}


def _lookup_product(inp: dict) -> str:
    state = demo_state.get()
    pid = inp.get("product_id", "").upper()
    tier = state["customer_tier"]

    product = _PRODUCTS.get(pid)
    if not product:
        return f"상품 코드 '{pid}'를 찾을 수 없습니다. 확인 후 다시 문의해 주세요."

    vip_note = " (VIP 고객 5% 추가 할인 적용 가능)" if tier == "vip" else ""
    return (
        f"[{product['name']}] "
        f"가격: {product['price']}{vip_note} / "
        f"재고: {product['stock']} / "
        f"사양: {product['spec']}"
    )


def _check_stock(inp: dict) -> str:
    pid = inp.get("product_id", "").upper()
    stock_map = {
        "EARPHONE": "재고 있음 (서울 물류센터 당일 출고 가능)",
        "CHARGER":  "재고 있음 (당일 출고 가능)",
        "CABLE":    "품절 (재입고 예정: 영업일 기준 3일 후)",
    }
    return stock_map.get(pid, f"상품 코드 '{pid}' 재고를 확인할 수 없습니다.")


product_assistant = {
    "id": "Assistant_ProductAssistant",
    "name": "상품 문의",
    "description": """Call this if:
        - Customer asks about product specifications, features, or details
        - Customer wants to know product price or stock availability
        - Customer asks for product recommendations
        DO NOT CALL THIS IF:
        - Customer asks about their existing order or delivery status
        - Customer wants a refund or exchange for an already purchased item""",
    "system_message": """당신은 상품 문의 전문 상담원입니다.

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
    "tools": [
        {
            "name": "lookup_product",
            "description": "상품 상세 정보(가격, 재고, 사양)를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "상품 코드 (예: EARPHONE, CHARGER, CABLE)",
                    },
                },
            },
            "returns": lambda inp: _lookup_product(inp),
        },
        {
            "name": "check_stock",
            "description": "상품 재고 및 출고 가능 여부를 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "상품 코드",
                    },
                },
            },
            "returns": lambda inp: _check_stock(inp),
        },
    ],
}

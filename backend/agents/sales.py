"""Product / sales inquiry agent."""
import demo_state
from i18n import t

_PRODUCT_IDS = ("EARPHONE", "CHARGER", "CABLE")


def _product_fields(pid: str) -> dict | None:
    if pid not in _PRODUCT_IDS:
        return None
    return {
        "name": t(f"product.{pid}.name"),
        "price": t(f"product.{pid}.price"),
        "stock": t(f"product.{pid}.stock"),
        "spec": t(f"product.{pid}.spec"),
    }


def _lookup_product(inp: dict) -> str:
    state = demo_state.get()
    pid = inp.get("product_id", "").upper()
    tier = state["customer_tier"]

    product = _product_fields(pid)
    if not product:
        return t("product.lookup.not_found", pid=pid)

    vip_note = t("product.lookup.vip_note") if tier == "vip" else ""
    return t(
        "product.lookup.template",
        name=product["name"],
        price=product["price"],
        vip_note=vip_note,
        stock=product["stock"],
        spec=product["spec"],
    )


def _check_stock(inp: dict) -> str:
    pid = inp.get("product_id", "").upper()
    if pid in _PRODUCT_IDS:
        return t(f"product.stock.{pid}")
    return t("product.stock.unknown", pid=pid)


def build_product_assistant() -> dict:
    return {
        "id": "Assistant_ProductAssistant",
        "name": t("agent.product.name"),
        "description": """Call this if:
        - Customer asks about product specifications, features, or details
        - Customer wants to know product price or stock availability
        - Customer asks for product recommendations
        DO NOT CALL THIS IF:
        - Customer asks about their existing order or delivery status
        - Customer wants a refund or exchange for an already purchased item""",
        "system_message": t("agent.product.system_message"),
        "tools": [
            {
                "name": "lookup_product",
                "description": t("agent.product.tool.lookup_product.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": t("agent.product.tool.lookup_product.param.product_id"),
                        },
                    },
                },
                "returns": _lookup_product,
            },
            {
                "name": "check_stock",
                "description": t("agent.product.tool.check_stock.description"),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": t("agent.product.tool.check_stock.param.product_id")},
                    },
                },
                "returns": _check_stock,
            },
        ],
    }

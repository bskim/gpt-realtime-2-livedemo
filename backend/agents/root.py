"""Root routing agent. Strings are resolved per-locale via i18n.t() at build time."""
from i18n import t


def build_root_assistant() -> dict:
    return {
        "id": "Assistant_RootAssistant",
        "name": t("agent.root.name"),
        "description": """Call this if:
    - You need to greet the Customer.
    - You need to check if Customer has any additional questions.
    - You need to close the conversation after the Customer's request has been resolved.
    DO NOT CALL THIS IF:
    - You need to handle order inquiries or changes
    - You need to handle delivery or shipping inquiries
    - You need to handle refunds, exchanges, or coupon application
    - You need to answer product specification or availability questions
    - You need to handle membership, points, or subscription inquiries
    - You need to handle product defects or A/S claims""",
        "system_message": t("agent.root.system_message"),
        "tools": [],
    }

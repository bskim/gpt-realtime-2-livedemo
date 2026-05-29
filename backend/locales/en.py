"""i18n string table — English."""

STRINGS: dict = {
    # ── AssistantService / language tag for agent system_message ──
    "assistant.language": "English",
    # ── Azure realtime session input transcription language code ──
    "realtime.transcription_language": "en",
    # ── Forced closing line on user end-gesture ──
    "realtime.forced_closing_line": "Thank you for reaching out. I'll wrap up this call now.",
    # End-of-session detection regex patterns.
    "realtime.end_session_patterns": [
        r"thank\s*you",
        r"thanks",
        r"that'?s\s*all",
        r"i'?m\s*good",
        r"no\s*(more|further)\s*(questions|help)",
        r"that'?ll\s*be\s*all",
        r"please\s*end\s*(the\s*)?(call|session)",
        r"hang\s*up",
        r"(i'?ll\s*)?(call|reach)\s*back\s*later",
        r"i'?ll\s*let\s*you\s*know",
        r"(have\s*a\s*)?good\s*(day|one)",
        r"appreciate\s*(it|your\s*help)",
    ],
    "realtime.forced_closing_instruction": "The customer has indicated they want to end the call. Respond with exactly this one sentence: '{line}'",
    "realtime.auto_end_reason": "Detected customer intent to end the call",

    # ── Labels for state values ──
    "label.tier.vip": "VIP",
    "label.tier.regular": "Regular",
    "label.tone.normal": "Normal",
    "label.tone.urgent": "Urgent",
    "label.tone.complaint": "Complaint",
    "label.order.normal": "On track",
    "label.order.delayed": "Delivery delayed",
    "label.order.lost": "Delivery lost",
    "label.order.refund_requested": "Refund requested",
    "label.inquiry.simple": "Simple inquiry",
    "label.inquiry.complex": "Complex intent",
    "label.inquiry.ambiguous": "Ambiguous request",
    "label.workflow.unresolved": "Primary workflow could not resolve (Fallback)",
    "label.workflow.resolved": "Primary workflow can handle",
    "label.yes": "Yes",
    "label.no": "No",
    "label.has": "Yes",
    "label.has_not": "No",
    "label.unknown": "Unknown",
    "label.none": "None",

    # ── Demo presets ──
    "preset.S1.label": "S1 Simple FAQ",
    "preset.S2.label": "S2 Complex intent",
    "preset.S3.label": "S3 Upset customer",
    "preset.S4.label": "S4 Ambiguous request",
    "preset.S3.history": ["Preparing", "Cancelled (out of stock)", "Reordered", "Delivery delayed"],
    "preset.S4.history": ["Preparing", "Cancellation requested"],

    # ── Transfer context ──
    "transfer.header": (
        "[Transfer context — Primary workflow could not resolve → starting GPT-Realtime-2 session]\n"
        "- Customer ID: {cid} / Tier: {tier}\n"
        "- Request type: {tone}\n"
        "- Most recent order ID: {recent_order_id} / Ordered at: {recent_order_at}\n"
        "- Order status: {order_status}\n"
    ),
    "transfer.body.complex": (
        "- Workflow elapsed: about 2 min 30 sec\n"
        "- Reason for transfer: cannot handle complex intent\n"
        "- Customer request: change order + update shipping address + apply coupon, all at once\n"
        "- Has coupon: {has_coupon}\n"
        "- Instructions: handle the multi-part request step by step and confirm with the customer at each step.\n"
    ),
    "transfer.body.ambiguous": (
        "- Workflow elapsed: about 1 min\n"
        "- Reason for transfer: unable to identify customer intent (3 failed attempts)\n"
        "- Customer speech pattern: tends to rephrase or reverse statements\n"
        "- Confirmed information: none\n"
        "- Instructions: calmly re-clarify the customer's intent. "
        "Use simple yes/no questions to narrow things down.\n"
    ),
    "transfer.body.default": "- Reason for transfer: workflow could not resolve\n",
    "transfer.body.complaint_suffix": "- Customer sentiment: upset. Lead with empathy / apology in your first response.\n",
    "transfer.body.urgent_suffix": "- Urgency: high. Lead with the key action and outcome briefly.\n",

    # ── Opening greeting ──
    "greeting.default": "Hello, how can I help you today?",
    "greeting.workflow_unresolved": (
        "It sounds like the previous conversation wasn't quite satisfactory. "
        "Let me review the history and see what additional support we can provide."
    ),
    "greeting.complaint": "Hello, and I'm sorry for the inconvenience. Let me check your order status right away and walk you through the available next steps.",
    "greeting.urgent": "Hello, I've flagged this as urgent and will handle it on priority. Let me check the key status first.",
    "greeting.delayed": "Hello, I'll help you with the delivery delay. Let me check the current status first.",
    "greeting.lost": "Hello, I'll help you look into the lost delivery. Let me pull up the order status right now.",
    "greeting.refund_requested": "Hello, I'll help with the refund request status. Let me check where it stands first.",
    "greeting.normal": "Hello, I can help with delivery or order questions. Please go ahead and tell me what you need.",

    # ── Session preamble ──
    "preamble.template": (
        "[Session context — demo pre-injected information]\n"
        "- Customer ID: {customer_id}\n"
        "- Most recent order ID: {recent_order_id}\n"
        "- Most recent order time: {recent_order_at}\n"
        "- Repeat-issue count: {repeat_count}\n"
        "- Seller fault: {seller_fault}\n"
        "- Order status history: {order_status_history}\n"
        "- Customer tier: {tier}\n"
        "- Request type: {tone}\n"
        "- Order status: {order_status}\n"
        "- Inquiry type: {inquiry}\n"
        "- Has coupon: {has_coupon}\n"
        "- Current state: {workflow}\n\n"
        "[First-response rules]\n"
        "- Start the very first voice response using the opening line below.\n"
        "- Prefer the opening line below, but you may rephrase it lightly for natural delivery.\n"
        "- If the assistant has already spoken at least once, do not repeat the greeting.\n"
        "- Opening line: {greeting}\n"
    ),

    # ── Order ──
    "order.label.order_meta": "[Order: {oid} / Ordered at: {oat}]",
    "order.eta.normal_regular": "tomorrow, 3 PM",
    "order.eta.normal_vip": "today, 6 PM (VIP same-day delivery)",
    "order.lookup.normal": "{meta} Processing normally. Estimated delivery: {eta}. Item: 1x Wireless Earbuds.",
    "order.lookup.delayed": "{meta} Delivery delayed. Cause: warehouse backlog. Estimated arrival: in 2 days. We apologize for the inconvenience.",
    "order.lookup.lost": "{meta} Lost-delivery case opened. Carrier investigation in progress. Reshipment or refund are both available.",
    "order.lookup.refund_requested": "{meta} Refund request received and under review (1–3 business days).",
    "order.lookup.unknown": "{meta} Unable to verify the current status.",
    "order.cancel.done": "{meta} Cancellation completed. The payment will be refunded within 3–5 business days.",
    "order.cancel.already_refund": "{meta} A refund request is already in progress. I'll connect you to the refund team.",

    # ── Delivery ──
    "delivery.eta.normal_regular": "tomorrow, 3 PM",
    "delivery.eta.normal_vip": "today, 6 PM (VIP same-day delivery)",
    "delivery.lookup.auto_comp": (
        "{meta} {days} days have elapsed since order, so this qualifies for delayed-delivery compensation. "
        "A 3,000 KRW coupon equivalent to shipping cost will be issued automatically. "
        "The compensation applies immediately, independent of the current shipping status."
    ),
    "delivery.lookup.normal": "{meta} In transit. Current location: departed Seoul warehouse. Estimated arrival: {eta}.",
    "delivery.lookup.delayed": (
        "{meta} Delivery delay detected. Cause: holiday-season backlog. "
        "Estimated arrival: in 2 days. Address changes can still be made until 5 PM today. "
        "Meets the policy threshold (delayed 3+ days), so a 3,000 KRW shipping-equivalent coupon is auto-issued."
    ),
    "delivery.lookup.lost": "{meta} Lost-delivery report received. Carrier investigation in progress (1–2 business days).",
    "delivery.lookup.unknown": "{meta} Unable to look up delivery info. I'll connect you to the orders team.",
    "delivery.address.need_input": (
        "{meta} I need the exact new address before changing it. "
        "Could you please tell me the address you'd like to switch to?"
    ),
    "delivery.address.need_confirm": (
        "{meta} I'm at the confirmation step. "
        "Once you confirm we should proceed with '{addr}', I'll process the change."
    ),
    "delivery.address.delayed": (
        "{meta} Address-change request received: '{addr}'. "
        "After checking the shipment/redispatch stage, I'll confirm the outcome; this may add 1–2 business days."
    ),
    "delivery.address.lost": "{meta} The package is in lost-investigation, so the address cannot be changed right now. I'll update the address when reshipping.",
    "delivery.address.normal": (
        "{meta} Address-change request received: '{addr}'. "
        "If it has already shipped, application may vary; I'll confirm the final outcome and follow up."
    ),

    # ── Refund ──
    "refund.elapsed.with_days": "{days} days since order",
    "refund.elapsed.long_repeat": "long-standing / repeated-issue criteria",
    "refund.elapsed.repeat": "repeated-issue criteria",
    "refund.elapsed.delay_default": "policy threshold of 3+ day delivery delay",
    "refund.repeat_notice.with_count": "We confirmed the issue has recurred {count} times, which meets the extra-compensation criteria. ",
    "refund.repeat_notice.vip_generic": "We confirmed recent repeat / delay issues that meet the extra-compensation criteria. ",
    "refund.repeat_notice.regular_generic": "We confirmed recent repeated issues that meet the extra-compensation criteria. ",
    "refund.vip_discretionary": (
        "{meta} VIP-priority refund accepted. Reason: {reason}. "
        "{repeat_notice}Given {elapsed} or quality issues confirmed, an additional 10,000 KRW discretionary coupon has been approved. "
        "Refund is prioritized within 1 business day; the additional coupon will be applied to your account sequentially."
    ),
    "refund.regular_discretionary": (
        "{meta} Refund accepted. Reason: {reason}. "
        "{repeat_notice}Seller-fault repeated issue ({elapsed}) confirmed, so an additional 5,000 KRW discretionary coupon has been approved. "
        "Refund proceeds on the standard schedule; the additional coupon will be applied to your account sequentially."
    ),
    "refund.vip_immediate": (
        "{meta} VIP refund approved immediately. Reason: {reason}. "
        "Full payment will be refunded within 1 business day. Return shipping is on us."
    ),
    "refund.lost": (
        "{meta} Refund for lost delivery completed. Reason: lost in transit. "
        "Full refund plus a 5,000 KRW compensation coupon will be issued."
    ),
    "refund.delayed": (
        "{meta} Walking you through the refund/compensation policy for delivery delay. Reason: {reason}. "
        "Per {elapsed}, a 3,000 KRW shipping-equivalent coupon is auto-issued. "
        "If you'd like a full refund, I can file it right away."
    ),
    "refund.default": (
        "{meta} Refund accepted. Reason: {reason}. "
        "Return waybill will be sent by SMS. After we receive it, the refund processes within 3–5 business days."
    ),
    "refund.coupon.invalid": "{meta} Coupon code '{code}' is invalid or has already been used.",
    "refund.coupon.applied": (
        "{meta} Coupon '{code}' applied. "
        "Discount amount: 5,000 KRW. It will apply automatically to your next order."
    ),

    # ── Sales / product ──
    "product.EARPHONE.name": "Wireless Earbuds Pro X",
    "product.EARPHONE.price": "89,000 KRW",
    "product.EARPHONE.stock": "In stock",
    "product.EARPHONE.spec": "Bluetooth 5.3, ANC, 30-hour battery",
    "product.CHARGER.name": "65W GaN Fast Charger",
    "product.CHARGER.price": "34,000 KRW",
    "product.CHARGER.stock": "In stock",
    "product.CHARGER.spec": "USB-C × 2 + USB-A × 1, foldable",
    "product.CABLE.name": "USB-C Cable 1m",
    "product.CABLE.price": "9,900 KRW",
    "product.CABLE.stock": "Out of stock",
    "product.CABLE.spec": "USB 2.0, up to 60W charging",
    "product.lookup.not_found": "I couldn't find product code '{pid}'. Please confirm the code and try again.",
    "product.lookup.vip_note": " (VIP customers can get an additional 5% off)",
    "product.lookup.template": "[{name}] Price: {price}{vip_note} / Stock: {stock} / Spec: {spec}",
    "product.stock.EARPHONE": "In stock (same-day shipping from Seoul warehouse)",
    "product.stock.CHARGER": "In stock (same-day shipping)",
    "product.stock.CABLE": "Out of stock (restocking in 3 business days)",
    "product.stock.unknown": "Unable to check stock for product code '{pid}'.",

    # ── Membership ──
    "membership.points.vip": "[{cid}] Points balance: 25,800 P. VIP benefit: 2x point accrual. Expires: 2025-12-31.",
    "membership.points.regular": "[{cid}] Points balance: 8,400 P. Expires: 2025-12-31.",
    "membership.points.unknown": "[{cid}] Unable to load points information.",
    "membership.plan.VIP": "9,900 KRW/month / free shipping + 2x points + dedicated CS line",
    "membership.plan.PREMIUM": "4,900 KRW/month / free shipping + 1.5x points",
    "membership.plan.STANDARD": "Free / basic accrual benefits",
    "membership.plan.unknown": "Unknown tier",
    "membership.register.done": "[{cid}] Membership enrollment for {plan} completed. Benefits: {benefits}. Applies from your next order.",

    # ── A/S ──
    "as.priority.urgent": "Priority handling",
    "as.priority.normal": "Standard handling",
    "as.report.done": (
        "[{ticket}] A/S ticket created. {priority}. Order: {oid} / Ordered at: {oat}. Symptom: {description}. "
        "A technician will be assigned and contact you within 1–2 business days."
    ),
    "as.report.description_default": "(no symptom description provided)",
    "as.warranty.refund_requested": (
        "[Order: {oid} / Ordered at: {oat}] This item is currently in refund-request state. "
        "I'll coordinate with the refund team and follow up."
    ),
    "as.warranty.normal": (
        "[Order: {oid} / Ordered at: {oat}] Warranty period: 1 year from purchase. "
        "Within warranty. Free repair or replacement is available."
    ),

    # ── Human followup ──
    "human_followup.with_phone": (
        "I'm not able to transfer you live right now. The conversation has been recorded securely, and an agent will follow up sequentially by phone or SMS. "
        "I've logged the requested callback number ({phone}) with the reason '{summary}'. "
        "I'm sorry we couldn't resolve this immediately."
    ),
    "human_followup.without_phone": (
        "I'm not able to transfer you live right now. The conversation has been recorded securely, and an agent will follow up sequentially by phone or SMS. "
        "We'll use the phone number on your profile by default; please let me know if you'd like us to use a different number. "
        "I'm sorry we couldn't resolve this immediately."
    ),
    "human_followup.summary_default": "current conversation",
    "human_followup.tool.description": "Use this when the customer asks to be connected to a human agent or to be called back. If callback_phone is supplied, register that number.",
    "human_followup.param.callback_phone": "Optional callback phone number requested by the customer",
    "human_followup.param.issue_summary": "Summary of the current conversation",

    # ── Global agent rules ──
    "agent.global_rules": """

## Shared operating rules
- When the customer asks to be transferred / called back / connected to a human, do not stall with filler — call the `request_human_followup` function in the same turn.
- When delivering the `request_human_followup` result, only briefly confirm whether a different callback number is needed.
- For changes to shipping address / contact info / personal info, do not commit via a function call until the customer explicitly states the new value and confirms it.
- Never invent or guess an address / phone number the user did not provide.
- For compensation / additional-compensation / coupon-amount requests, first apply the current agent's compensation policy (or transfer to the refund/compensation agent) before anything else.
- Only call `request_human_followup` when the customer explicitly asks to speak with a human / receive a callback. A plain compensation question is not enough to trigger it.
""",

    # ── Root agent ──
    "agent.root.name": "Consultation routing",
    "agent.root.system_message": """You are the AI router for a shopping-mall customer center.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Core rules
    1. If a [Session context] or [Transfer context] block appears at the top of the session, lead the first response with a tailored greeting that reflects that background.
    2. If the customer has already stated their request, skip the greeting and immediately call the appropriate specialist-agent function.
    3. Even if the customer hasn't stated their request yet, when pre-injected background exists, briefly acknowledge that context instead of a generic "How can I help you?".
    3. Never answer directly. Always route to a specialist agent via function call.
    4. After the specialist agent finishes, ask "Is there anything else I can help with?".
    5. If the customer has no further questions, close with "Thank you. Have a great day.".
    6. If the customer asks to speak with a human / be called back, do not refuse — call `request_human_followup` and log the callback.

    ## Routing targets
    - Order lookup / change / cancel → Assistant_OrderAssistant
    - Delivery status / address change / lost package → Assistant_DeliveryAssistant
    - Refund / exchange / coupon → Assistant_RefundAssistant
    - Product spec / stock / price → Assistant_ProductAssistant
    - Points / membership → Assistant_MembershipAssistant
    - Product defects / A/S → Assistant_AfterServiceAssistant

    ## Do not
    - Never speak internal keywords like "TERMINATE".
    - Do not narrate "I'll transfer you to an agent" — just execute the function call.
    - At the Root layer, do not provide concrete delivery / order / refund policy yourself. Always route to the specialist agent.
    """,

    # ── Order agent ──
    "agent.order.name": "Order management",
    "agent.order.system_message": """You are a specialist agent for order management.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Look up order status and explain it clearly.
    - Process order changes or cancellations.
    - For complex intents (order change + other requests), handle them step by step.

    ## Cautions
    - For delayed or lost orders, lead with empathy before proposing a solution.
    - When the session context has the most recent order ID/time, use it as the default order without re-asking the customer.
    """,
    "agent.order.tool.lookup_order.description": "Look up the order status and details.",
    "agent.order.tool.lookup_order.param.order_id": "Order number or customer code",
    "agent.order.tool.cancel_order.description": "Cancel an order and file the refund.",
    "agent.order.tool.cancel_order.param.order_id": "Order number",
    "agent.order.tool.cancel_order.param.reason": "Reason for cancellation",

    # ── Delivery agent ──
    "agent.delivery.name": "Delivery management",
    "agent.delivery.system_message": """You are a specialist agent for delivery management.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Look up delivery status and explain it to the customer.
    - Process address-change requests.
    - Lead with empathy on delayed / lost cases before proposing a solution.
    - When a formal policy threshold is met (e.g., 3+ day delivery delay), state the compensation right away.
    - If the customer asks for additional compensation / coupon top-up / repeated-issue compensation, hand off to the refund/compensation agent (`Assistant_RefundAssistant`) immediately.

    ## Cautions
    - For delayed or lost cases, acknowledge the inconvenience first, then propose the solution.
    - When the session context has the most recent order ID/time, use it as the default order without re-asking the customer.
    - When a policy threshold is met, do not loop-route; state the compensation criteria clearly here.
    - Demo policy: any order 3+ days past order time auto-issues a 3,000 KRW shipping-equivalent coupon.
    - When asked about compensation, do not respond with "I'll connect the relevant team" only — state the policy criteria and amount in the current response at minimum.
    - Do not call `request_human_followup` before the customer explicitly asks for "human agent" or "have someone call me".
    - If the customer pushes for extra compensation (e.g., auto-comp is not enough, multiple repeated issues, repeated seller cancellations), prefer transferring to `Assistant_RefundAssistant`.
    - Use the current session context (order ID / order time / status) as the top-priority signal.
    - Only proceed with address change when the customer has stated the new address directly. If no address was given, ask for it first.
    - Do not finalize via `update_address` unless `customer_confirmed=true`. Until confirmation, respond at the acknowledgement / confirmation step.
    - Do not pass an arbitrary or example address that the user did not say.
    - Only ask one minimum clarifying question when essential information is missing (e.g., damage location).
    """,
    "agent.delivery.tool.lookup_delivery.description": "Look up delivery status and estimated arrival.",
    "agent.delivery.tool.lookup_delivery.param.order_id": "Order number",
    "agent.delivery.tool.update_address.description": "Update the shipping address.",
    "agent.delivery.tool.update_address.param.order_id": "Order number",
    "agent.delivery.tool.update_address.param.new_address": "New shipping address",
    "agent.delivery.tool.update_address.param.customer_confirmed": "Whether the customer has explicitly confirmed to proceed with this address",

    # ── Refund agent ──
    "agent.refund.name": "Refund / exchange",
    "agent.refund.system_message": """You are a specialist agent for refunds and exchanges.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Accept and process refund or exchange requests.
    - Process coupon-application requests.
    - Acknowledge the customer's dissatisfaction with empathy and propose the best resolution.
    - For delivery-delay compensation questions, state the formal policy criteria clearly first.

    ## Cautions
    - Empathize first, then propose a solution.
    - For VIP customers, announce the priority treatment (immediate approval).
    - When the session context has the most recent order ID/time, use it as the default order without re-asking the customer.
    - When a policy threshold is met, do not loop-route; state the criteria and compensation amount directly in the current response.
    - Demo policy: any order 3+ days past order time auto-issues a 3,000 KRW shipping-equivalent coupon.
    - For VIP customers, you may proactively offer a 10,000 KRW discretionary coupon when excessive delay (e.g., 14+ days), repeated delays / repeated out-of-stock cancellations, or damage/defect issues are detected.
    - For regular customers, you may offer an additional 5,000 KRW discretionary compensation when seller_fault=true plus repeated-issue (repeat_count>=2) conditions are met.
    - When calling `process_refund`, prefer the supplied `repeat_count`, `seller_fault`, and `order_status_history` to decide the compensation branch.
    - If the customer asks for a human agent, do not refuse — call `request_human_followup` and log the callback.
    - Do not end the turn with only "I'll connect the relevant team" / "We'll check the policy and follow up".
    - For any compensation question, state the criteria (3 days), the form of compensation (coupon), and the amount (3,000 KRW) in a single sentence at least once.
    - Use the current session context (order ID / order time / status) as the top-priority signal.
    - Only ask one minimum clarifying question when essential info for a refund/exchange is missing (e.g., damage area, quantity).
    """,
    "agent.refund.tool.process_refund.description": "Accept and process a refund or exchange request.",
    "agent.refund.tool.process_refund.param.order_id": "Order number",
    "agent.refund.tool.process_refund.param.reason": "Reason for refund / exchange",
    "agent.refund.tool.process_refund.param.type": "refund or exchange",
    "agent.refund.tool.process_refund.param.repeat_count": "Count of repeated occurrences of the same issue (e.g. repeated seller out-of-stock cancellation)",
    "agent.refund.tool.process_refund.param.seller_fault": "Whether the cause is seller fault (e.g. mis-listed stock)",
    "agent.refund.tool.process_refund.param.order_status_history": "Order status history (e.g. ['Preparing','Cancelled (out of stock)','Reordered','Delivery delayed'])",
    "agent.refund.tool.apply_coupon.description": "Apply a coupon code.",
    "agent.refund.tool.apply_coupon.param.order_id": "Order number",
    "agent.refund.tool.apply_coupon.param.coupon_code": "Coupon code",

    # ── Sales / product agent ──
    "agent.product.name": "Product inquiry",
    "agent.product.system_message": """You are a specialist agent for product inquiries.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Provide accurate product specs, prices, and stock information.
    - Recommend products that fit the customer's needs.
    - Highlight extra discount benefits for VIP customers.

    ## Supported product codes
    EARPHONE, CHARGER, CABLE
    """,
    "agent.product.tool.lookup_product.description": "Look up product details (price, stock, spec).",
    "agent.product.tool.lookup_product.param.product_id": "Product code (e.g. EARPHONE, CHARGER, CABLE)",
    "agent.product.tool.check_stock.description": "Check product stock and shipping availability.",
    "agent.product.tool.check_stock.param.product_id": "Product code",

    # ── Membership agent ──
    "agent.membership.name": "Membership / points",
    "agent.membership.system_message": """You are a specialist agent for membership and points.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Provide the points balance and expiration date.
    - Explain membership tier benefits and process new sign-ups or upgrades.
    - Emphasize VIP-only benefits for VIP customers.

    ## Membership tiers
    - STANDARD: Free / basic accrual
    - PREMIUM: 4,900 KRW/month / free shipping + 1.5x points
    - VIP: 9,900 KRW/month / free shipping + 2x points + dedicated CS
    """,
    "agent.membership.tool.check_points.description": "Look up the customer's points balance and expiration.",
    "agent.membership.tool.check_points.param.customer_id": "Customer code",
    "agent.membership.tool.register_membership.description": "Process a new membership signup or tier upgrade.",
    "agent.membership.tool.register_membership.param.customer_id": "Customer code",
    "agent.membership.tool.register_membership.param.membership_type": "Membership tier: STANDARD / PREMIUM / VIP",

    # ── A/S agent ──
    "agent.afterservice.name": "A/S — defects",
    "agent.afterservice.system_message": """You are a specialist agent for A/S and product defects.

    ## Voice style
    - Speak in English.
    - Keep it short and concise — no more than 2–3 sentences per turn.
    - Sound warm and friendly, like a thoughtful human agent.

    ## Responsibilities
    - Accept product-defect symptoms and issue an A/S ticket.
    - Explain warranty period and whether free repair is available.
    - Prioritize VIP / urgent customers.

    ## Cautions
    - Acknowledge the inconvenience first, then proceed with intake.
    - When the session context has the most recent order ID/time, use it as the default order without re-asking the customer.
    - If the warranty has expired, present the paid-repair option.
    """,
    "agent.afterservice.tool.report_defect.description": "Register a product defect / damage and issue an A/S ticket.",
    "agent.afterservice.tool.report_defect.param.order_id": "Order number",
    "agent.afterservice.tool.report_defect.param.description": "Description of the defect symptoms",
    "agent.afterservice.tool.check_warranty.description": "Check warranty period and free-repair eligibility.",
    "agent.afterservice.tool.check_warranty.param.order_id": "Order number",
}

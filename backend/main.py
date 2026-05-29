import asyncio
import base64
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

import demo_state
from agents.activation import build_membership_assistant
from agents.delivery import build_delivery_assistant
from agents.order import build_order_assistant
from agents.refund import build_refund_assistant
from agents.root import build_root_assistant
from agents.sales import build_product_assistant
from agents.technical import build_afterservice_assistant
from assistant_service import AssistantService
from i18n import (
    available_locales,
    get_default_locale,
    get_locale,
    set_locale,
    t,
)
from realtime_client import RealtimeClient

# backend/.env 값을 OS 전역 환경변수보다 우선시킨다.
# 다른 azd 프로젝트의 전역 env(예: 다른 모델/엔드포인트)가 남아 있어도 이 데모는 .env 를 따른다.
_BACKEND_ENV = Path(__file__).parent / ".env"
load_dotenv(_BACKEND_ENV, override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_ep = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
_dep = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()

# 설정 검증 — 조용한 오동작(예: 이웃 프로젝트의 전역 env 가 새어들어온 경우)을 시작 시점에 fail-fast 로 차단한다.
_config_errors: list[str] = []
if not _BACKEND_ENV.exists():
    _config_errors.append(
        "backend/.env 가 존재하지 않습니다. azd 의 postprovision hook 이 실패했을 수 있습니다. "
        "scripts/write_env.ps1 또는 scripts/write_env.sh 를 수동 실행하거나 backend/.env 를 직접 작성하세요."
    )
if not _ep:
    _config_errors.append("AZURE_OPENAI_ENDPOINT 가 비어 있습니다.")
elif "cognitiveservices.azure.com" not in _ep and "openai.azure.com" not in _ep:
    _config_errors.append(f"AZURE_OPENAI_ENDPOINT 값이 Azure OpenAI 형식이 아닙니다: {_ep}")
if not _dep:
    _config_errors.append("AZURE_OPENAI_DEPLOYMENT 이 비어 있습니다.")
elif "realtime" not in _dep.lower():
    _config_errors.append(
        f"AZURE_OPENAI_DEPLOYMENT='{_dep}' 은 realtime 배포가 아닙니다. 이 데모는 'gpt-realtime-2' 배포가 필요합니다. "
        "시스템 전역 환경변수(예: 다른 프로젝트의 azd env)가 새어들어온 것일 수 있습니다. backend/.env 를 확인하세요."
    )

if _config_errors:
    for _msg in _config_errors:
        logger.error("[config] %s", _msg)
    raise SystemExit(
        "[config] 환경 설정 오류로 서버를 시작할 수 없습니다. 위 로그를 확인하고 backend/.env 를 바로잡으세요."
    )


def _mask_endpoint(value: str) -> str:
    if not value:
        return ""
    try:
        scheme, rest = value.split("://", 1)
        host = rest.split("/", 1)[0]
        if len(host) <= 6:
            masked_host = "*" * len(host)
        else:
            masked_host = host[:3] + "***" + host[-3:]
        return f"{scheme}://{masked_host}"
    except ValueError:
        return "***"


app = FastAPI(title="GPT-Realtime-2 Voice CS Demo")


@app.get("/health")
async def health() -> dict:
    """마스킹된 설정 요약. 브라우저로서 백엔드가 어떤 리소스에 붙을지 1초만에 진단한다."""
    return {
        "status": "ok",
        "endpoint": _mask_endpoint(_ep),
        "deployment": _dep,
        "env_file": str(_BACKEND_ENV) if _BACKEND_ENV.exists() else None,
        "default_locale": get_default_locale(),
        "available_locales": available_locales(),
    }

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
ALLOWED_VOICES = {
    "sage",
    "shimmer",
    "verse",
    "ballad",
    "alloy",
    "ash",
    "echo",
    "cedar",
    "marin",
}


def build_transfer_context(state: dict) -> str:
    """
    Workflow 미처리 시 전환 컨텍스트를 RT-2 system prompt 앞에 주입한다.
    inquiry_type에 따라 다른 컨텍스트를 생성한다.
    """
    if state.get("workflow_resolved", True):
        return ""

    cid = state.get("customer_id", "CUST-001")
    tier = state.get("customer_tier", "regular")
    tone = state.get("request_tone", "normal")
    order_status = state.get("order_status", "normal")
    inquiry = state.get("inquiry_type", "simple")

    header = t(
        "transfer.header",
        cid=cid,
        tier=t(f"label.tier.{tier}"),
        tone=t(f"label.tone.{tone}"),
        recent_order_id=state.get("recent_order_id", t("label.unknown")),
        recent_order_at=state.get("recent_order_at", t("label.unknown")),
        order_status=t(f"label.order.{order_status}"),
    )

    if inquiry == "complex":
        body = t(
            "transfer.body.complex",
            has_coupon=t("label.has" if state.get("has_coupon") else "label.has_not"),
        )
    elif inquiry == "ambiguous":
        body = t("transfer.body.ambiguous")
    else:
        body = t("transfer.body.default")

    if tone == "complaint":
        body += t("transfer.body.complaint_suffix")
    elif tone == "urgent":
        body += t("transfer.body.urgent_suffix")
    return header + body + "\n"


def build_opening_greeting(state: dict) -> str:
    if demo_state.is_default_state(state):
        return t("greeting.default")

    tone = state.get("request_tone", "normal")
    order_status = state.get("order_status", "normal")

    if not state.get("workflow_resolved", True):
        return t("greeting.workflow_unresolved")
    if tone == "complaint":
        return t("greeting.complaint")
    if tone == "urgent":
        return t("greeting.urgent")
    if order_status == "delayed":
        return t("greeting.delayed")
    if order_status == "lost":
        return t("greeting.lost")
    if order_status == "refund_requested":
        return t("greeting.refund_requested")
    return t("greeting.normal")


def build_session_preamble(state: dict) -> str:
    history_value = state.get("order_status_history")
    if isinstance(history_value, list):
        history_text = ", ".join(history_value) if history_value else t("label.none")
    else:
        history_text = history_value or t("label.none")

    preamble = t(
        "preamble.template",
        customer_id=state.get("customer_id", "CUST-001"),
        recent_order_id=state.get("recent_order_id", t("label.unknown")),
        recent_order_at=state.get("recent_order_at", t("label.unknown")),
        repeat_count=state.get("repeat_count", 0),
        seller_fault=t("label.yes" if state.get("seller_fault") else "label.no"),
        order_status_history=history_text,
        tier=t(f"label.tier.{state.get('customer_tier', 'regular')}"),
        tone=t(f"label.tone.{state.get('request_tone', 'normal')}"),
        order_status=t(f"label.order.{state.get('order_status', 'normal')}"),
        inquiry=t(f"label.inquiry.{state.get('inquiry_type', 'simple')}"),
        has_coupon=t("label.has" if state.get("has_coupon") else "label.has_not"),
        workflow=t("label.workflow.resolved" if state.get("workflow_resolved", True) else "label.workflow.unresolved"),
        greeting=build_opening_greeting(state),
    )

    transfer_context = build_transfer_context(state)
    if transfer_context:
        preamble += "\n" + transfer_context
    return preamble


def apply_demo_injection(payload: dict) -> tuple[str | None, float | None]:
    update = dict(payload)
    preset_id = update.pop("preset", None)
    requested_voice = update.pop("voice", None)
    requested_speed = update.pop("speed", None)
    requested_locale = update.pop("locale", None)

    if requested_locale is not None:
        set_locale(requested_locale)

    selected_voice: str | None = None
    if isinstance(requested_voice, str):
        normalized_voice = requested_voice.strip().lower()
        if normalized_voice in ALLOWED_VOICES:
            selected_voice = normalized_voice
        else:
            selected_voice = "sage"

    if preset_id:
        demo_state.apply_preset(preset_id)
    if update:
        demo_state.update(update)

    return selected_voice, requested_speed


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # 세션마다 기본 locale로 초기화 — 이전 세션의 ContextVar 값이 새어들지 않도록 강제 리셋.
    set_locale(get_default_locale())
    logger.info("Browser WebSocket connected (locale=%s)", get_locale())

    async def send_to_browser(msg: dict):
        try:
            await websocket.send_json(msg)
        except Exception:
            pass

    client_holder: dict = {"client": None}
    initial_voice: str | None = None
    initial_speed: float | None = None

    try:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            initial_msg = json.loads(raw)
            if initial_msg.get("type") == "demo_inject":
                initial_voice, initial_speed = apply_demo_injection(initial_msg.get("payload", {}))
                logger.info(f"Initial demo state: {demo_state.get()} (locale={get_locale()})")
        except asyncio.TimeoutError:
            pass

        # locale이 결정된 후 에이전트 및 설정을 해당 세션 locale로 빌드한다.
        assistant = AssistantService(language=t("assistant.language"))
        assistant.register_agent(build_order_assistant())
        assistant.register_agent(build_delivery_assistant())
        assistant.register_agent(build_refund_assistant())
        assistant.register_agent(build_product_assistant())
        assistant.register_agent(build_membership_assistant())
        assistant.register_agent(build_afterservice_assistant())
        assistant.register_root_agent(build_root_assistant())

        client = RealtimeClient(assistant=assistant, send_callback=send_to_browser)
        client_holder["client"] = client
        if initial_voice:
            await client.update_voice(initial_voice, initial_speed)

        await send_to_browser({"type": "session_status", "status": "connecting"})

        # 세션 컨텍스트 및 전환 컨텍스트 빌드
        state = demo_state.get()
        session_preamble = build_session_preamble(state)
        transfer_ctx = build_transfer_context(state)
        await client.connect(session_preamble=session_preamble)
        await client.wait_for_session()

        # 브라우저에 transfer context 전송 (UI 시각화용)
        await send_to_browser({
            "type": "transfer_context",
            "context": transfer_ctx,
            "state": state,
            "is_fallback": bool(transfer_ctx),
        })
        await send_to_browser({"type": "session_status", "status": "connected"})
        logger.info("Azure OpenAI Realtime session established")

        # 세션 시작 시 인사 유도 — server_vad는 음성 없으면 응답 안 하므로 명시적 트리거
        await client.create_response()

        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "audio_input":
                audio_bytes = base64.b64decode(msg["data"])
                await client.append_input_audio(bytearray(audio_bytes))

            elif msg_type == "demo_inject":
                voice, speed = apply_demo_injection(msg.get("payload", {}))
                if voice:
                    await client.update_voice(voice, speed)
                logger.info(f"Demo state: {demo_state.get()} (locale={get_locale()})")
                await send_to_browser({"type": "demo_state", "state": demo_state.get(), "locale": get_locale()})

            elif msg_type == "session_end":
                break

    except WebSocketDisconnect:
        logger.info("Browser WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await send_to_browser({"type": "error", "message": str(e)})
    finally:
        client = client_holder.get("client")
        if client is not None:
            await client.disconnect()
        logger.info("Azure OpenAI Realtime session closed")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

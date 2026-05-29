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
from agents.delivery import delivery_assistant
from agents.order import order_assistant
from agents.refund import refund_assistant
from agents.root import root_assistant
from agents.activation import membership_assistant
from agents.sales import product_assistant
from agents.technical import afterservice_assistant
from assistant_service import AssistantService
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
    tier_label = {"vip": "VIP", "regular": "일반"}.get(state.get("customer_tier", "regular"), "일반")
    tone_label = {"normal": "일반", "urgent": "긴급", "complaint": "불만"}.get(
        state.get("request_tone", "normal"), "일반"
    )
    order_status_label = {
        "normal": "정상",
        "delayed": "배송 지연 중",
        "lost": "배송 분실",
        "refund_requested": "환불 요청 중",
    }.get(state.get("order_status", "normal"), "정상")

    inquiry = state.get("inquiry_type", "simple")
    tone = state.get("request_tone", "normal")

    header = (
        f"[전환 컨텍스트 — Workflow 미처리 → GPT-Realtime-2 세션 시작]\n"
        f"- 고객 코드: {cid} / 등급: {tier_label}\n"
        f"- 요청 형태: {tone_label}\n"
        f"- 최근 주문번호: {state.get('recent_order_id', '미확인')} / 주문일시: {state.get('recent_order_at', '미확인')}\n"
        f"- 주문 상태: {order_status_label}\n"
    )

    bodies = {
        "complex": (
            "- Workflow 처리 시간: 약 2분 30초\n"
            "- 전환 사유: 복합 의도 처리 불가\n"
            "- 고객 요청 내용: 주문 변경 + 배송지 수정 + 쿠폰 적용 동시 요청\n"
            f"- 쿠폰 보유: {'있음' if state.get('has_coupon') else '없음'}\n"
            "- 지시사항: 복합 요청을 단계적으로 처리하고 각 단계마다 고객 확인을 받으세요.\n"
        ),
        "ambiguous": (
            "- Workflow 처리 시간: 약 1분\n"
            "- 전환 사유: 고객 의도 파악 불가 (3회 실패)\n"
            "- 고객 발화 패턴: 말을 바꾸거나 번복하는 경향 있음\n"
            "- 확인된 정보: 없음\n"
            "- 지시사항: 차분하게 고객의 의도를 다시 파악하세요. "
            "예/아니오로 답할 수 있는 간단한 질문을 활용하세요.\n"
        ),
    }

    body = bodies.get(inquiry, "- 전환 사유: Workflow 처리 불가\n")
    if tone == "complaint":
        body += "- 고객 정서: 불만 상태. 첫 답변에서 공감/사과를 먼저 제시하세요.\n"
    elif tone == "urgent":
        body += "- 고객 요청 긴급도: 높음. 핵심 조치와 결과를 먼저 짧게 안내하세요.\n"
    return header + body + "\n"


def build_opening_greeting(state: dict) -> str:
    if demo_state.is_default_state(state):
        return "안녕하세요, 무엇을 도와드릴까요?"

    tone = state.get("request_tone", "normal")
    order_status = state.get("order_status", "normal")

    if not state.get("workflow_resolved", True):
        return (
            "이전 상담이 만족스럽지 않으셨나 보군요. "
            "상담 내역을 확인하고 추가적인 지원이 가능한지 확인 후 안내드리겠습니다."
        )

    if tone == "complaint":
        return "안녕하세요. 먼저 불편을 드려 죄송합니다. 현재 주문 상태를 바로 확인하고 가능한 조치를 빠르게 안내드리겠습니다."
    if tone == "urgent":
        return "안녕하세요. 긴급 문의로 접수해 우선 처리하겠습니다. 핵심 상태부터 바로 확인해드릴게요."

    if order_status == "delayed":
        return "안녕하세요. 배송 지연 관련 문의를 도와드리겠습니다. 현재 상태를 먼저 확인해볼게요."
    if order_status == "lost":
        return "안녕하세요. 배송 분실 건 확인을 도와드리겠습니다. 주문 상태부터 바로 조회하겠습니다."
    if order_status == "refund_requested":
        return "안녕하세요. 환불 요청 진행 상황을 도와드리겠습니다. 현재 접수 상태부터 확인하겠습니다."
    return "안녕하세요. 배송이나 주문 관련 문의를 도와드릴게요. 궁금하신 내용을 편하게 말씀해 주세요."


def build_session_preamble(state: dict) -> str:
    tier_label = {"vip": "VIP", "regular": "일반"}.get(state.get("customer_tier", "regular"), "일반")
    tone_label = {"normal": "일반", "urgent": "긴급", "complaint": "불만"}.get(
        state.get("request_tone", "normal"), "일반"
    )
    order_status_label = {
        "normal": "정상",
        "delayed": "배송 지연 중",
        "lost": "배송 분실",
        "refund_requested": "환불 요청 중",
    }.get(state.get("order_status", "normal"), "정상")
    inquiry_label = {
        "simple": "단순 문의",
        "complex": "복합 의도",
        "ambiguous": "모호 요청",
    }.get(state.get("inquiry_type", "simple"), "단순 문의")
    workflow_label = "사전 Workflow 미처리(Fallback)" if not state.get("workflow_resolved", True) else "Workflow 처리 가능"

    preamble = (
        "[세션 컨텍스트 — 데모 사전 주입 정보]\n"
        f"- 고객 코드: {state.get('customer_id', 'CUST-001')}\n"
        f"- 최근 주문번호: {state.get('recent_order_id', '미확인')}\n"
        f"- 최근 주문일시: {state.get('recent_order_at', '미확인')}\n"
        f"- 반복 이슈 횟수: {state.get('repeat_count', 0)}\n"
        f"- 판매자 책임 사유: {'예' if state.get('seller_fault') else '아니오'}\n"
        f"- 주문 상태 이력: {', '.join(state.get('order_status_history', [])) if isinstance(state.get('order_status_history'), list) else state.get('order_status_history', '없음')}\n"
        f"- 고객 등급: {tier_label}\n"
        f"- 요청 형태: {tone_label}\n"
        f"- 주문 상태: {order_status_label}\n"
        f"- 문의 유형: {inquiry_label}\n"
        f"- 쿠폰 보유: {'있음' if state.get('has_coupon') else '없음'}\n"
        f"- 현재 상태: {workflow_label}\n\n"
        "[첫 응답 규칙]\n"
        "- 세션의 첫 음성 응답은 아래 첫 인사 문안을 기준으로 시작하세요.\n"
        "- 아래 첫 인사 문안을 우선적으로 따르되, 어색하면 자연스럽게 다듬어도 됩니다.\n"
        "- 이미 assistant가 한 번이라도 응답했다면 반복 인사하지 마세요.\n"
        f"- 첫 인사 문안: {build_opening_greeting(state)}\n"
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
    logger.info("Browser WebSocket connected")

    async def send_to_browser(msg: dict):
        try:
            await websocket.send_json(msg)
        except Exception:
            pass

    assistant = AssistantService(language="Korean")
    assistant.register_agent(order_assistant)
    assistant.register_agent(delivery_assistant)
    assistant.register_agent(refund_assistant)
    assistant.register_agent(product_assistant)
    assistant.register_agent(membership_assistant)
    assistant.register_agent(afterservice_assistant)
    assistant.register_root_agent(root_assistant)

    client = RealtimeClient(assistant=assistant, send_callback=send_to_browser)

    try:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            initial_msg = json.loads(raw)
            if initial_msg.get("type") == "demo_inject":
                voice, speed = apply_demo_injection(initial_msg.get("payload", {}))
                logger.info(f"Initial demo state: {demo_state.get()}")
                if voice:
                    await client.update_voice(voice, speed)
        except asyncio.TimeoutError:
            pass

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
                logger.info(f"Demo state: {demo_state.get()}")
                await send_to_browser({"type": "demo_state", "state": demo_state.get()})

            elif msg_type == "session_end":
                break

    except WebSocketDisconnect:
        logger.info("Browser WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await send_to_browser({"type": "error", "message": str(e)})
    finally:
        await client.disconnect()
        logger.info("Azure OpenAI Realtime session closed")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

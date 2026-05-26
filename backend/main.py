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

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-Realtime-2 Voice CS Demo")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def build_transfer_context(state: dict) -> str:
    """
    Workflow 미처리 시 전환 컨텍스트를 RT-2 system prompt 앞에 주입한다.
    inquiry_type에 따라 다른 컨텍스트를 생성한다.
    """
    if state.get("workflow_resolved", True):
        return ""

    cid = state.get("customer_id", "CUST-001")
    tier_label = {"vip": "VIP", "regular": "일반", "problem": "불만 고객", "urgent": "긴급"}.get(
        state.get("customer_tier", "regular"), "일반"
    )
    order_status_label = {
        "normal": "정상",
        "delayed": "배송 지연 중",
        "lost": "배송 분실",
        "refund_requested": "환불 요청 중",
    }.get(state.get("order_status", "normal"), "정상")

    inquiry = state.get("inquiry_type", "simple")

    header = (
        f"[전환 컨텍스트 — Workflow 미처리 → GPT-Realtime-2 세션 시작]\n"
        f"- 고객 코드: {cid} / 등급: {tier_label}\n"
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
        "emotional": (
            "- Workflow 처리 시간: 약 4분\n"
            "- 전환 사유: 감정적 고객, Workflow 처리 불가\n"
            "- 고객 상태: 배송 지연으로 인해 매우 불만족 상태, 감정 고조\n"
            "- 지시사항: 먼저 충분히 공감하고 사과하세요. 해결책은 그 다음입니다. "
            "톤을 부드럽고 차분하게 유지하세요.\n"
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
    return header + body + "\n"


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
        await send_to_browser({"type": "session_status", "status": "connecting"})

        # 전환 컨텍스트 빌드 및 주입
        state = demo_state.get()
        transfer_ctx = build_transfer_context(state)
        await client.connect(transfer_context=transfer_ctx)
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

        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "audio_input":
                audio_bytes = base64.b64decode(msg["data"])
                await client.append_input_audio(bytearray(audio_bytes))

            elif msg_type == "demo_inject":
                payload = msg.get("payload", {})
                preset_id = payload.pop("preset", None)
                if preset_id:
                    demo_state.apply_preset(preset_id)
                if payload:
                    demo_state.update(payload)
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

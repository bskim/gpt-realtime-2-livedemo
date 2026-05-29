import os
import re
import json
import base64
import asyncio
import inspect
import logging
import traceback
from datetime import datetime
from collections import defaultdict
from typing import Callable, Awaitable

import numpy as np
import websockets
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from assistant_service import AssistantService
from i18n import t

logger = logging.getLogger(__name__)

AUDIO_SAMPLE_RATE = 24000  # gpt-realtime-2: PCM16 24 kHz


def _end_session_patterns() -> list[str]:
    """locale 별 종료 의사 감지 정규식."""
    value = t("realtime.end_session_patterns")
    return value if isinstance(value, list) else []


def _forced_closing_line() -> str:
    return t("realtime.forced_closing_line")


def float_to_16bit_pcm(float32_array: np.ndarray) -> np.ndarray:
    return (np.clip(float32_array, -1, 1) * 32767).astype(np.int16)


def base64_to_array_buffer(b64: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8)


def array_buffer_to_base64(arr: np.ndarray) -> str:
    if arr.dtype == np.float32:
        arr = float_to_16bit_pcm(arr)
    else:
        arr = arr.tobytes()
    return base64.b64encode(arr).decode("utf-8")


class RealtimeEventHandler:
    def __init__(self):
        self.event_handlers: dict = defaultdict(list)

    def on(self, event_name: str, handler: Callable) -> None:
        self.event_handlers[event_name].append(handler)

    def clear_event_handlers(self) -> None:
        self.event_handlers = defaultdict(list)

    def dispatch(self, event_name: str, event) -> None:
        for handler in self.event_handlers[event_name]:
            if inspect.iscoroutinefunction(handler):
                asyncio.create_task(handler(event))
            else:
                handler(event)

    async def wait_for_next(self, event_name: str):
        future: asyncio.Future = asyncio.get_event_loop().create_future()

        def handler(event):
            if not future.done():
                future.set_result(event)

        self.on(event_name, handler)
        return await future


class RealtimeAPI(RealtimeEventHandler):
    def __init__(self):
        super().__init__()
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].strip().rstrip("/")
        # Portal/azd 출력에 따라 endpoint 끝에 /openai/v1, /openai 가 붙어 오는 경우가 있어 정규화한다.
        # 정규화하지 않으면 아래 ws_url 조립에서 /openai/v1/openai/v1/realtime 처럼 경로가 중복되어 404가 난다.
        for suffix in ("/openai/v1", "/openai"):
            if endpoint.lower().endswith(suffix):
                endpoint = endpoint[: -len(suffix)].rstrip("/")
        # Support both https:// and already-wss:// endpoints
        self.url = endpoint.replace("https://", "wss://").replace("http://", "ws://")
        self.credentials = DefaultAzureCredential()
        self.acquire_token = get_bearer_token_provider(
            self.credentials, "https://cognitiveservices.azure.com/.default"
        )
        self.azure_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"].strip()
        if "realtime" not in self.azure_deployment.lower():
            logger.warning(
                "AZURE_OPENAI_DEPLOYMENT='%s' 는 realtime 모델 배포명이 아닐 수 있습니다. "
                "이 데모는 gpt-realtime-2 배포가 필요합니다.",
                self.azure_deployment,
            )
        self.ws = None

    def is_connected(self) -> bool:
        return self.ws is not None

    async def connect(self, model: str = None) -> None:
        if self.is_connected():
            raise RuntimeError("Already connected")
        model = model or self.azure_deployment
        # gpt-realtime-2: GA endpoint, model via query param, auth via Entra ID Bearer
        headers = {"Authorization": f"Bearer {self.acquire_token()}"}

        ws_url = f"{self.url}/openai/v1/realtime?model={model}"
        self.ws = await websockets.connect(ws_url, additional_headers=headers)
        logger.info(f"Connected to Azure OpenAI Realtime (gpt-realtime-2): {ws_url}")
        asyncio.create_task(self._receive_messages())

    async def _receive_messages(self) -> None:
        async for message in self.ws:
            event = json.loads(message)
            evt_type = event["type"]
            if evt_type == "error":
                logger.error(f"Realtime API error: {message}")
            elif evt_type.startswith("response."):
                logger.info(f"<< {evt_type}")
            elif evt_type == "session.created" or evt_type == "session.updated":
                logger.info(f"<< {evt_type}: {json.dumps(event.get('session', {}), ensure_ascii=False)[:500]}")
            else:
                logger.info(f"<< {evt_type}")
            self.dispatch(f"server.{evt_type}", event)
            self.dispatch("server.*", event)

    async def send(self, event_name: str, data: dict = None) -> None:
        if not self.is_connected():
            raise RuntimeError("RealtimeAPI is not connected")
        data = data or {}
        event = {"event_id": self._gen_id("evt_"), "type": event_name, **data}
        if event_name != "input_audio_buffer.append":
            logger.info(f">> {event_name}: {json.dumps(data, ensure_ascii=False)[:300]}")
        self.dispatch(f"client.{event_name}", event)
        self.dispatch("client.*", event)
        await self.ws.send(json.dumps(event))

    def _gen_id(self, prefix: str) -> str:
        return f"{prefix}{int(datetime.utcnow().timestamp() * 1000)}"

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
            self.ws = None


class RealtimeConversation:
    default_frequency = AUDIO_SAMPLE_RATE

    EventProcessors = {
        "conversation.item.added": lambda s, e: s._on_item_created(e),
        "conversation.item.truncated": lambda s, e: s._on_item_truncated(e),
        "conversation.item.deleted": lambda s, e: s._on_item_deleted(e),
        "conversation.item.input_audio_transcription.completed": lambda s, e: s._on_transcription_completed(e),
        "input_audio_buffer.speech_started": lambda s, e: s._on_speech_started(e),
        "input_audio_buffer.speech_stopped": lambda s, e, buf: s._on_speech_stopped(e, buf),
        "response.created": lambda s, e: s._on_response_created(e),
        "response.output_item.added": lambda s, e: s._on_output_item_added(e),
        "response.output_item.done": lambda s, e: s._on_output_item_done(e),
        "response.content_part.added": lambda s, e: s._on_content_part_added(e),
        "response.output_audio_transcript.delta": lambda s, e: s._on_audio_transcript_delta(e),
        "response.output_audio.delta": lambda s, e: s._on_audio_delta(e),
        "response.text.delta": lambda s, e: s._on_text_delta(e),
        "response.function_call_arguments.delta": lambda s, e: s._on_fn_args_delta(e),
    }

    def __init__(self):
        self.clear()

    def clear(self):
        self.item_lookup: dict = {}
        self.items: list = []
        self.response_lookup: dict = {}
        self.responses: list = []
        self.queued_speech_items: dict = {}
        self.queued_transcript_items: dict = {}
        self.queued_input_audio = None

    def queue_input_audio(self, audio):
        self.queued_input_audio = audio

    def process_event(self, event, *args):
        processor = self.EventProcessors.get(event["type"])
        if not processor:
            raise ValueError(f"No processor for {event['type']}")
        return processor(self, event, *args)

    def get_item(self, id: str):
        return self.item_lookup.get(id)

    def get_items(self):
        return self.items[:]

    def _on_item_created(self, event):
        item = event["item"].copy()
        if item["id"] not in self.item_lookup:
            self.item_lookup[item["id"]] = item
            self.items.append(item)
        item["formatted"] = {"audio": [], "text": "", "transcript": ""}
        if item["id"] in self.queued_speech_items:
            item["formatted"]["audio"] = self.queued_speech_items.pop(item["id"])["audio"]
        if "content" in item:
            for c in item["content"]:
                if c["type"] in ("text", "input_text"):
                    item["formatted"]["text"] += c["text"]
        if item["id"] in self.queued_transcript_items:
            item["formatted"]["transcript"] = self.queued_transcript_items.pop(item["id"])["transcript"]
        if item["type"] == "message":
            item["status"] = "completed" if item["role"] == "user" else "in_progress"
            if item["role"] == "user" and self.queued_input_audio:
                item["formatted"]["audio"] = self.queued_input_audio
                self.queued_input_audio = None
        elif item["type"] == "function_call":
            item["formatted"]["tool"] = {
                "type": "function",
                "name": item["name"],
                "call_id": item["call_id"],
                "arguments": "",
            }
            item["status"] = "in_progress"
        elif item["type"] == "function_call_output":
            item["status"] = "completed"
            item["formatted"]["output"] = item["output"]
        return item, None

    def _on_item_truncated(self, event):
        item = self.item_lookup.get(event["item_id"])
        if not item:
            return None, None
        end = (event["audio_end_ms"] * self.default_frequency) // 1000
        item["formatted"]["transcript"] = ""
        item["formatted"]["audio"] = item["formatted"]["audio"][:end]
        return item, None

    def _on_item_deleted(self, event):
        item = self.item_lookup.pop(event["item_id"], None)
        if item and item in self.items:
            self.items.remove(item)
        return item, None

    def _on_transcription_completed(self, event):
        transcript = event.get("transcript") or ""
        item = self.item_lookup.get(event["item_id"])
        if not item:
            self.queued_transcript_items[event["item_id"]] = {"transcript": transcript}
            return None, None
        item["type"] = "conversation.item.input_audio_transcription.completed"
        item["content"][event["content_index"]]["transcript"] = transcript
        item["formatted"]["transcript"] = transcript
        return item, {"transcript": transcript}

    def _on_speech_started(self, event):
        self.queued_speech_items[event["item_id"]] = {"audio_start_ms": event["audio_start_ms"]}
        return None, None

    def _on_speech_stopped(self, event, buf):
        speech = self.queued_speech_items.get(event["item_id"], {})
        speech["audio_end_ms"] = event["audio_end_ms"]
        if buf:
            start = (speech["audio_start_ms"] * self.default_frequency) // 1000
            end = (speech["audio_end_ms"] * self.default_frequency) // 1000
            speech["audio"] = buf[start:end]
        return None, None

    def _on_response_created(self, event):
        resp = event["response"]
        if resp["id"] not in self.response_lookup:
            self.response_lookup[resp["id"]] = resp
            self.responses.append(resp)
        return None, None

    def _on_output_item_added(self, event):
        resp = self.response_lookup.get(event["response_id"])
        if resp:
            resp["output"].append(event["item"]["id"])
        return None, None

    def _on_output_item_done(self, event):
        item = self.item_lookup.get(event["item"]["id"])
        if item:
            item["status"] = event["item"]["status"]
        return item, None

    def _on_content_part_added(self, event):
        item = self.item_lookup.get(event["item_id"])
        if item:
            item["content"].append(event["part"])
        return item, None

    def _on_audio_transcript_delta(self, event):
        item = self.item_lookup.get(event["item_id"])
        if not item:
            return None, None
        item["content"][event["content_index"]]["transcript"] += event["delta"]
        item["formatted"]["transcript"] += event["delta"]
        return item, {"transcript": event["delta"]}

    def _on_audio_delta(self, event):
        item = self.item_lookup.get(event["item_id"])
        if not item:
            return None, None
        raw = base64_to_array_buffer(event["delta"]).tobytes()
        return item, {"audio": raw}

    def _on_text_delta(self, event):
        item = self.item_lookup.get(event["item_id"])
        if not item:
            return None, None
        item["content"][event["content_index"]]["text"] += event["delta"]
        item["formatted"]["text"] += event["delta"]
        return item, {"text": event["delta"]}

    def _on_fn_args_delta(self, event):
        item = self.item_lookup.get(event["item_id"])
        if not item:
            return None, None
        item["arguments"] = getattr(item, "arguments", "") + event["delta"]
        if item.get("formatted", {}).get("tool"):
            item["formatted"]["tool"]["arguments"] += event["delta"]
        return item, {"arguments": event["delta"]}


class RealtimeClient(RealtimeEventHandler):
    def __init__(
        self,
        assistant: AssistantService,
        send_callback: Callable[[dict], Awaitable[None]],
    ):
        super().__init__()
        self.assistant = assistant
        self._send_callback = send_callback
        self.current_agent: str = "root"
        self.session_preamble: str = ""
        self.last_user_transcript: str = ""
        self.user_requested_human_followup: bool = False
        self.pending_auto_end: bool = False
        self.suppress_next_auto_response_for_close: bool = False
        self.cancelling_for_forced_closing: bool = False
        self.awaiting_forced_closing: bool = False
        self.forced_closing_line: str = _forced_closing_line()

        # gpt-realtime-2 session config: nested audio.input / audio.output structure
        self.default_session_config = {
            "type": "realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "transcription": {"model": "whisper-1", "language": t("realtime.transcription_language")},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.9,
                        "prefix_padding_ms": 400,
                        "silence_duration_ms": 1000,
                        "create_response": True,
                    },
                },
                "output": {
                    "voice": "sage",
                    "speed": 1.05,
                },
            },
            "tools": [],
            "tool_choice": "auto",
        }
        self.session_config: dict = {}
        self.session_created: bool = False
        self.session_updated: bool = False
        self.input_audio_buffer = bytearray()

        self.realtime = RealtimeAPI()
        self.conversation = RealtimeConversation()
        self._reset_config()
        self._add_api_event_handlers()

    def _reset_config(self):
        self.session_created = False
        self.session_updated = False
        self.session_config = self.default_session_config.copy()
        self.input_audio_buffer = bytearray()
        self.user_requested_human_followup = False

    def _compose_instructions(self, system_message: str) -> str:
        if self.session_preamble:
            return self.session_preamble + "\n" + system_message
        return system_message

    async def _send(self, msg: dict):
        try:
            await self._send_callback(msg)
        except Exception as e:
            logger.warning(f"send_callback failed: {e}")

    # Event handlers wired to RealtimeAPI.

    def _add_api_event_handlers(self):
        ra = self.realtime
        ra.on("server.session.created", self._on_session_created)
        ra.on("server.session.updated", self._on_session_updated)
        ra.on("server.response.created", self._on_response_created)
        ra.on("server.response.done", self._on_response_done)
        ra.on("server.response.output_item.added", self._process_event)
        ra.on("server.response.content_part.added", self._process_event)
        ra.on("server.input_audio_buffer.speech_started", self._on_speech_started)
        ra.on("server.input_audio_buffer.speech_stopped", self._on_speech_stopped)
        ra.on("server.conversation.item.added", self._on_item_created)
        ra.on("server.conversation.item.truncated", self._process_event)
        ra.on("server.conversation.item.deleted", self._process_event)
        ra.on(
            "server.conversation.item.input_audio_transcription.completed",
            self._on_transcription_completed,
        )
        ra.on("server.response.output_audio_transcript.delta", self._on_transcript_delta)
        ra.on("server.response.output_audio.delta", self._on_audio_delta)
        ra.on("server.response.text.delta", self._process_event)
        ra.on("server.response.function_call_arguments.delta", self._process_event)
        ra.on("server.response.output_item.done", self._on_output_item_done)

    def _on_session_created(self, event):
        self.session_created = True

    def _on_session_updated(self, event):
        self.session_updated = True
        session = event.get("session") or {}
        if not isinstance(session, dict):
            session = {}
        audio_out = session.get("audio", {}).get("output", {})
        if not isinstance(audio_out, dict):
            audio_out = {}
        logger.info(
            "Session config applied — voice=%s, speed=%s, language=%s",
            audio_out.get("voice"), audio_out.get("speed"), audio_out.get("language", "N/A"),
        )

    async def _on_response_created(self, event):
        self._process_event(event)

        # 종료 의사 감지 직후 자동 생성되는 일반 응답은 취소하고,
        # 종료 전용 멘트만 한 번 발화하도록 전환한다.
        if self.suppress_next_auto_response_for_close and self.pending_auto_end and not self.awaiting_forced_closing:
            self.suppress_next_auto_response_for_close = False
            self.pending_auto_end = False
            self.awaiting_forced_closing = True
            self.cancelling_for_forced_closing = True
            self.forced_closing_line = _forced_closing_line()
            await self.realtime.send("response.cancel", {})
            await self.create_response(
                instructions=t(
                    "realtime.forced_closing_instruction",
                    line=self.forced_closing_line,
                )
            )
            return

        await self.realtime.send("input_audio_buffer.clear", {})
        await self._send({"type": "session_status", "status": "thinking"})

    async def _on_response_done(self, event):
        resp = event.get("response") or {}
        if not isinstance(resp, dict):
            resp = {}
        status = resp.get("status", "unknown")
        status_details = resp.get("status_details") or {}
        if isinstance(status_details, dict):
            reason = status_details.get("reason", "")
        else:
            reason = str(status_details)
        logger.info("Response done — status=%s, reason=%s", status, reason)
        if status == "cancelled":
            logger.warning("Response cancelled: %s", reason or "barge-in or server interrupt")
            if self.cancelling_for_forced_closing:
                self.cancelling_for_forced_closing = False
                return
            if self.awaiting_forced_closing:
                self.awaiting_forced_closing = False
                await self._send({
                    "type": "auto_session_end",
                    "reason": t("realtime.auto_end_reason"),
                    "close_now": True,
                })
                return

        # 종료 의사 감지 후에는 일반 답변 다음에 종료 전용 멘트를 반드시 한 번 더 발화한다.
        if self.pending_auto_end and not self.awaiting_forced_closing:
            self.pending_auto_end = False
            self.awaiting_forced_closing = True
            self.forced_closing_line = _forced_closing_line()
            await self.create_response(
                instructions=t(
                    "realtime.forced_closing_instruction",
                    line=self.forced_closing_line,
                )
            )
            return

        if self.awaiting_forced_closing:
            self.awaiting_forced_closing = False
            await self._send({
                "type": "auto_session_end",
                "reason": t("realtime.auto_end_reason"),
                "close_after_playback": True,
            })
            return

        await self._send({"type": "session_status", "status": "listening"})

    def _process_event(self, event, *args):
        try:
            item, delta = self.conversation.process_event(event, *args)
        except Exception:
            return None, None
        if item:
            self.dispatch("conversation.updated", {"item": item, "delta": delta})
        return item, delta

    async def _on_speech_started(self, event):
        self._process_event(event)
        self.dispatch("conversation.interrupted", event)
        await self._send({"type": "session_status", "status": "listening"})

    def _on_speech_stopped(self, event):
        self._process_event(event, self.input_audio_buffer)

    def _on_item_created(self, event):
        item, delta = self._process_event(event)
        self.dispatch("conversation.item.appended", {"item": item})
        if item and item["status"] == "completed":
            self.dispatch("conversation.item.completed", {"item": item})

    async def _on_transcription_completed(self, event):
        item, delta = self._process_event(event)
        if delta and delta.get("transcript"):
            user_text = delta["transcript"].strip()
            self.last_user_transcript = user_text
            await self._send({
                "type": "transcript",
                "role": "user",
                "text": user_text,
                "agent": self.current_agent,
                "item_id": event.get("item_id"),
            })
            if self._is_explicit_human_escalation_request(user_text) and not self.user_requested_human_followup:
                self.user_requested_human_followup = True
                await self.update_session(
                    tools=self.assistant.get_tools_for_session(
                        self.current_agent,
                        include_human_followup=True,
                    )
                )
            if self._is_end_gesture(user_text):
                self.awaiting_forced_closing = False
                self.pending_auto_end = True
                self.suppress_next_auto_response_for_close = True

    def _is_end_gesture(self, text: str) -> bool:
        if not text:
            return False
        normalized = re.sub(r"\s+", "", text)
        for pattern in _end_session_patterns():
            if re.search(pattern, text, re.IGNORECASE) or re.search(pattern.replace("\\s*", ""), normalized, re.IGNORECASE):
                return True
        return False

    def _is_compensation_request(self, text: str) -> bool:
        if not text:
            return False
        patterns = (
            r"추가\s*보상",
            r"보상",
            r"쿠폰",
            r"증액",
            r"자동\s*보상",
            r"반복\s*이슈",
            r"품절.*취소",
        )
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _is_explicit_human_escalation_request(self, text: str) -> bool:
        if not text:
            return False
        patterns = (
            r"상담원\s*연결",
            r"사람\s*(이랑|과)\s*얘기",
            r"담당자\s*연락",
            r"재연락",
            r"콜백",
            r"직접\s*연결",
        )
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    async def _on_transcript_delta(self, event):
        item, delta = self._process_event(event)
        if delta and delta.get("transcript"):
            await self._send({
                "type": "transcript",
                "role": "assistant",
                "text": delta["transcript"],
                "agent": self.current_agent,
                "delta": True,
                "item_id": event.get("item_id"),
                "response_id": event.get("response_id"),
            })

    async def _on_audio_delta(self, event):
        item, delta = self._process_event(event)
        if delta and delta.get("audio"):
            b64 = base64.b64encode(delta["audio"]).decode("utf-8")
            await self._send({"type": "audio_output", "data": b64})
            await self._send({"type": "session_status", "status": "speaking"})

    async def _on_output_item_done(self, event):
        item, _ = self._process_event(event)
        if item and item["status"] == "completed":
            self.dispatch("conversation.item.completed", {"item": item})
        formatted = (item or {}).get("formatted") or {}
        tool = formatted.get("tool")
        if tool:
            await self._call_tool(tool)

    # Tool / agent dispatch.

    async def _call_tool(self, tool: dict):
        tool_name = tool["name"]
        effective_tool = tool

        # Deterministic guard:
        # In delivery context, compensation requests should be handled by refund assistant
        # before human follow-up unless user explicitly asked escalation.
        if (
            tool_name == "request_human_followup"
            and not self.user_requested_human_followup
        ):
            if (
                self.current_agent == "Assistant_DeliveryAssistant"
                and self._is_compensation_request(self.last_user_transcript)
            ):
                logger.info(
                    "Reroute tool call from request_human_followup to Assistant_RefundAssistant for compensation request"
                )
                tool_name = "Assistant_RefundAssistant"
                effective_tool = {
                    "name": tool_name,
                    "call_id": tool["call_id"],
                    "arguments": "{}",
                }
            else:
                logger.info(
                    "Blocked request_human_followup because user did not explicitly request callback/escalation"
                )
                await self._send({
                    "type": "tool_call",
                    "name": tool_name,
                    "args": {},
                    "call_id": tool["call_id"],
                    "result": "고객이 상담원 연결이나 콜백을 명시적으로 요청하지 않았습니다. 현재 범위에서 계속 안내하거나, 필요하면 먼저 상담원 연결 의사를 확인하세요.",
                    "status": "done",
                })
                await self.realtime.send(
                    "conversation.item.create",
                    {
                        "item": {
                            "type": "function_call_output",
                            "call_id": tool["call_id"],
                            "output": "고객이 상담원 연결이나 콜백을 명시적으로 요청하지 않았습니다. 현재 범위에서 계속 안내하거나, 필요하면 먼저 상담원 연결 의사를 확인하세요.",
                        }
                    },
                )
                await self.create_response()
                return

        try:
            args = json.loads(effective_tool["arguments"]) if effective_tool["arguments"] else {}
        except json.JSONDecodeError:
            args = {}

        is_agent_switch = bool(re.search(r"assistant", tool_name, re.IGNORECASE))

        await self._send({
            "type": "tool_call",
            "name": tool_name,
            "args": args,
            "call_id": effective_tool["call_id"],
            "status": "calling",
        })

        try:
            if is_agent_switch:
                target = self.assistant.get_agent(tool_name)
                if not target:
                    raise ValueError(f"Unknown agent: {tool_name}")

                old_agent = self.current_agent
                self.current_agent = tool_name

                await self._send({
                    "type": "agent_switch",
                    "from": old_agent,
                    "to": tool_name,
                    "to_name": target.get("name", tool_name),
                })
                await self._send({
                    "type": "tool_call",
                    "name": tool_name,
                    "args": args,
                    "call_id": effective_tool["call_id"],
                    "result": {"switched_to": target.get("name", tool_name)},
                    "status": "done",
                })

                # Must send function_call_output before session.update (Azure requirement)
                await self.realtime.send(
                    "conversation.item.create",
                    {
                        "item": {
                            "type": "function_call_output",
                            "call_id": effective_tool["call_id"],
                            "output": json.dumps({"status": "ok", "agent": tool_name}),
                        }
                    },
                )
                await self.update_session(
                    instructions=self._compose_instructions(target["system_message"]),
                    tools=self.assistant.get_tools_for_session(
                        tool_name,
                        include_human_followup=self.user_requested_human_followup,
                    ),
                )
            else:
                tool_def = self.assistant.find_tool(tool_name)
                if tool_def:
                    result = tool_def["returns"](args)
                else:
                    result = f"Tool '{tool_name}' not found."

                await self._send({
                    "type": "tool_call",
                    "name": tool_name,
                    "args": args,
                    "call_id": effective_tool["call_id"],
                    "result": result,
                    "status": "done",
                })
                await self.realtime.send(
                    "conversation.item.create",
                    {
                        "item": {
                            "type": "function_call_output",
                            "call_id": effective_tool["call_id"],
                            "output": result if isinstance(result, str) else json.dumps(result),
                        }
                    },
                )
        except Exception:
            logger.error(traceback.format_exc())
            await self.realtime.send(
                "conversation.item.create",
                {
                    "item": {
                        "type": "function_call_output",
                        "call_id": effective_tool["call_id"],
                        "output": json.dumps({"error": traceback.format_exc()}),
                    }
                },
            )

        await self.create_response()

    # Connection & session.

    def is_connected(self) -> bool:
        return self.realtime.is_connected()

    async def connect(self, session_preamble: str = "") -> None:
        if self.is_connected():
            raise RuntimeError("Already connected")
        await self.realtime.connect()
        self.session_preamble = session_preamble.strip()
        root = self.assistant.get_agent("root")
        instructions = self._compose_instructions(root["system_message"])
        # instructions is a top-level session field in gpt-realtime-2
        self.session_config["instructions"] = instructions
        self.session_config["tools"] = self.assistant.get_tools_for_session(
            "root",
            include_human_followup=self.user_requested_human_followup,
        )
        await self.update_session()

    async def wait_for_session(self) -> None:
        timeout = 10.0
        elapsed = 0.0
        while not self.session_updated:
            await asyncio.sleep(0.05)
            elapsed += 0.05
            if elapsed >= timeout:
                logger.error("Timeout waiting for session.updated — session config may not be applied")
                break

    async def disconnect(self) -> None:
        self.session_created = False
        self.conversation.clear()
        if self.realtime.is_connected():
            await self.realtime.disconnect()

    async def update_session(self, **kwargs) -> None:
        self.session_config.update(kwargs)
        session = dict(self.session_config)
        if self.realtime.is_connected():
            await self.realtime.send("session.update", {"session": session})

    async def update_voice(self, voice: str, speed: float | None = None) -> None:
        audio = self.session_config.setdefault("audio", {})
        output = audio.setdefault("output", {})
        output["voice"] = voice
        if speed is not None:
            output["speed"] = speed
        self.session_updated = False
        await self.update_session()
        logger.info("Voice change requested: %s (speed=%s)", voice, speed)

    async def append_input_audio(self, buf: bytearray) -> None:
        if len(buf) > 0:
            await self.realtime.send(
                "input_audio_buffer.append",
                {"audio": array_buffer_to_base64(np.frombuffer(buf, dtype=np.int16))},
            )
            self.input_audio_buffer.extend(buf)

    async def create_response(self, instructions: str | None = None) -> None:
        if self.get_turn_detection_type() is None and len(self.input_audio_buffer) > 0:
            await self.realtime.send("input_audio_buffer.commit")
            self.conversation.queue_input_audio(self.input_audio_buffer)
            self.input_audio_buffer = bytearray()
        payload = {}
        if instructions:
            payload = {"response": {"instructions": instructions}}
        await self.realtime.send("response.create", payload)

    def get_turn_detection_type(self) -> str | None:
        return (
            self.session_config
            .get("audio", {})
            .get("input", {})
            .get("turn_detection", {})
            .get("type")
        )

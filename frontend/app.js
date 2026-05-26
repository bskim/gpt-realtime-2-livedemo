// ═══════════════════════════════════════════════════════════
//  Voice CS × GPT-Realtime-2 Demo — app.js
// ═══════════════════════════════════════════════════════════

const SAMPLE_RATE = 24000;

// ── Workflow mock conversations per scenario ──────────────────
const WORKFLOW_SCENARIOS = {
  S1: {
    workflow_resolved: true,
    messages: [
      { role: 'user', text: '배송 얼마나 걸려요?' },
      { role: 'bot',  text: '안녕하세요! 일반 배송은 2-3 영업일, 빠른 배송은 익일 도착입니다.' },
      { role: 'bot',  text: '추가 문의가 있으시면 말씀해 주세요.' },
    ],
    badgeClass: 'ok',
    badgeText: '처리됨',
  },
  S2: {
    workflow_resolved: false,
    messages: [
      { role: 'user',   text: '주문 바꾸고 싶은데요, 배송지도 바꾸고 쿠폰도 쓰고 싶어요.' },
      { role: 'bot',    text: '주문 변경은 가능합니다. 배송지 변경을 먼저 도와드릴게요.' },
      { role: 'user',   text: '아니요, 세 가지를 한 번에 처리하고 싶어요.' },
      { role: 'bot',    text: '죄송합니다, 복합 요청 처리가 어렵습니다...' },
      { role: 'system', text: '⚠ Workflow 미처리 — 복합 의도 처리 불가 → RT-2 전환' },
    ],
    badgeClass: 'failed',
    badgeText: '미처리',
  },
  S3: {
    workflow_resolved: false,
    messages: [
      { role: 'user',   text: '왜 이렇게 배송이 늦어요! 항상 이러네요.' },
      { role: 'bot',    text: '불편을 드려 죄송합니다. 주문번호를 말씀해 주시겠어요?' },
      { role: 'user',   text: '됐어요, 그냥 사람이랑 얘기하고 싶어요!' },
      { role: 'system', text: '⚠ Workflow 미처리 — 감정적 고객 감지 (불만 4회 이상) → RT-2 전환' },
    ],
    badgeClass: 'failed',
    badgeText: '미처리',
  },
  S4: {
    workflow_resolved: false,
    messages: [
      { role: 'user',   text: '저 그게요... 아, 뭐였더라...' },
      { role: 'bot',    text: '네, 말씀해 주세요. 무엇을 도와드릴까요?' },
      { role: 'user',   text: '아 잠깐만요, 그게 아니라... 어...' },
      { role: 'bot',    text: '죄송합니다, 말씀하신 내용을 이해하지 못했습니다.' },
      { role: 'system', text: '⚠ Workflow 미처리 — 의도 파악 불가 (3회 실패) → RT-2 전환' },
    ],
    badgeClass: 'failed',
    badgeText: '미처리',
  },
};

// ── State ────────────────────────────────────────────────
let ws = null;
let audioCtx = null;
let mediaStream = null;
let scriptProcessor = null;
let inputAnalyser = null;
let outputGain = null;
let outputAnalyser = null;
let nextPlayTime = 0;
let currentAgent = 'root';
let isFallback = false;
let streamingMsgEl = null;
let demoState = {
  customer_id:   'CUST-001',
  customer_tier: 'regular',
  order_status:  'normal',
  workflow_resolved: true,
  inquiry_type:  'simple',
  has_coupon:    false,
};

// ── DOM refs ─────────────────────────────────────────────
const btnConnect    = document.getElementById('btnConnect');
const btnRecord     = document.getElementById('btnRecord');
const btnStop       = document.getElementById('btnStop');
const statusChip    = document.getElementById('statusChip');
const pathIndicator = document.getElementById('pathIndicator');
const pathLabel     = document.getElementById('pathLabel');
const messages      = document.getElementById('messages');
const logBody       = document.getElementById('logBody');
const canvasIn      = document.getElementById('canvasInput');
const canvasOut     = document.getElementById('canvasOutput');
const workflowMessages = document.getElementById('workflowMessages');
const workflowBadge    = document.getElementById('workflowBadge');
const transferViz   = document.getElementById('transferViz');
const tfCtx         = document.getElementById('tfCtx');
const transferBanner= document.getElementById('transferBanner');
const archPrimary   = document.getElementById('archPrimary');
const archRt2       = document.getElementById('archRt2');
const currentAgentCard = document.getElementById('currentAgentCard');
const caDot         = document.getElementById('caDot');
const caLabel       = document.getElementById('caLabel');
const caSub         = document.getElementById('caSub');

// ═══════════════════════════════════════════════════════════
//  WebSocket
// ═══════════════════════════════════════════════════════════
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.binaryType = 'arraybuffer';

  ws.onopen = () => {
    setStatus('connecting');
    sendDemoState();
  };

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    handleServerMsg(msg);
  };

  ws.onclose = () => {
    setStatus('disconnected');
    btnConnect.disabled = false;
    btnRecord.disabled  = true;
    btnStop.disabled    = true;
    ws = null;
  };

  ws.onerror = (e) => console.error('WS error', e);
  btnConnect.disabled = true;
}

function sendWs(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function sendDemoState() {
  sendWs({ type: 'demo_inject', payload: { ...demoState } });
}

// ═══════════════════════════════════════════════════════════
//  Server message handler
// ═══════════════════════════════════════════════════════════
function handleServerMsg(msg) {
  switch (msg.type) {
    case 'session_status':    onSessionStatus(msg.status); break;
    case 'transfer_context':  onTransferContext(msg); break;
    case 'audio_output':      onAudioOutput(msg.data); break;
    case 'transcript':        onTranscript(msg); break;
    case 'agent_switch':      onAgentSwitch(msg); break;
    case 'tool_call':         onToolCall(msg); break;
    case 'demo_state':        demoState = msg.state; break;
    case 'error':             addLogEntry(`<div style="color:var(--red);font-size:11px">오류: ${msg.message}</div>`); break;
  }
}

// ── Session status ───────────────────────────────────────
function onSessionStatus(status) {
  setStatus(status);
  if (status === 'connected') {
    btnRecord.disabled = false;
    btnStop.disabled   = false;
  }
}

function setStatus(s) {
  statusChip.className = `status-chip ${s}`;
  statusChip.textContent = {
    disconnected: 'disconnected',
    connecting:   'connecting...',
    connected:    'connected',
    listening:    'listening',
    thinking:     'thinking',
    speaking:     'speaking',
  }[s] || s;
}

// ── Transfer context ─────────────────────────────────────
function onTransferContext(msg) {
  isFallback = msg.is_fallback;

  if (isFallback) {
    // Header path indicator
    pathIndicator.className = 'path-indicator fallback';
    pathLabel.textContent = '🔴 RT-2 FALLBACK';

    // Architecture highlight
    archPrimary.classList.remove('active-primary');
    archRt2.classList.add('active-rt2');

    // Transfer banner in chat
    transferBanner.classList.add('visible');

    // Context panel in left panel
    if (msg.context) {
      transferViz.classList.add('visible');
      tfCtx.textContent = msg.context;
    }

    // Log entry
    if (msg.context) {
      addContextBadge(msg.context);
    }
  } else {
    pathIndicator.className = 'path-indicator primary';
    pathLabel.textContent = '✓ PRIMARY PATH (Workflow)';
    archPrimary.classList.add('active-primary');
  }
}

function addContextBadge(ctx) {
  const el = document.createElement('div');
  el.className = 'ctx-badge';
  el.innerHTML = `<b>🔄 전환 컨텍스트 주입됨</b>${escHtml(ctx)}`;
  insertLogEntry(el);
}

// ── Audio output ─────────────────────────────────────────
function onAudioOutput(b64) {
  if (!audioCtx) return;
  const raw   = atob(b64);
  const int16 = new Int16Array(raw.length / 2);
  for (let i = 0; i < int16.length; i++) {
    int16[i] = (raw.charCodeAt(i * 2)) | (raw.charCodeAt(i * 2 + 1) << 8);
  }
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

  const buf = audioCtx.createBuffer(1, float32.length, SAMPLE_RATE);
  buf.copyToChannel(float32, 0);

  const src = audioCtx.createBufferSource();
  src.buffer = buf;
  src.connect(outputGain);

  const now = audioCtx.currentTime;
  if (nextPlayTime < now) nextPlayTime = now + 0.05;
  src.start(nextPlayTime);
  nextPlayTime += buf.duration;
}

// ── Transcript ───────────────────────────────────────────
let currentStreamId = null;

function onTranscript(msg) {
  if (msg.role === 'user') {
    finishStreaming();
    appendMsg('user', msg.text, null);
    return;
  }

  // assistant delta streaming
  if (msg.delta) {
    if (!streamingMsgEl) {
      streamingMsgEl = appendMsg('ai', '', msg.agent);
      streamingMsgEl.querySelector('.msg-text').classList.add('streaming');
    }
    streamingMsgEl.querySelector('.msg-text').textContent += msg.text;
    messages.scrollTop = messages.scrollHeight;
  } else {
    finishStreaming();
    appendMsg('ai', msg.text, msg.agent);
  }
}

function finishStreaming() {
  if (streamingMsgEl) {
    streamingMsgEl.querySelector('.msg-text').classList.remove('streaming');
    streamingMsgEl = null;
  }
}

function appendMsg(role, text, agentId) {
  finishStreaming();
  const wrap = document.createElement('div');
  wrap.className = `msg msg-${role === 'user' ? 'user' : 'ai'}`;

  if (role !== 'user' && agentId) {
    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    const tag = document.createElement('span');
    tag.className = `agent-tag ${agentClass(agentId)}`;
    tag.textContent = agentDisplayName(agentId);
    meta.appendChild(tag);
    wrap.appendChild(meta);
  }

  const txt = document.createElement('div');
  txt.className = 'msg-text';
  txt.textContent = text;
  wrap.appendChild(txt);

  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

// ── Agent switch ─────────────────────────────────────────
function onAgentSwitch(msg) {
  currentAgent = msg.to;
  updateAgentCard(msg.to, msg.to_name);

  const el = document.createElement('div');
  el.className = 'switch-card';
  el.innerHTML = `
    <span class="agent-tag ${agentClass(msg.from)}">${agentDisplayName(msg.from)}</span>
    <span class="sw-arrow">→</span>
    <span class="agent-tag ${agentClass(msg.to)}">${msg.to_name || agentDisplayName(msg.to)}</span>
  `;
  insertLogEntry(el);
}

function updateAgentCard(agentId, name) {
  const cls = agentKey(agentId);
  caDot.className = `ca-dot ${cls}`;
  caLabel.textContent = name || agentDisplayName(agentId);
  caSub.textContent = agentId;
}

// ── Tool call ─────────────────────────────────────────────
const toolCardMap = {};

function onToolCall(msg) {
  const key = `${msg.name}-${msg.args ? JSON.stringify(msg.args) : ''}`;

  if (msg.status === 'calling') {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.innerHTML = `
      <div class="tool-head">
        <span class="tool-name">${escHtml(msg.name)}</span>
        <span class="tool-badge calling" id="tb-${key}">호출 중...</span>
      </div>
      <div class="tool-body">
        <div class="tool-lbl">Args</div>
        <div class="tool-json">${escHtml(JSON.stringify(msg.args, null, 2))}</div>
      </div>
    `;
    toolCardMap[key] = card;
    insertLogEntry(card);
  } else if (msg.status === 'done') {
    const card = toolCardMap[key];
    if (card) {
      const badge = card.querySelector(`#tb-${key}`);
      if (badge) { badge.className = 'tool-badge done'; badge.textContent = '완료'; }
      card.querySelector('.tool-body').insertAdjacentHTML('beforeend', `
        <div class="tool-lbl">Result</div>
        <div class="tool-json">${escHtml(typeof msg.result === 'string' ? msg.result : JSON.stringify(msg.result, null, 2))}</div>
      `);
      delete toolCardMap[key];
    }
  }
}

// ═══════════════════════════════════════════════════════════
//  Audio capture
// ═══════════════════════════════════════════════════════════
async function startRecording() {
  audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });

  // Output routing
  outputGain    = audioCtx.createGain();
  outputAnalyser = audioCtx.createAnalyser();
  outputGain.connect(audioCtx.destination);
  outputGain.connect(outputAnalyser);
  outputAnalyser.fftSize = 256;

  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  const source = audioCtx.createMediaStreamSource(mediaStream);

  inputAnalyser = audioCtx.createAnalyser();
  inputAnalyser.fftSize = 256;
  source.connect(inputAnalyser);

  scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1);
  source.connect(scriptProcessor);
  scriptProcessor.connect(audioCtx.destination);

  scriptProcessor.onaudioprocess = (e) => {
    const float32 = e.inputBuffer.getChannelData(0);
    const int16   = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const v = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = v < 0 ? v * 32768 : v * 32767;
    }
    sendWs({ type: 'audio_input', data: arrayBufferToBase64(int16.buffer) });
  };

  nextPlayTime = 0;
  drawWaveforms();
  btnRecord.disabled = true;
  btnStop.disabled   = false;
}

function stopRecording() {
  if (scriptProcessor) { scriptProcessor.disconnect(); scriptProcessor = null; }
  if (mediaStream)     { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
  if (audioCtx)        { audioCtx.close(); audioCtx = null; }
  btnRecord.disabled = false;
  btnStop.disabled   = true;
  setStatus('connected');
}

// ═══════════════════════════════════════════════════════════
//  Waveform drawing
// ═══════════════════════════════════════════════════════════
function drawWaveforms() {
  if (!audioCtx) return;
  requestAnimationFrame(drawWaveforms);
  drawAnalyser(canvasIn,  inputAnalyser,  '#39d353');
  drawAnalyser(canvasOut, outputAnalyser, '#bc8cff');
}

function drawAnalyser(canvas, analyser, color) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight;
  ctx.clearRect(0, 0, W, H);

  if (!analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteTimeDomainData(data);

  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth   = 1.5;
  const step = W / data.length;
  for (let i = 0; i < data.length; i++) {
    const y = ((data[i] / 128) - 1) * (H / 2) + H / 2;
    i === 0 ? ctx.moveTo(0, y) : ctx.lineTo(i * step, y);
  }
  ctx.stroke();
}

// ═══════════════════════════════════════════════════════════
//  Demo control panel
// ═══════════════════════════════════════════════════════════
document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const id = btn.dataset.preset;
    applyPreset(id);
  });
});

function applyPreset(id) {
  const scenario = WORKFLOW_SCENARIOS[id];
  if (!scenario) return;

  // Update Workflow simulation panel
  workflowMessages.innerHTML = '';
  scenario.messages.forEach(m => {
    const el = document.createElement('div');
    el.className = `workflow-msg ${m.role}`;
    el.textContent = m.text;
    workflowMessages.appendChild(el);
  });
  workflowBadge.className = `workflow-badge ${scenario.badgeClass}`;
  workflowBadge.textContent = scenario.badgeText;

  // Show/hide transfer viz
  transferViz.classList.toggle('visible', !scenario.workflow_resolved);

  // Sync toggle buttons
  const presetStateMap = {
    S1: { customer_tier: 'regular', order_status: 'normal',           inquiry_type: 'simple',    has_coupon: false },
    S2: { customer_tier: 'vip',     order_status: 'normal',           inquiry_type: 'complex',   has_coupon: true  },
    S3: { customer_tier: 'problem', order_status: 'delayed',          inquiry_type: 'emotional', has_coupon: false },
    S4: { customer_tier: 'regular', order_status: 'refund_requested', inquiry_type: 'ambiguous', has_coupon: false },
  };
  const presetState = presetStateMap[id];
  if (presetState) {
    Object.entries(presetState).forEach(([field, val]) => {
      syncToggle(field, val);
      demoState[field] = val;
    });
    demoState.workflow_resolved = scenario.workflow_resolved;
  }

  // Send to backend
  sendWs({ type: 'demo_inject', payload: { preset: id } });
}

function syncToggle(field, val) {
  document.querySelectorAll(`[data-field="${field}"]`).forEach(b => {
    b.classList.toggle('active', b.dataset.val === String(val));
  });
}

// Toggle buttons (manual)
document.querySelectorAll('.toggle-btn[data-field]').forEach(btn => {
  btn.addEventListener('click', () => {
    const field = btn.dataset.field;
    let   val   = btn.dataset.val;
    if (val === 'true') val = true;
    else if (val === 'false') val = false;

    // Single-select within same field (except boolean fields)
    if (typeof val === 'string') {
      document.querySelectorAll(`[data-field="${field}"]`).forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    } else {
      btn.classList.toggle('active');
      val = btn.classList.contains('active');
    }
    demoState[field] = val;
    sendWs({ type: 'demo_inject', payload: { [field]: val } });
  });
});

// Customer ID input
document.getElementById('customerIdInput').addEventListener('change', (e) => {
  demoState.customer_id = e.target.value;
  sendWs({ type: 'demo_inject', payload: { customer_id: e.target.value } });
});

// ═══════════════════════════════════════════════════════════
//  Button handlers
// ═══════════════════════════════════════════════════════════
btnConnect.addEventListener('click', () => {
  connect();
});

btnRecord.addEventListener('click', () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  startRecording().catch(err => {
    console.error('Mic error:', err);
    alert('마이크 접근 권한이 필요합니다.');
  });
});

btnStop.addEventListener('click', () => {
  stopRecording();
  sendWs({ type: 'session_end' });
});

// ═══════════════════════════════════════════════════════════
//  Helpers
// ═══════════════════════════════════════════════════════════
function addLogEntry(html) {
  const el = document.createElement('div');
  el.innerHTML = html;
  insertLogEntry(el.firstChild || el);
}

function insertLogEntry(el) {
  // Insert after the current-agent-card (index 2 = after arch diagram + agent card)
  const anchor = currentAgentCard;
  anchor.insertAdjacentElement('afterend', el);
  logBody.scrollTop = logBody.scrollHeight;
}

function agentKey(agentId) {
  if (!agentId) return '';
  const id = agentId.toLowerCase();
  if (id.includes('order'))        return 'order';
  if (id.includes('delivery'))     return 'delivery';
  if (id.includes('refund'))       return 'refund';
  if (id.includes('product'))      return 'product';
  if (id.includes('membership'))   return 'membership';
  if (id.includes('afterservice')) return 'afterservice';
  return '';
}

function agentClass(agentId) {
  return 'tag-' + (agentKey(agentId) || 'root');
}

function agentDisplayName(agentId) {
  if (!agentId) return 'Root';
  const id = agentId.toLowerCase();
  if (id.includes('order'))        return '주문 관리';
  if (id.includes('delivery'))     return '배송 관리';
  if (id.includes('refund'))       return '환불/교환';
  if (id.includes('product'))      return '상품 문의';
  if (id.includes('membership'))   return '회원/포인트';
  if (id.includes('afterservice')) return 'A/S 불량';
  return '상담 안내';
}

function arrayBufferToBase64(buffer) {
  const bytes  = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function escHtml(str) {
  if (typeof str !== 'string') str = JSON.stringify(str);
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

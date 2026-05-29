// Voice CS × GPT-Realtime-2 demo client.

const SAMPLE_RATE = 24000;

// Build per-locale workflow scenarios from i18n strings.
function buildWorkflowScenarios() {
  const scenarios = {};
  ['S1', 'S2', 'S3', 'S4'].forEach(id => {
    const messages = [];
    for (let i = 1; i <= 8; i++) {
      const roleKey = `workflow.${id}.msg.${i}.role`;
      const textKey = `workflow.${id}.msg.${i}.text`;
      const role = window.i18n.t(roleKey);
      const text = window.i18n.t(textKey);
      if (role === roleKey || text === textKey) break;
      messages.push({ role, text });
    }
    scenarios[id] = {
      workflow_resolved: id === 'S1',
      messages,
      badgeClass: window.i18n.t(`workflow.${id}.badge_class`),
      badgeText: window.i18n.t(`workflow.${id}.badge`),
    };
  });
  return scenarios;
}

let WORKFLOW_SCENARIOS = {};

// State.
let ws = null;
let audioCtx = null;
let mediaStream = null;
let scriptProcessor = null;
let inputAnalyser = null;
let outputGain = null;
let outputAnalyser = null;
let nextPlayTime = 0;
let pendingPlaybackCount = 0;
let currentAgent = 'root';
let isFallback = false;
let isSpeaking = false;
let autoEndPending = false;
let isEndingSession = false;
let currentStatus = 'disconnected';
let streamingMsgEl = null;
let streamingItemId = null;
let activePresetId = null;
let demoState = {
  customer_id:   'CUST-001',
  recent_order_id: 'ORD-20260527-1001',
  recent_order_at: '2026-05-25 14:20 KST',
  repeat_count:  0,
  seller_fault:  false,
  order_status_history: [],
  customer_tier: 'regular',
  request_tone:  'normal',
  order_status:  'normal',
  workflow_resolved: true,
  inquiry_type:  'simple',
  has_coupon:    false,
  voice:         'sage',
  speed:         1.05,
  locale:        'ko',
};

// DOM refs.
const btnStart      = document.getElementById('btnStart');
const btnEnd        = document.getElementById('btnEnd');
const statusChip    = document.getElementById('statusChip');
const messages      = document.getElementById('messages');
const logBody       = document.getElementById('logBody');
const canvasIn      = document.getElementById('canvasInput');
const canvasOut     = document.getElementById('canvasOutput');
const workflowMessages = document.getElementById('workflowMessages');
const workflowBadge    = document.getElementById('workflowBadge');
const transferViz   = document.getElementById('transferViz');
const tfCtx         = document.getElementById('tfCtx');
const transferBanner= document.getElementById('transferBanner');
const currentAgentCard = document.getElementById('currentAgentCard');
const caDot         = document.getElementById('caDot');
const caLabel       = document.getElementById('caLabel');
const caSub         = document.getElementById('caSub');
const voiceSelect   = document.getElementById('voiceSelect');
const btnVoiceApply = document.getElementById('btnVoiceApply');
const voiceSpeedRange = document.getElementById('voiceSpeedRange');
const voiceSpeedValue = document.getElementById('voiceSpeedValue');
const presetButtons = Array.from(document.querySelectorAll('.preset-btn'));
const stateButtons  = Array.from(document.querySelectorAll('.toggle-btn[data-field]'));
const customerIdInput = document.getElementById('customerIdInput');
const recentOrderIdInput = document.getElementById('recentOrderIdInput');
const recentOrderAtInput = document.getElementById('recentOrderAtInput');
const repeatCountInput = document.getElementById('repeatCountInput');
const orderStatusHistoryInput = document.getElementById('orderStatusHistoryInput');
const localeButtons = Array.from(document.querySelectorAll('.locale-btn'));

function parseHistoryInput(raw) {
  if (!raw || typeof raw !== 'string') return [];
  return raw.split(',').map(v => v.trim()).filter(Boolean);
}

function formatHistoryInput(history) {
  if (!Array.isArray(history)) return '';
  return history.join(', ');
}

function formatOrderAtForServer(localDateTime) {
  if (!localDateTime) return '';
  return `${localDateTime.replace('T', ' ')} KST`;
}

function formatOrderAtForInput(serverDateTime) {
  if (!serverDateTime) return '';
  return String(serverDateTime).replace(' KST', '').replace(' ', 'T').slice(0, 16);
}

function presetHistoryFor(id) {
  const key = `preset.${id}.history`;
  const raw = window.i18n.t(key);
  if (!raw || raw === key) return [];
  return parseHistoryInput(raw);
}

function setSessionLock(lock) {
  btnVoiceApply.disabled = lock;
  voiceSelect.disabled = lock;
  voiceSpeedRange.disabled = lock;
  presetButtons.forEach(btn => { btn.disabled = lock; });
  stateButtons.forEach(btn => { btn.disabled = lock; });
  customerIdInput.disabled = lock;
  recentOrderIdInput.disabled = lock;
  recentOrderAtInput.disabled = lock;
  repeatCountInput.disabled = lock;
  orderStatusHistoryInput.disabled = lock;
  localeButtons.forEach(btn => { btn.disabled = lock; });
}

function resetConversationUI() {
  finishStreaming();
  pendingPlaybackCount = 0;
  nextPlayTime = 0;
  autoEndPending = false;
  isEndingSession = false;

  transferBanner.classList.remove('visible');
  messages.innerHTML = '';
  messages.appendChild(transferBanner);

  let node = currentAgentCard.nextElementSibling;
  while (node) {
    const next = node.nextElementSibling;
    node.remove();
    node = next;
  }

  currentAgent = 'root';
  caDot.className = 'ca-dot';
  caLabel.textContent = window.i18n.t('log.current_agent.idle');
  caSub.textContent = '';

  transferViz.classList.remove('visible');
  tfCtx.textContent = '';

  Object.keys(toolCardMap).forEach(k => delete toolCardMap[k]);
}

// WebSocket connection.
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
    btnStart.disabled = false;
    btnEnd.disabled   = true;
    setSessionLock(false);
    isEndingSession = false;
    ws = null;
  };

  ws.onerror = (e) => console.error('WS error', e);
  btnStart.disabled = true;
  setSessionLock(true);
}

function sendWs(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function sendDemoState() {
  sendWs({ type: 'demo_inject', payload: { ...demoState, locale: window.i18n.locale } });
}

// Server message handler.
function handleServerMsg(msg) {
  switch (msg.type) {
    case 'session_status':    onSessionStatus(msg.status); break;
    case 'transfer_context':  onTransferContext(msg); break;
    case 'audio_output':      onAudioOutput(msg.data); break;
    case 'transcript':        onTranscript(msg); break;
    case 'agent_switch':      onAgentSwitch(msg); break;
    case 'tool_call':         onToolCall(msg); break;
    case 'demo_state':        onDemoState(msg.state); break;
    case 'auto_session_end':  onAutoSessionEnd(msg); break;
    case 'error':             addLogEntry(`<div style="color:var(--red);font-size:11px">${escHtml(window.i18n.t('log.error_prefix', { message: msg.message }))}</div>`); break;
  }
}

function onAutoSessionEnd(msg) {
  const reason = msg?.reason || window.i18n.t('log.auto_end.default_reason');
  addLogEntry(`<div style="font-size:11px;color:var(--muted)">${escHtml(window.i18n.t('log.auto_end', { reason }))}</div>`);
  if (msg?.close_now) {
    endSession();
    return;
  }
  autoEndPending = true;
  tryFinalizeAutoEnd();
}

function onDemoState(state) {
  demoState = { ...demoState, ...state };
  customerIdInput.value = state.customer_id || '';
  recentOrderIdInput.value = state.recent_order_id || '';
  recentOrderAtInput.value = formatOrderAtForInput(state.recent_order_at || '');
  repeatCountInput.value = Number.isFinite(Number(state.repeat_count)) ? String(Number(state.repeat_count)) : '0';
  orderStatusHistoryInput.value = formatHistoryInput(state.order_status_history);
  if (typeof state.speed === 'number') {
    const safeSpeed = Math.min(1.25, Math.max(0.75, state.speed));
    voiceSpeedRange.value = safeSpeed.toFixed(2);
    voiceSpeedValue.textContent = `${safeSpeed.toFixed(2)}x`;
  }
}

// Session status.
function onSessionStatus(status) {
  if (status === 'thinking') {
    finishStreaming();
  }
  setStatus(status);
  if (status === 'connected') {
    btnEnd.disabled = false;
    setSessionLock(true);
    startRecording().catch(err => {
      console.error('Mic error:', err);
      alert(window.i18n.t('alert.mic_required'));
    });
  }
}

function setStatus(s) {
  currentStatus = s;
  statusChip.className = `status-chip ${s}`;
  isSpeaking = (s === 'speaking');
  const key = `status.${s}`;
  const txt = window.i18n.t(key);
  statusChip.textContent = (txt === key) ? s : txt;
  tryFinalizeAutoEnd();
}

function tryFinalizeAutoEnd() {
  if (!autoEndPending || !ws) return;
  if (pendingPlaybackCount === 0 && currentStatus !== 'speaking') {
    autoEndPending = false;
    endSession();
  }
}

// Transfer context.
function onTransferContext(msg) {
  isFallback = msg.is_fallback;

  if (isFallback) {
    transferBanner.classList.add('visible');
    if (msg.context) {
      transferViz.classList.add('visible');
      tfCtx.textContent = msg.context;
      addContextBadge(msg.context);
    }
  }
}

function addContextBadge(ctx) {
  const el = document.createElement('div');
  el.className = 'ctx-badge';
  el.innerHTML = `<b>${escHtml(window.i18n.t('log.context_badge.title'))}</b>${escHtml(ctx)}`;
  insertLogEntry(el);
}

// Audio output.
function onAudioOutput(b64) {
  if (!audioCtx) return;
  if (currentStatus !== 'thinking') setStatus('speaking');

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
  pendingPlaybackCount += 1;
  src.onended = () => {
    pendingPlaybackCount = Math.max(0, pendingPlaybackCount - 1);
    if (pendingPlaybackCount === 0 && currentStatus === 'speaking' && ws) {
      setStatus('listening');
    }
    tryFinalizeAutoEnd();
  };

  const now = audioCtx.currentTime;
  if (nextPlayTime < now) nextPlayTime = now + 0.05;
  src.start(nextPlayTime);
  nextPlayTime += buf.duration;
}

// Transcript.
function onTranscript(msg) {
  if (msg.role === 'user') {
    finishStreaming();
    streamingItemId = null;
    appendMsg('user', msg.text, null);
    return;
  }

  if (msg.delta) {
    const incomingItemId = msg.item_id || null;
    const streamChanged = incomingItemId && streamingItemId && incomingItemId !== streamingItemId;
    if (streamChanged) {
      finishStreaming();
    }
    if (!streamingMsgEl) {
      streamingMsgEl = appendMsg('ai', '', msg.agent);
      streamingMsgEl.querySelector('.msg-text').classList.add('streaming');
      streamingItemId = incomingItemId;
    }
    streamingMsgEl.querySelector('.msg-text').textContent += msg.text;
    messages.scrollTop = messages.scrollHeight;
  } else {
    finishStreaming();
    streamingItemId = null;
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

// Agent switch.
function onAgentSwitch(msg) {
  finishStreaming();
  streamingItemId = null;
  currentAgent = msg.to;
  updateAgentCard(msg.to, msg.to_name);

  const el = document.createElement('div');
  el.className = 'switch-card';
  el.innerHTML = `
    <span class="agent-tag ${agentClass(msg.from)}">${escHtml(agentDisplayName(msg.from))}</span>
    <span class="sw-arrow">→</span>
    <span class="agent-tag ${agentClass(msg.to)}">${escHtml(msg.to_name || agentDisplayName(msg.to))}</span>
  `;
  insertLogEntry(el);

  const chatEl = document.createElement('div');
  chatEl.className = 'msg msg-agent-switch';
  chatEl.innerHTML = `<span class="agent-tag ${agentClass(msg.to)}">${escHtml(msg.to_name || agentDisplayName(msg.to))}</span>${escHtml(window.i18n.t('agent.switch_suffix'))}`;
  messages.appendChild(chatEl);
  messages.scrollTop = messages.scrollHeight;
}

function updateAgentCard(agentId, name) {
  const cls = agentKey(agentId);
  caDot.className = `ca-dot ${cls}`;
  caLabel.textContent = name || agentDisplayName(agentId);
  caSub.textContent = agentId;
}

// Tool call.
const toolCardMap = {};

function onToolCall(msg) {
  const key = msg.call_id || `tc-${Date.now()}`;

  if (msg.status === 'calling') {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.dataset.callId = key;
    card.innerHTML = `
      <div class="tool-head">
        <span class="tool-name">${escHtml(msg.name)}</span>
        <span class="tool-badge calling">${escHtml(window.i18n.t('log.tool.calling'))}</span>
      </div>
      <div class="tool-body">
        <div class="tool-lbl">${escHtml(window.i18n.t('log.tool.args'))}</div>
        <div class="tool-json">${escHtml(JSON.stringify(msg.args, null, 2))}</div>
      </div>
    `;
    toolCardMap[key] = card;
    insertLogEntry(card);

    addToolCallToChat(msg.name, msg.args);
  } else if (msg.status === 'done') {
    const card = toolCardMap[key];
    if (card) {
      const badge = card.querySelector('.tool-badge');
      if (badge) { badge.className = 'tool-badge done'; badge.textContent = window.i18n.t('log.tool.done'); }
      card.querySelector('.tool-body').insertAdjacentHTML('beforeend', `
        <div class="tool-lbl">${escHtml(window.i18n.t('log.tool.result'))}</div>
        <div class="tool-json">${escHtml(typeof msg.result === 'string' ? msg.result : JSON.stringify(msg.result, null, 2))}</div>
      `);
      delete toolCardMap[key];
    }

    if (msg.result) {
      addToolResultToChat(msg.name, msg.result);
    }
  }
}

function addToolCallToChat(name, args) {
  finishStreaming();
  streamingItemId = null;
  const wrap = document.createElement('div');
  wrap.className = 'msg msg-tool';
  const argsStr = args && Object.keys(args).length > 0 ? ` (${Object.values(args).join(', ')})` : '';
  wrap.innerHTML = `<span class="tool-icon">⚡</span><span class="tool-inline-name">${escHtml(name)}</span>${escHtml(argsStr)}`;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
}

function addToolResultToChat(name, result) {
  finishStreaming();
  streamingItemId = null;
  const wrap = document.createElement('div');
  wrap.className = 'msg msg-tool-result';
  const text = typeof result === 'string' ? result : JSON.stringify(result);
  const short = text.length > 80 ? text.substring(0, 80) + '...' : text;
  wrap.innerHTML = `<span class="tool-icon">✓</span><span class="tool-inline-result">${escHtml(short)}</span>`;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
}

// Audio capture.
async function startRecording() {
  audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });

  outputGain    = audioCtx.createGain();
  outputAnalyser = audioCtx.createAnalyser();
  outputGain.connect(audioCtx.destination);
  outputGain.connect(outputAnalyser);
  outputAnalyser.fftSize = 256;

  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    video: false,
  });
  const source = audioCtx.createMediaStreamSource(mediaStream);

  inputAnalyser = audioCtx.createAnalyser();
  inputAnalyser.fftSize = 256;
  source.connect(inputAnalyser);

  scriptProcessor = audioCtx.createScriptProcessor(4096, 1, 1);
  source.connect(scriptProcessor);
  scriptProcessor.connect(audioCtx.destination);

  scriptProcessor.onaudioprocess = (e) => {
    if (isSpeaking) return;
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
}

function stopRecording() {
  if (scriptProcessor) { scriptProcessor.disconnect(); scriptProcessor = null; }
  if (mediaStream)     { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
  if (audioCtx)        { audioCtx.close(); audioCtx = null; }
  pendingPlaybackCount = 0;
  nextPlayTime = 0;
  setStatus('disconnected');
}

// Waveform drawing.
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

// Preset buttons.
document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const id = btn.dataset.preset;
    applyPreset(id);
  });
});

function renderWorkflowMessages(scenario) {
  workflowMessages.innerHTML = '';
  scenario.messages.forEach(m => {
    const el = document.createElement('div');
    el.className = `workflow-msg ${m.role}`;
    el.textContent = m.text;
    workflowMessages.appendChild(el);
  });
  workflowBadge.className = `workflow-badge ${scenario.badgeClass}`;
  workflowBadge.textContent = scenario.badgeText;
}

function applyPreset(id) {
  const scenario = WORKFLOW_SCENARIOS[id];
  if (!scenario) return;

  activePresetId = id;
  renderWorkflowMessages(scenario);
  transferViz.classList.toggle('visible', !scenario.workflow_resolved);

  const presetStateMap = {
    S1: { customer_tier: 'regular', request_tone: 'normal',    order_status: 'normal',           inquiry_type: 'simple',    has_coupon: false, repeat_count: 0, seller_fault: false, order_status_history: [] },
    S2: { customer_tier: 'vip',     request_tone: 'urgent',    order_status: 'normal',           inquiry_type: 'complex',   has_coupon: true,  repeat_count: 0, seller_fault: false, order_status_history: [] },
    S3: { customer_tier: 'regular', request_tone: 'complaint', order_status: 'delayed',          inquiry_type: 'simple',    has_coupon: false, repeat_count: 2, seller_fault: true,  order_status_history: presetHistoryFor('S3') },
    S4: { customer_tier: 'regular', request_tone: 'normal',    order_status: 'refund_requested', inquiry_type: 'ambiguous', has_coupon: false, repeat_count: 1, seller_fault: false, order_status_history: presetHistoryFor('S4') },
  };
  const presetState = presetStateMap[id];
  if (presetState) {
    Object.entries(presetState).forEach(([field, val]) => {
      syncToggle(field, val);
      demoState[field] = val;
    });
    demoState.workflow_resolved = scenario.workflow_resolved;
    syncToggle('workflow_resolved', scenario.workflow_resolved);
    orderStatusHistoryInput.value = formatHistoryInput(presetState.order_status_history);
    repeatCountInput.value = String(presetState.repeat_count);
  }

  sendWs({ type: 'demo_inject', payload: { preset: id, locale: window.i18n.locale } });
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

customerIdInput.addEventListener('change', (e) => {
  demoState.customer_id = e.target.value;
  sendWs({ type: 'demo_inject', payload: { customer_id: e.target.value } });
});

recentOrderIdInput.addEventListener('change', (e) => {
  demoState.recent_order_id = e.target.value;
  sendWs({ type: 'demo_inject', payload: { recent_order_id: e.target.value } });
});

recentOrderAtInput.addEventListener('change', (e) => {
  const formatted = formatOrderAtForServer(e.target.value);
  demoState.recent_order_at = formatted;
  sendWs({ type: 'demo_inject', payload: { recent_order_at: formatted } });
});

repeatCountInput.addEventListener('change', (e) => {
  const parsed = Math.max(0, Number.parseInt(e.target.value || '0', 10) || 0);
  demoState.repeat_count = parsed;
  e.target.value = String(parsed);
  sendWs({ type: 'demo_inject', payload: { repeat_count: parsed } });
});

orderStatusHistoryInput.addEventListener('change', (e) => {
  const history = parseHistoryInput(e.target.value);
  demoState.order_status_history = history;
  e.target.value = formatHistoryInput(history);
  sendWs({ type: 'demo_inject', payload: { order_status_history: history } });
});

voiceSpeedRange.addEventListener('input', (e) => {
  const speed = Number(e.target.value);
  demoState.speed = speed;
  voiceSpeedValue.textContent = `${speed.toFixed(2)}x`;
});

btnVoiceApply.addEventListener('click', () => {
  if (btnVoiceApply.disabled) return;
  const voice = voiceSelect.value;
  const speed = Number(voiceSpeedRange.value);
  demoState.voice = voice;
  demoState.speed = speed;
  sendWs({ type: 'demo_inject', payload: { voice, speed } });
  addLogEntry(`<div style="font-size:11px;color:var(--muted)">${escHtml(window.i18n.t('log.voice_applied', { voice, speed: speed.toFixed(2) }))}</div>`);
});

// Locale toggle.
function syncLocaleButtons() {
  localeButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.locale === window.i18n.locale);
  });
}

localeButtons.forEach(btn => {
  btn.addEventListener('click', async () => {
    if (btn.disabled) return;
    const target = btn.dataset.locale;
    if (target === window.i18n.locale) return;
    await window.i18n.setLocale(target);
  });
});

// Button handlers.
btnStart.addEventListener('click', () => {
  resetConversationUI();
  connect();
});

btnEnd.addEventListener('click', () => {
  endSession();
});

function endSession() {
  if (isEndingSession) return;
  isEndingSession = true;
  stopRecording();
  sendWs({ type: 'session_end' });
  if (ws) ws.close();
  btnStart.disabled = false;
  btnEnd.disabled   = true;
  setSessionLock(false);
}

// Helpers.
function addLogEntry(html) {
  const el = document.createElement('div');
  el.innerHTML = html;
  insertLogEntry(el.firstChild || el);
}

function insertLogEntry(el) {
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
  const key = agentKey(agentId) || 'root';
  return window.i18n.t(`agent.${key}`);
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

// i18n lifecycle hooks.
function refreshLocaleDependentUi() {
  WORKFLOW_SCENARIOS = buildWorkflowScenarios();
  syncLocaleButtons();
  demoState.locale = window.i18n.locale;
  if (!ws) {
    caLabel.textContent = window.i18n.t('log.current_agent.idle');
  }
  if (activePresetId && WORKFLOW_SCENARIOS[activePresetId]) {
    renderWorkflowMessages(WORKFLOW_SCENARIOS[activePresetId]);
  }
  setStatus(currentStatus);
}

window.i18n.ready.then(() => {
  refreshLocaleDependentUi();
});

window.i18n.onChange(() => {
  refreshLocaleDependentUi();
  if (ws && ws.readyState === WebSocket.OPEN) {
    sendWs({ type: 'demo_inject', payload: { locale: window.i18n.locale } });
  }
});

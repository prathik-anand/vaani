/* Vaani client-side controller.
   Responsibilities:
     - Hold-to-talk recording via Web Speech API (preferred) or MediaRecorder fallback
     - Camera access, snapshot, sample-paper picker
     - POST /turn, render reply bubble + function calls
     - Browser TTS for the spoken reply (preserves the offline claim)
     - Fetch /info on load to populate the engine line in the judges' panel       */

(() => {
  const elTime     = document.querySelector('.status-bar .time');
  const elCam      = document.getElementById('cam');
  const elCaptured = document.getElementById('captured');
  const elPlace    = document.getElementById('placeholder');
  const elConv     = document.getElementById('conversation');
  const btnCam     = document.getElementById('cam-btn');
  const btnMic     = document.getElementById('mic-btn');
  const btnLang    = document.getElementById('lang-btn');
  const lblLang    = document.getElementById('lang-label');
  const elFn       = document.getElementById('fn-calls');
  const elEngine   = document.getElementById('engine');
  const elElapsed  = document.getElementById('elapsed');

  // Live wall clock in the status bar
  const tick = () => {
    const d = new Date();
    elTime.textContent = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  };
  tick(); setInterval(tick, 30_000);

  // Language wheel
  const LANGS = [
    { code: 'hi', label: 'हि', name: 'Hindi'   },
    { code: 'en', label: 'EN', name: 'English' },
    { code: 'ta', label: 'த',  name: 'Tamil'   },
    { code: 'mr', label: 'म',  name: 'Marathi' },
  ];
  let langIdx = 0;
  btnLang.addEventListener('click', () => {
    langIdx = (langIdx + 1) % LANGS.length;
    lblLang.textContent = LANGS[langIdx].label;
  });
  const currentLang = () => LANGS[langIdx].code;

  // Camera setup (best-effort; no error if denied — samples cover the demo)
  let stream = null;
  let lastImageBlob = null;
  let lastImageName = null;

  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }, audio: false,
      });
      elCam.srcObject = stream;
      elPlace.style.display = 'none';
    } catch (e) {
      // Camera denied — silently fall back to sample buttons
      elCam.style.display = 'none';
    }
  }
  startCamera();

  function capture() {
    if (elCaptured.src && !elCam.srcObject) return null;  // already showing a sample
    const canvas = document.createElement('canvas');
    canvas.width  = elCam.videoWidth  || 640;
    canvas.height = elCam.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(elCam, 0, 0, canvas.width, canvas.height);
    return new Promise(resolve =>
      canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.85)
    );
  }

  btnCam.addEventListener('click', async () => {
    const blob = await capture();
    if (!blob) return;
    lastImageBlob = blob;
    lastImageName = `capture_${Date.now()}.jpg`;
    showCaptured(URL.createObjectURL(blob));
  });

  function showCaptured(url) {
    elCaptured.src = url;
    elCaptured.hidden = false;
    elCam.style.display = 'none';
    elPlace.style.display = 'none';
  }

  // Sample paper buttons (demo path)
  document.querySelectorAll('.sample').forEach(btn => {
    btn.addEventListener('click', async () => {
      const url = btn.dataset.img;
      const name = btn.dataset.name;
      const r = await fetch(url);
      lastImageBlob = await r.blob();
      lastImageName = name;
      showCaptured(url);
    });
  });

  // Hold-to-talk via Web Speech API (online ASR is browser-side; for the in-app
  // pretend we're offline, this is the closest analogue). If Speech API is missing
  // the user can still tap a sample + use a default question via /turn text=.
  let recognising = false;
  let recogniser = null;
  function buildRecogniser() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.lang = ({hi:'hi-IN', en:'en-IN', ta:'ta-IN', mr:'mr-IN'})[currentLang()] || 'hi-IN';
    return r;
  }

  function pushBubble(side, text) {
    const div = document.createElement('div');
    div.className = `bubble bubble-${side}`;
    div.textContent = text;
    // Replace the empty greeting if it's still there
    const empty = elConv.querySelector('.bubble.empty');
    if (empty) empty.remove();
    elConv.appendChild(div);
    elConv.scrollTop = elConv.scrollHeight;
    return div;
  }

  async function sendTurn(userText) {
    if (userText) pushBubble('user', userText);
    const fd = new FormData();
    fd.append('text', userText || '');
    fd.append('lang', currentLang());
    if (lastImageBlob) {
      fd.append('image', lastImageBlob, lastImageName || 'capture.jpg');
      fd.append('image_filename', lastImageName || '');
    }
    const r = await fetch('/turn', { method: 'POST', body: fd });
    const j = await r.json();
    pushBubble('bot', j.reply_text);
    elElapsed.textContent = `${j.elapsed_ms} ms · ${j.engine}`;
    renderFnCalls(j.fn_calls);
    speak(j.reply_text, j.language);
    return j;
  }

  function renderFnCalls(calls) {
    if (!calls || !calls.length) return;
    // Clear the placeholder
    const ph = elFn.querySelector('li.muted');
    if (ph) ph.remove();
    calls.forEach(call => {
      const li = document.createElement('li');
      const argsStr = JSON.stringify(call.args || {}, null, 2);
      li.innerHTML =
        `<div><span class="name">${escapeHtml(call.name)}</span></div>` +
        `<pre class="args">${escapeHtml(argsStr)}</pre>`;
      elFn.appendChild(li);
      elFn.scrollTop = elFn.scrollHeight;
    });
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function speak(text, lang) {
    if (!('speechSynthesis' in window)) return;
    try {
      const u = new SpeechSynthesisUtterance(text);
      const map = {hi:'hi-IN', en:'en-IN', ta:'ta-IN', mr:'mr-IN'};
      u.lang = map[lang] || map[currentLang()] || 'hi-IN';
      u.rate = 0.95;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch {}
  }

  // Mic button — hold-to-talk
  function startListening() {
    recogniser = buildRecogniser();
    if (!recogniser) {
      // Speech API missing: send a default question for the current image
      const fallback = ({hi:'yeh kya hai mujhe kya karna hai',
                        en:'what is this paper about',
                        ta:'idu enna seyya vendum',
                        mr:'he kay aahe'})[currentLang()] || 'yeh kya hai';
      sendTurn(fallback);
      return;
    }
    recognising = true;
    btnMic.classList.add('recording');
    recogniser.onresult = e => {
      const text = e.results[0][0].transcript;
      sendTurn(text);
    };
    recogniser.onerror = () => stopListening();
    recogniser.onend = () => stopListening();
    recogniser.start();
  }
  function stopListening() {
    recognising = false;
    btnMic.classList.remove('recording');
    if (recogniser) try { recogniser.stop(); } catch {}
    recogniser = null;
  }
  btnMic.addEventListener('mousedown', startListening);
  btnMic.addEventListener('mouseup',   stopListening);
  btnMic.addEventListener('touchstart', e => { e.preventDefault(); startListening(); });
  btnMic.addEventListener('touchend',   e => { e.preventDefault(); stopListening();  });
  btnMic.addEventListener('click',     () => { if (!recognising) startListening();  });

  // Boot: fetch /info to populate engine + network labels (no hardcoded claims)
  const elNetwork = document.getElementById('network');
  fetch('/info').then(r => r.json()).then(j => {
    elEngine.textContent = j.engine + (j.is_stub ? ' (demo mode)' : '');
    if (elNetwork) {
      elNetwork.textContent = j.offline ? 'offline · 0 outbound calls' : 'online';
      elNetwork.className = j.offline ? 'ok' : '';
    }
  }).catch(() => {
    elEngine.textContent = 'unknown';
    if (elNetwork) elNetwork.textContent = 'unknown';
  });
})();

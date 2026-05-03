/* Vaani — onboarding-first, upload-first web app.
 *
 * Flow:
 *   1. First visit: ask the user their language. Save in localStorage.
 *   2. Returning: skip onboarding. Show topbar with their language; let them change.
 *   3. Main: Upload OR Camera (primary). "Try a sample" reveals demo papers.
 *   4. After paper: auto-fill question in their lang, Ask.
 *   5. Reply: spoken aloud automatically + replay button. Tool call collapsed below.
 */
(() => {

  // ── Languages catalogue ───────────────────────────────────────
  // BCP-47 locale chosen for SpeechSynthesis voice availability.
  // 20 quick-pick (Indian + global majors) + 60+ in the searchable long tail.
  const QUICK_LANGS = [
    { code: 'hi', locale: 'hi-IN', native: 'हिन्दी',   english: 'Hindi'    },
    { code: 'en', locale: 'en-IN', native: 'English',  english: 'English'  },
    { code: 'ta', locale: 'ta-IN', native: 'தமிழ்',    english: 'Tamil'    },
    { code: 'mr', locale: 'mr-IN', native: 'मराठी',    english: 'Marathi'  },
    { code: 'bn', locale: 'bn-IN', native: 'বাংলা',     english: 'Bengali'  },
    { code: 'te', locale: 'te-IN', native: 'తెలుగు',    english: 'Telugu'   },
    { code: 'gu', locale: 'gu-IN', native: 'ગુજરાતી',  english: 'Gujarati' },
    { code: 'kn', locale: 'kn-IN', native: 'ಕನ್ನಡ',    english: 'Kannada'  },
    { code: 'ml', locale: 'ml-IN', native: 'മലയാളം',   english: 'Malayalam'},
    { code: 'pa', locale: 'pa-IN', native: 'ਪੰਜਾਬੀ',   english: 'Punjabi'  },
    { code: 'ur', locale: 'ur-IN', native: 'اردو',     english: 'Urdu'     },
    { code: 'ar', locale: 'ar-SA', native: 'العربية', english: 'Arabic'   },
    { code: 'es', locale: 'es-ES', native: 'Español',  english: 'Spanish'  },
    { code: 'fr', locale: 'fr-FR', native: 'Français', english: 'French'   },
    { code: 'pt', locale: 'pt-BR', native: 'Português',english: 'Portuguese'},
    { code: 'ru', locale: 'ru-RU', native: 'Русский',  english: 'Russian'  },
    { code: 'de', locale: 'de-DE', native: 'Deutsch',  english: 'German'   },
    { code: 'zh', locale: 'zh-CN', native: '中文',      english: 'Chinese'  },
    { code: 'ja', locale: 'ja-JP', native: '日本語',    english: 'Japanese' },
    { code: 'sw', locale: 'sw-KE', native: 'Kiswahili',english: 'Swahili'  },
  ];
  // Long-tail. Subset of Gemma 4's claimed 140 — we list the speakable majors.
  const MORE_LANGS = [
    ['ko','ko-KR','한국어','Korean'], ['vi','vi-VN','Tiếng Việt','Vietnamese'],
    ['th','th-TH','ไทย','Thai'], ['id','id-ID','Bahasa Indonesia','Indonesian'],
    ['ms','ms-MY','Bahasa Melayu','Malay'], ['fil','fil-PH','Filipino','Filipino'],
    ['tr','tr-TR','Türkçe','Turkish'], ['fa','fa-IR','فارسی','Persian'],
    ['he','he-IL','עברית','Hebrew'], ['it','it-IT','Italiano','Italian'],
    ['nl','nl-NL','Nederlands','Dutch'], ['pl','pl-PL','Polski','Polish'],
    ['cs','cs-CZ','Čeština','Czech'], ['sk','sk-SK','Slovenčina','Slovak'],
    ['hu','hu-HU','Magyar','Hungarian'], ['ro','ro-RO','Română','Romanian'],
    ['uk','uk-UA','Українська','Ukrainian'], ['el','el-GR','Ελληνικά','Greek'],
    ['sv','sv-SE','Svenska','Swedish'], ['no','nb-NO','Norsk','Norwegian'],
    ['da','da-DK','Dansk','Danish'], ['fi','fi-FI','Suomi','Finnish'],
    ['or','or-IN','ଓଡ଼ିଆ','Odia'], ['as','as-IN','অসমীয়া','Assamese'],
    ['ne','ne-NP','नेपाली','Nepali'], ['si','si-LK','සිංහල','Sinhala'],
    ['my','my-MM','မြန်မာ','Burmese'], ['km','km-KH','ខ្មែរ','Khmer'],
    ['lo','lo-LA','ລາວ','Lao'], ['am','am-ET','አማርኛ','Amharic'],
    ['ha','ha-NG','Hausa','Hausa'], ['yo','yo-NG','Yorùbá','Yoruba'],
    ['ig','ig-NG','Igbo','Igbo'], ['zu','zu-ZA','isiZulu','Zulu'],
    ['xh','xh-ZA','isiXhosa','Xhosa'], ['af','af-ZA','Afrikaans','Afrikaans'],
    ['so','so-SO','Soomaali','Somali'], ['rw','rw-RW','Kinyarwanda','Kinyarwanda'],
    ['mg','mg-MG','Malagasy','Malagasy'], ['ca','ca-ES','Català','Catalan'],
    ['eu','eu-ES','Euskara','Basque'], ['gl','gl-ES','Galego','Galician'],
    ['hr','hr-HR','Hrvatski','Croatian'], ['sr','sr-RS','Српски','Serbian'],
    ['sl','sl-SI','Slovenščina','Slovenian'], ['bg','bg-BG','Български','Bulgarian'],
    ['mk','mk-MK','Македонски','Macedonian'], ['sq','sq-AL','Shqip','Albanian'],
    ['lt','lt-LT','Lietuvių','Lithuanian'], ['lv','lv-LV','Latviešu','Latvian'],
    ['et','et-EE','Eesti','Estonian'], ['is','is-IS','Íslenska','Icelandic'],
    ['ga','ga-IE','Gaeilge','Irish'], ['cy','cy-GB','Cymraeg','Welsh'],
    ['mt','mt-MT','Malti','Maltese'], ['hy','hy-AM','Հայերեն','Armenian'],
    ['ka','ka-GE','ქართული','Georgian'], ['az','az-AZ','Azərbaycan','Azerbaijani'],
    ['kk','kk-KZ','Қазақ','Kazakh'], ['uz','uz-UZ','Oʻzbek','Uzbek'],
    ['mn','mn-MN','Монгол','Mongolian'],
  ].map(a => ({ code: a[0], locale: a[1], native: a[2], english: a[3] }));

  const ALL_LANGS = [...QUICK_LANGS, ...MORE_LANGS];

  // Per-lang default question templates (prefilled in the ask box).
  const DEFAULT_Q = {
    hi:'yeh kya hai mujhe kya karna hai',  ta:'idhu enna seyya vendum',
    mr:'he kay aahe',                      bn:'eta ki, ki korbo',
    te:'idi enti, nenu emi cheyali',       gu:'aa shu chhe, mara mate shu karvu',
    kn:'idu yenu, naanu enu maadabeku',    ml:'idu enthaan, njaan enth cheyyanam',
    pa:'eh ki hai, mainu ki karna chahida hai',
    ur:'yeh kya hai mujhe kya karna chahiye',
    en:'what is this paper, what should I do',
    ar:'ما هذا، ماذا أفعل',
    es:'¿qué es esto y qué debo hacer?',   fr:'qu\'est-ce que c\'est et que dois-je faire ?',
    pt:'o que é isso e o que devo fazer?', ru:'что это и что мне делать?',
    de:'was ist das und was soll ich tun?',zh:'这是什么，我该怎么办？',
    ja:'これは何ですか、どうすればいいですか？',
    sw:'hii ni nini, nifanye nini?',
  };
  const fallbackQuestion = (code) => DEFAULT_Q[code] || DEFAULT_Q.en;

  // ── State ─────────────────────────────────────────────────────
  const LS_KEY = 'vaani.lang';
  let user = readUser();   // {code, locale, native, english} or null

  // ── Onboarding ────────────────────────────────────────────────
  const onb = document.getElementById('onboarding');
  const appRoot = document.getElementById('app-root');
  const langGrid = document.getElementById('lang-grid');
  const langList = document.getElementById('lang-list');
  const langSearch = document.getElementById('lang-search');

  function readUser() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || 'null'); }
    catch { return null; }
  }
  function saveUser(lang) {
    user = lang;
    localStorage.setItem(LS_KEY, JSON.stringify(lang));
    renderLangChip();
  }

  function renderOnboarding() {
    langGrid.innerHTML = '';
    QUICK_LANGS.forEach(l => {
      const b = document.createElement('button');
      b.className = 'lang-pick';
      b.innerHTML = `<span class="native">${escape(l.native)}</span>` +
                    `<span class="english">${escape(l.english)}</span>`;
      b.addEventListener('click', () => pickLang(l));
      langGrid.appendChild(b);
    });
    langList.innerHTML = '';
    ALL_LANGS.forEach(l => {
      const b = document.createElement('button');
      b.className = 'lang-list-item';
      b.dataset.search = (l.native + ' ' + l.english).toLowerCase();
      b.innerHTML = `<span class="native">${escape(l.native)}</span>` +
                    `<span class="english">${escape(l.english)}</span>`;
      b.addEventListener('click', () => pickLang(l));
      langList.appendChild(b);
    });
    langSearch.addEventListener('input', e => {
      const q = e.target.value.trim().toLowerCase();
      Array.from(langList.children).forEach(c => {
        c.hidden = q && c.dataset.search.indexOf(q) === -1;
      });
    });
  }

  function pickLang(lang) {
    saveUser(lang);
    showApp();
  }

  function showOnboarding() {
    onb.hidden = false;
    appRoot.hidden = true;
    renderOnboarding();
  }
  function showApp() {
    onb.hidden = true;
    appRoot.hidden = false;
    renderLangChip();
    renderSamples();
    bootEngineLabel();
  }

  // ── Topbar lang chip ──────────────────────────────────────────
  const langChipBtn = document.getElementById('lang-chip');
  const langChipLabel = document.getElementById('lang-chip-label');

  function renderLangChip() {
    if (!user) return;
    langChipLabel.textContent = `${user.native} · ${user.english}`;
  }
  langChipBtn.addEventListener('click', () => {
    showOnboarding();
  });

  // ── Bring-a-paper: upload, camera, drag-drop, samples ────────
  const dz = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const cameraInput = document.getElementById('camera-input');
  const uploadBtn = document.getElementById('upload-btn');
  const cameraBtn = document.getElementById('camera-btn');
  const trySample = document.getElementById('try-sample');
  const paperGrid = document.getElementById('paper-grid');

  uploadBtn.addEventListener('click', () => fileInput.click());
  cameraBtn.addEventListener('click', () => cameraInput.click());
  fileInput.addEventListener('change', e => {
    if (e.target.files[0]) onPaperSelected(e.target.files[0], 'upload');
  });
  cameraInput.addEventListener('change', e => {
    if (e.target.files[0]) onPaperSelected(e.target.files[0], 'capture');
  });

  // Drag and drop
  ['dragenter','dragover'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('drag'); }));
  ['dragleave','drop'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('drag'); }));
  dz.addEventListener('drop', e => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) onPaperSelected(f, 'drop');
  });

  trySample.addEventListener('click', e => {
    e.preventDefault();
    paperGrid.hidden = !paperGrid.hidden;
    if (!paperGrid.hidden) paperGrid.scrollIntoView({behavior:'smooth', block:'nearest'});
  });

  function renderSamples() {
    const samples = [
      { url:'/samples/prescription_hindi.jpg',     name:'prescription_hindi.jpg',
        tag:'Hindi · Rx',           urgent:false },
      { url:'/samples/ration_receipt_tamil.jpg',   name:'ration_receipt_tamil.jpg',
        tag:'Tamil · Receipt',      urgent:false },
      { url:'/samples/marathi_letter.jpg',         name:'marathi_letter.jpg',
        tag:'Marathi · Letter',     urgent:false },
      { url:'/samples/school_notice_english.jpg',  name:'school_notice_english.jpg',
        tag:'English · Notice',     urgent:false },
      { url:'/samples/fever_paper.jpg',            name:'fever_paper.jpg',
        tag:'Urgent · Fever',       urgent:true  },
    ];
    paperGrid.innerHTML = '';
    samples.forEach(s => {
      const c = document.createElement('button');
      c.className = 'card';
      c.innerHTML = `<img src="${s.url}" alt=""><span class="card-tag${s.urgent?' urgent':''}">${escape(s.tag)}</span>`;
      c.addEventListener('click', () => {
        fetch(s.url).then(r => r.blob()).then(blob => {
          const file = new File([blob], s.name, { type: 'image/jpeg' });
          onPaperSelected(file, 'sample');
        });
      });
      paperGrid.appendChild(c);
    });
  }

  // ── Selected paper → ask ──────────────────────────────────────
  let currentBlob = null;
  let currentName = null;
  const askSection = document.getElementById('ask-section');
  const paperPreview = document.getElementById('paper-preview');
  const questionEl = document.getElementById('question');
  const askBtn = document.getElementById('ask-btn');
  const hintEl = document.getElementById('hint');

  function onPaperSelected(file, source) {
    currentBlob = file;
    currentName = file.name || 'paper.jpg';
    const url = URL.createObjectURL(file);
    paperPreview.src = url;
    askSection.hidden = false;
    questionEl.value = fallbackQuestion(user.code);
    questionEl.placeholder = `Ask in ${user.native}…`;
    hintEl.textContent = `Vaani will read the paper and reply in ${user.english} (${user.native}). Audio plays automatically.`;
    askSection.scrollIntoView({behavior:'smooth', block:'start'});
  }

  askBtn.addEventListener('click', sendTurn);
  questionEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !askBtn.disabled) sendTurn();
  });

  // ── /turn ─────────────────────────────────────────────────────
  const replySection = document.getElementById('reply');
  const conv = document.getElementById('conversation');
  const toolWrap = document.getElementById('tool-call-wrap');
  const toolPre = document.getElementById('tool-call');

  async function sendTurn() {
    if (!currentBlob) return;
    const q = questionEl.value.trim() || fallbackQuestion(user.code);
    pushBubble('user', q);
    replySection.hidden = false;
    setLoading(true);

    const fd = new FormData();
    fd.append('text', q);
    fd.append('lang', user.code);
    fd.append('image_filename', currentName);
    fd.append('image', currentBlob, currentName);

    let response;
    try {
      const r = await fetch('/turn', { method:'POST', body:fd });
      if (!r.ok) {
        const txt = await r.text();
        pushBubble('bot', `(Error ${r.status}: ${txt.slice(0,200)})`);
        setLoading(false);
        return;
      }
      response = await r.json();
    } catch (e) {
      pushBubble('bot', `(Network error: ${e.message})`);
      setLoading(false);
      return;
    }

    const replyLang = response.language || user.code;
    pushBubble('bot', response.reply_text || '(empty reply)', replyLang);
    speak(response.reply_text, replyLang);
    renderToolCall(response.fn_calls);
    setLoading(false);
  }

  function pushBubble(side, text, replyLang) {
    const div = document.createElement('div');
    div.className = `bubble bubble-${side}`;
    div.textContent = text;
    if (side === 'bot' && text) {
      const btn = document.createElement('button');
      btn.className = 'replay';
      btn.title = 'Replay audio';
      btn.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">' +
        '<path d="M8 5v14l11-7L8 5z" fill="currentColor"/></svg>';
      btn.addEventListener('click', () => { speak(text, replyLang || user.code); });
      div.appendChild(btn);
    }
    conv.appendChild(div);
    div.scrollIntoView({behavior:'smooth', block:'end'});
  }

  function renderToolCall(calls) {
    if (!calls || !calls.length) {
      toolWrap.hidden = true;
      toolPre.textContent = '';
      return;
    }
    toolWrap.hidden = false;
    toolPre.textContent = JSON.stringify(calls, null, 2);
  }

  function setLoading(loading) {
    askBtn.classList.toggle('loading', loading);
    askBtn.textContent = loading ? '…' : 'Ask';
    askBtn.disabled = loading;
  }

  // ── TTS — the audio output is the feature ────────────────────
  function pickVoice(locale) {
    const voices = window.speechSynthesis.getVoices();
    if (!voices || !voices.length) return null;
    // 1. exact locale match (hi-IN)
    let v = voices.find(x => x.lang === locale);
    if (v) return v;
    // 2. prefix match (hi-*)
    const lang = locale.split('-')[0];
    v = voices.find(x => x.lang.startsWith(lang + '-'));
    if (v) return v;
    // 3. base lang match (hi)
    v = voices.find(x => x.lang === lang);
    return v || null;
  }

  function speak(text, langCode) {
    if (!text || !('speechSynthesis' in window)) return;
    try {
      const lang = ALL_LANGS.find(l => l.code === langCode) || user;
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang.locale;
      u.rate = 0.95;
      const v = pickVoice(lang.locale);
      if (v) u.voice = v;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch {}
  }

  // Make sure voices are loaded (Chrome loads them async)
  if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {};
  }

  // ── Boot ──────────────────────────────────────────────────────
  function bootEngineLabel() {
    fetch('/info').then(r => r.json()).then(j => {
      document.getElementById('engine').textContent = j.engine || 'unknown';
    }).catch(() => { document.getElementById('engine').textContent = 'unknown'; });
  }

  function escape(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // Decide first view
  if (user) showApp();
  else showOnboarding();
})();

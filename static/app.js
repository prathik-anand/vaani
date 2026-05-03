/* Vaani — voice-first web app controller.
 *
 * Flow:
 *   1. First visit → onboarding (language picker, localStorage cached).
 *   2. Returning   → main app, chrome localized to user's language.
 *   3. Bring paper → upload / camera / drag-drop / "try a sample" link.
 *   4. Ask         → primary: hold-to-talk mic (Web Speech API).
 *                    secondary: type fallback inside <details>.
 *   5. Reply       → audio plays automatically. Big play/replay button.
 *                    Transcript collapsed by default. Friendly action card
 *                    summarises the tool call in the user's language.
 *
 * Debug mode (`?debug=1`) reveals the raw tool-call JSON panel.
 */
(() => {

  // ── Language catalogue ───────────────────────────────────────
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

  // ── String tables — chrome translates per user's language ───
  const STRINGS = {
    en: {
      onb_question: 'Which language do you speak?',
      onb_sub: "I'll explain papers to you in this language. You can change it any time.",
      onb_more: 'More languages',
      onb_search: 'Search 140+ languages…',
      change_language: 'Change language',
      hero_intro: "Bring any paper. I'll read it to you in your language.",
      step_show: 'Show me a paper',
      step_ask: 'Ask',
      step_reply: 'Reply',
      btn_upload: 'Upload',
      btn_camera: 'Camera',
      btn_ask: 'Ask',
      dz_hint: 'Or drop an image here',
      try_sample: 'Try a sample paper →',
      samples_label: 'Or try one of these',
      mic_idle: 'Hold to speak',
      mic_idle_sub: 'or type your question below',
      mic_listening: 'Listening…',
      mic_listening_sub: 'Release when you finish',
      type_instead: 'Type instead',
      ask_placeholder: 'Ask in your language…',
      audio_thinking: 'Reading the paper…',
      audio_speaking: 'Speaking',
      audio_done: 'Tap play to hear it again',
      show_transcript: 'Show what was said',
      ask_again: 'Show another paper',
      footer_built: 'Built on Gemma 4',
      action_reminder_title: 'Reminder set',
      action_reminder_desc: '{med} · {times} · {days} day(s)',
      action_red_flag_title: 'Go to the clinic today',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'Questions ready for the clinic',
      action_questions_desc: 'About: {topic}',
      action_draft_title: 'Reply drafted',
      action_draft_desc: '{intent}',
      action_lookup_title: 'Medicine explained',
      action_lookup_desc: '{name}',
    },
    hi: {
      onb_question: 'आप कौन सी भाषा बोलते हैं?',
      onb_sub: 'मैं आपको कागज़ इसी भाषा में समझाऊँगी। आप कभी भी बदल सकते हैं।',
      onb_more: 'और भाषाएँ',
      onb_search: '140+ भाषाओं में खोजें…',
      change_language: 'भाषा बदलें',
      hero_intro: 'कोई भी कागज़ लाइए। मैं आपकी भाषा में पढ़कर सुनाऊँगी।',
      step_show: 'मुझे कागज़ दिखाइए',
      step_ask: 'पूछिए',
      step_reply: 'जवाब',
      btn_upload: 'अपलोड',
      btn_camera: 'कैमरा',
      btn_ask: 'पूछें',
      dz_hint: 'या यहाँ कोई तस्वीर डालिए',
      try_sample: 'एक नमूना देखें →',
      samples_label: 'या इनमें से कोई आज़माएँ',
      mic_idle: 'बोलने के लिए दबाए रखें',
      mic_idle_sub: 'या नीचे अपना सवाल लिखिए',
      mic_listening: 'सुन रही हूँ…',
      mic_listening_sub: 'बोलने के बाद छोड़ दीजिए',
      type_instead: 'टाइप करें',
      ask_placeholder: 'अपनी भाषा में पूछिए…',
      audio_thinking: 'कागज़ पढ़ रही हूँ…',
      audio_speaking: 'बोल रही हूँ',
      audio_done: 'फिर से सुनने के लिए दबाएँ',
      show_transcript: 'क्या कहा गया',
      ask_again: 'दूसरा कागज़ दिखाएँ',
      footer_built: 'Gemma 4 पर बनी है',
      action_reminder_title: 'याद दिलाने वाला अलार्म लग गया',
      action_reminder_desc: '{med} · {times} · {days} दिन',
      action_red_flag_title: 'आज ही अस्पताल जाइए',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'क्लिनिक के लिए सवाल तैयार हैं',
      action_questions_desc: 'विषय: {topic}',
      action_draft_title: 'जवाब तैयार है',
      action_draft_desc: '{intent}',
      action_lookup_title: 'दवा की जानकारी',
      action_lookup_desc: '{name}',
    },
    ta: {
      onb_question: 'நீங்கள் எந்த மொழி பேசுகிறீர்கள்?',
      onb_sub: 'நான் இந்த மொழியில் காகிதங்களை விளக்குவேன். எப்போது வேண்டுமானாலும் மாற்றலாம்.',
      onb_more: 'மேலும் மொழிகள்',
      onb_search: '140+ மொழிகளில் தேடுங்கள்…',
      change_language: 'மொழியை மாற்று',
      hero_intro: 'எந்த காகிதமும் கொண்டு வாருங்கள். உங்கள் மொழியில் வாசித்துக் காட்டுகிறேன்.',
      step_show: 'காகிதத்தை காட்டுங்கள்',
      step_ask: 'கேளுங்கள்',
      step_reply: 'பதில்',
      btn_upload: 'பதிவேற்று',
      btn_camera: 'கேமரா',
      btn_ask: 'கேள்',
      dz_hint: 'அல்லது படத்தை இங்கே போடுங்கள்',
      try_sample: 'மாதிரியை பாருங்கள் →',
      samples_label: 'அல்லது இவற்றில் ஒன்றை முயற்சி செய்யுங்கள்',
      mic_idle: 'பேச அழுத்திப் பிடியுங்கள்',
      mic_idle_sub: 'அல்லது கீழே தட்டச்சு செய்யுங்கள்',
      mic_listening: 'கேட்கிறேன்…',
      mic_listening_sub: 'முடிந்ததும் விடுங்கள்',
      type_instead: 'தட்டச்சு செய்யுங்கள்',
      ask_placeholder: 'உங்கள் மொழியில் கேளுங்கள்…',
      audio_thinking: 'காகிதத்தை படிக்கிறேன்…',
      audio_speaking: 'பேசுகிறேன்',
      audio_done: 'மீண்டும் கேட்க தட்டுங்கள்',
      show_transcript: 'என்ன சொன்னேன்',
      ask_again: 'வேறு காகிதம் காட்டுங்கள்',
      footer_built: 'Gemma 4 இல் கட்டப்பட்டது',
      action_reminder_title: 'நினைவூட்டல் அமைக்கப்பட்டது',
      action_reminder_desc: '{med} · {times} · {days} நாட்கள்',
      action_red_flag_title: 'இன்றே மருத்துவமனைக்கு செல்லுங்கள்',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'மருத்துவமனைக்கான கேள்விகள் தயார்',
      action_questions_desc: 'பற்றி: {topic}',
      action_draft_title: 'பதில் தயாரிக்கப்பட்டது',
      action_draft_desc: '{intent}',
      action_lookup_title: 'மருந்து விளக்கம்',
      action_lookup_desc: '{name}',
    },
    mr: {
      onb_question: 'तुम्ही कोणती भाषा बोलता?',
      onb_sub: 'मी तुम्हाला कागद याच भाषेत समजावून सांगेन. कधीही बदलता येईल.',
      onb_more: 'आणखी भाषा',
      onb_search: '140+ भाषांमध्ये शोधा…',
      change_language: 'भाषा बदला',
      hero_intro: 'कोणताही कागद आणा. मी तुमच्या भाषेत वाचून सांगेन.',
      step_show: 'मला कागद दाखवा',
      step_ask: 'विचारा',
      step_reply: 'उत्तर',
      btn_upload: 'अपलोड',
      btn_camera: 'कॅमेरा',
      btn_ask: 'विचारा',
      dz_hint: 'किंवा इथे चित्र टाका',
      try_sample: 'नमुना पहा →',
      samples_label: 'किंवा यापैकी एक वापरा',
      mic_idle: 'बोलण्यासाठी दाबून ठेवा',
      mic_idle_sub: 'किंवा खाली टाइप करा',
      mic_listening: 'ऐकत आहे…',
      mic_listening_sub: 'बोलून झाल्यावर सोडा',
      type_instead: 'टाइप करा',
      ask_placeholder: 'तुमच्या भाषेत विचारा…',
      audio_thinking: 'कागद वाचत आहे…',
      audio_speaking: 'बोलत आहे',
      audio_done: 'पुन्हा ऐकण्यासाठी दाबा',
      show_transcript: 'काय म्हटलं',
      ask_again: 'दुसरा कागद दाखवा',
      footer_built: 'Gemma 4 वर बनवलेली',
      action_reminder_title: 'आठवण लावली',
      action_reminder_desc: '{med} · {times} · {days} दिवस',
      action_red_flag_title: 'आजच दवाखान्यात जा',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'दवाखान्यासाठी प्रश्न तयार',
      action_questions_desc: 'विषय: {topic}',
      action_draft_title: 'उत्तर तयार',
      action_draft_desc: '{intent}',
      action_lookup_title: 'औषधाची माहिती',
      action_lookup_desc: '{name}',
    },
    bn: {
      onb_question: 'আপনি কোন ভাষায় কথা বলেন?',
      onb_sub: 'আমি এই ভাষায় কাগজগুলি ব্যাখ্যা করব। যেকোনো সময় পরিবর্তন করতে পারেন।',
      onb_more: 'আরও ভাষা',
      onb_search: '১৪০+ ভাষায় খুঁজুন…',
      change_language: 'ভাষা পরিবর্তন',
      hero_intro: 'যেকোনো কাগজ আনুন। আমি আপনার ভাষায় পড়ে শোনাব।',
      step_show: 'কাগজ দেখান',
      step_ask: 'জিজ্ঞাসা',
      step_reply: 'উত্তর',
      btn_upload: 'আপলোড',
      btn_camera: 'ক্যামেরা',
      btn_ask: 'জিজ্ঞাসা',
      dz_hint: 'বা এখানে ছবি ফেলুন',
      try_sample: 'নমুনা দেখুন →',
      samples_label: 'অথবা এর মধ্যে একটি চেষ্টা করুন',
      mic_idle: 'কথা বলতে চাপ দিয়ে রাখুন',
      mic_idle_sub: 'বা নীচে টাইপ করুন',
      mic_listening: 'শুনছি…',
      mic_listening_sub: 'শেষ হলে ছেড়ে দিন',
      type_instead: 'টাইপ করুন',
      ask_placeholder: 'আপনার ভাষায় জিজ্ঞাসা করুন…',
      audio_thinking: 'কাগজ পড়ছি…',
      audio_speaking: 'বলছি',
      audio_done: 'আবার শুনতে চাপুন',
      show_transcript: 'কী বলেছিল',
      ask_again: 'আরেকটি কাগজ দেখান',
      footer_built: 'Gemma 4 দিয়ে তৈরি',
      action_reminder_title: 'মনে করিয়ে দেওয়া অ্যালার্ম সেট',
      action_reminder_desc: '{med} · {times} · {days} দিন',
      action_red_flag_title: 'আজই হাসপাতালে যান',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'ক্লিনিকের প্রশ্ন প্রস্তুত',
      action_questions_desc: 'বিষয়: {topic}',
      action_draft_title: 'উত্তর প্রস্তুত',
      action_draft_desc: '{intent}',
      action_lookup_title: 'ওষুধের ব্যাখ্যা',
      action_lookup_desc: '{name}',
    },
    es: {
      onb_question: '¿Qué idioma hablas?',
      onb_sub: 'Te explicaré los papeles en este idioma. Puedes cambiarlo en cualquier momento.',
      onb_more: 'Más idiomas',
      onb_search: 'Buscar entre 140+ idiomas…',
      change_language: 'Cambiar idioma',
      hero_intro: 'Trae cualquier papel. Te lo leeré en tu idioma.',
      step_show: 'Muéstrame un papel',
      step_ask: 'Pregunta',
      step_reply: 'Respuesta',
      btn_upload: 'Subir',
      btn_camera: 'Cámara',
      btn_ask: 'Preguntar',
      dz_hint: 'O suelta una imagen aquí',
      try_sample: 'Probar un papel de ejemplo →',
      samples_label: 'O prueba uno de estos',
      mic_idle: 'Mantén presionado para hablar',
      mic_idle_sub: 'o escribe tu pregunta abajo',
      mic_listening: 'Escuchando…',
      mic_listening_sub: 'Suelta cuando termines',
      type_instead: 'Escribir en vez',
      ask_placeholder: 'Pregunta en tu idioma…',
      audio_thinking: 'Leyendo el papel…',
      audio_speaking: 'Hablando',
      audio_done: 'Toca para escucharlo otra vez',
      show_transcript: 'Mostrar lo dicho',
      ask_again: 'Mostrar otro papel',
      footer_built: 'Construido sobre Gemma 4',
      action_reminder_title: 'Recordatorio configurado',
      action_reminder_desc: '{med} · {times} · {days} día(s)',
      action_red_flag_title: 'Ve a la clínica hoy',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'Preguntas listas para la clínica',
      action_questions_desc: 'Sobre: {topic}',
      action_draft_title: 'Respuesta redactada',
      action_draft_desc: '{intent}',
      action_lookup_title: 'Medicamento explicado',
      action_lookup_desc: '{name}',
    },
    ar: {
      onb_question: 'ما هي اللغة التي تتحدث بها؟',
      onb_sub: 'سأشرح لك الأوراق بهذه اللغة. يمكنك تغييرها في أي وقت.',
      onb_more: 'لغات أخرى',
      onb_search: 'ابحث في 140+ لغة…',
      change_language: 'تغيير اللغة',
      hero_intro: 'أحضر أي ورقة. سأقرأها لك بلغتك.',
      step_show: 'أرني ورقة',
      step_ask: 'اسأل',
      step_reply: 'الرد',
      btn_upload: 'رفع',
      btn_camera: 'كاميرا',
      btn_ask: 'اسأل',
      dz_hint: 'أو أسقط صورة هنا',
      try_sample: 'جرب ورقة نموذجية ←',
      samples_label: 'أو جرب واحدة من هذه',
      mic_idle: 'استمر بالضغط للتحدث',
      mic_idle_sub: 'أو اكتب سؤالك أدناه',
      mic_listening: 'أستمع…',
      mic_listening_sub: 'حرر عندما تنتهي',
      type_instead: 'الكتابة بدلاً من ذلك',
      ask_placeholder: 'اسأل بلغتك…',
      audio_thinking: 'أقرأ الورقة…',
      audio_speaking: 'أتحدث',
      audio_done: 'اضغط للاستماع مرة أخرى',
      show_transcript: 'إظهار ما قيل',
      ask_again: 'أظهر ورقة أخرى',
      footer_built: 'مبني على Gemma 4',
      action_reminder_title: 'تم ضبط التذكير',
      action_reminder_desc: '{med} · {times} · {days} يوم',
      action_red_flag_title: 'اذهب إلى العيادة اليوم',
      action_red_flag_desc: '{symptom}',
      action_questions_title: 'الأسئلة جاهزة للعيادة',
      action_questions_desc: 'حول: {topic}',
      action_draft_title: 'تم صياغة الرد',
      action_draft_desc: '{intent}',
      action_lookup_title: 'شرح الدواء',
      action_lookup_desc: '{name}',
    },
  };

  // Per-paper default question — used when mic isn't available.
  const DEFAULT_Q = {
    hi:'yeh kya hai mujhe kya karna hai',  ta:'idhu enna seyya vendum',
    mr:'he kay aahe',                      bn:'eta ki, ki korbo',
    te:'idi enti',                          gu:'aa shu chhe',
    kn:'idu yenu',                          ml:'idu enthaan',
    pa:'eh ki hai',                         ur:'yeh kya hai',
    en:'what is this paper, what should I do',
    ar:'ما هذا، ماذا أفعل',
    es:'¿qué es esto y qué debo hacer?',
    fr:"qu'est-ce que c'est et que dois-je faire?",
    pt:'o que é isso e o que devo fazer?',
    ru:'что это и что мне делать?',
    de:'was ist das und was soll ich tun?',
    zh:'这是什么，我该怎么办？',
    ja:'これは何ですか、どうすればいいですか？',
    sw:'hii ni nini, nifanye nini?',
  };
  const fallbackQuestion = (code) => DEFAULT_Q[code] || DEFAULT_Q.en;

  // ── State ─────────────────────────────────────────────────────
  const LS_KEY = 'vaani.lang';
  const DEBUG = new URLSearchParams(location.search).get('debug') === '1';
  let user = readUser();
  let currentBlob = null;
  let currentName = null;
  let lastReply = null;        // string
  let lastReplyLang = null;    // code
  let isPlaying = false;

  function readUser() {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || 'null'); }
    catch { return null; }
  }
  function saveUser(lang) {
    user = lang;
    localStorage.setItem(LS_KEY, JSON.stringify(lang));
  }

  // ── i18n ─────────────────────────────────────────────────────
  function t(key, fallback) {
    const lang = (user && user.code) || 'en';
    return (STRINGS[lang] && STRINGS[lang][key])
        || STRINGS.en[key]
        || fallback || key;
  }
  function applyChrome() {
    if (!user) return;
    document.documentElement.lang = user.code;
    document.documentElement.dir = ['ar','ur','he','fa'].includes(user.code) ? 'rtl' : 'ltr';
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-attr]').forEach(el => {
      const [attr, key] = el.dataset.i18nAttr.split('|');
      el.setAttribute(attr, t(key));
    });
  }

  // ── Onboarding ────────────────────────────────────────────────
  const onb = document.getElementById('onboarding');
  const appRoot = document.getElementById('app-root');
  const langGrid = document.getElementById('lang-grid');
  const langList = document.getElementById('lang-list');
  const langSearch = document.getElementById('lang-search');

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
    if (langSearch && !langSearch._wired) {
      langSearch._wired = true;
      langSearch.addEventListener('input', e => {
        const q = e.target.value.trim().toLowerCase();
        Array.from(langList.children).forEach(c => {
          c.hidden = q && c.dataset.search.indexOf(q) === -1;
        });
      });
    }
  }
  function pickLang(lang) { saveUser(lang); showApp(); }
  function showOnboarding() {
    onb.hidden = false; appRoot.hidden = true;
    renderOnboarding();
  }
  function showApp() {
    onb.hidden = true; appRoot.hidden = false;
    applyChrome();
    document.getElementById('lang-chip-label').textContent =
      `${user.native} · ${user.english}`;
    if (DEBUG) document.getElementById('tool-call-fold').hidden = false;
    bootEngineLabel();
    renderSamples();
  }

  // ── Topbar lang chip ──────────────────────────────────────────
  document.getElementById('lang-chip').addEventListener('click', showOnboarding);

  // ── Bring a paper: upload / camera / drop / sample ───────────
  const dz = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const cameraInput = document.getElementById('camera-input');
  const uploadBtn = document.getElementById('upload-btn');
  const cameraBtn = document.getElementById('camera-btn');
  const paperGrid = document.getElementById('paper-grid');

  uploadBtn.addEventListener('click', () => fileInput.click());
  cameraBtn.addEventListener('click', () => cameraInput.click());
  fileInput.addEventListener('change', e => {
    if (e.target.files[0]) onPaperSelected(e.target.files[0]);
  });
  cameraInput.addEventListener('change', e => {
    if (e.target.files[0]) onPaperSelected(e.target.files[0]);
  });
  ['dragenter','dragover'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('drag'); }));
  ['dragleave','drop'].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('drag'); }));
  dz.addEventListener('drop', e => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) onPaperSelected(f);
  });
  function renderSamples() {
    const samples = [
      // The real one. Actual student's handwritten teacher notice, brought home in
      // a school bag. Devanagari handwriting; Gemma 4 reads it cold and replies.
      { url:'/samples/real_school_notice_handwritten.jpg',
        name:'real_school_notice_handwritten.jpg',
        tag: 'REAL · Handwritten',  urgent:false, real:true },
      { url:'/samples/prescription_hindi.jpg',     name:'prescription_hindi.jpg',
        tag: 'Hindi · Rx',          urgent:false },
      { url:'/samples/marathi_letter.jpg',         name:'marathi_letter.jpg',
        tag: 'Marathi · Letter',    urgent:false },
      { url:'/samples/ration_receipt_tamil.jpg',   name:'ration_receipt_tamil.jpg',
        tag: 'Tamil · Receipt',     urgent:false },
      { url:'/samples/fever_paper.jpg',            name:'fever_paper.jpg',
        tag: 'Urgent · Fever',      urgent:true  },
    ];
    paperGrid.innerHTML = '';
    samples.forEach(s => {
      const c = document.createElement('button');
      c.className = 'card' + (s.real ? ' real' : '');
      const tagCls = s.urgent ? ' urgent' : (s.real ? ' real' : '');
      c.innerHTML = `<img src="${s.url}" alt=""><span class="card-tag${tagCls}">${escape(s.tag)}</span>`;
      c.addEventListener('click', () => {
        fetch(s.url).then(r => r.blob()).then(blob => {
          onPaperSelected(new File([blob], s.name, { type: 'image/jpeg' }));
        });
      });
      paperGrid.appendChild(c);
    });
  }

  // ── Paper selected → show ask stage ──────────────────────────
  const askStage = document.getElementById('ask-stage');
  const paperPreview = document.getElementById('paper-preview');
  function onPaperSelected(file) {
    currentBlob = file;
    currentName = file.name || 'paper.jpg';
    paperPreview.src = URL.createObjectURL(file);
    askStage.hidden = false;
    document.getElementById('reply-stage').hidden = true;  // reset previous reply
    const app = document.querySelector('.app');
    app.classList.remove('reply-active');
    app.classList.add('ask-active');
    setTimeout(() => askStage.scrollIntoView({behavior:'smooth', block:'start'}), 60);
  }

  // ── Ask: hold-to-talk mic + type fallback ────────────────────
  const micBtn = document.getElementById('mic-btn');
  const micState = document.getElementById('mic-state');
  const questionEl = document.getElementById('question');
  const askBtn = document.getElementById('ask-btn');

  let recogniser = null;
  let isRecording = false;
  let micGotResult = false;

  function buildRecogniser() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.lang = (user && user.locale) || 'hi-IN';
    return r;
  }
  function setMicState(state) {
    micBtn.classList.toggle('recording', state === 'listening');
    const head = micState.querySelector('.mic-headline');
    const sub = micState.querySelector('.mic-sub');
    if (state === 'listening') {
      head.textContent = t('mic_listening');
      sub.textContent = t('mic_listening_sub');
    } else {
      head.textContent = t('mic_idle');
      sub.textContent = t('mic_idle_sub');
    }
  }

  function startListening() {
    if (isRecording) return;
    micGotResult = false;
    recogniser = buildRecogniser();
    if (!recogniser) {
      // No Speech API — instantly send fallback
      sendTurn(fallbackQuestion(user.code));
      return;
    }
    isRecording = true;
    setMicState('listening');
    recogniser.onresult = e => {
      micGotResult = true;
      sendTurn(e.results[0][0].transcript);
    };
    recogniser.onerror = e => {
      const code = e && e.error;
      stopRec();
      const recoverable = ['no-speech','not-allowed','service-not-allowed',
                           'audio-capture','aborted','network'].includes(code);
      if (!micGotResult && recoverable) sendTurn(fallbackQuestion(user.code));
    };
    recogniser.onend = () => {
      stopRec();
      // If recogniser stops cleanly without a result (headless / no audio device),
      // still fire the fallback so the demo flow continues.
      setTimeout(() => {
        if (!micGotResult) sendTurn(fallbackQuestion(user.code));
      }, 80);
    };
    try { recogniser.start(); }
    catch {
      stopRec();
      if (!micGotResult) sendTurn(fallbackQuestion(user.code));
    }
  }
  function stopRec() {
    isRecording = false;
    setMicState('idle');
    if (recogniser) try { recogniser.stop(); } catch {}
    recogniser = null;
  }
  // hold-to-talk: mousedown/touchstart starts, release stops
  micBtn.addEventListener('mousedown', startListening);
  micBtn.addEventListener('mouseup',   stopRec);
  micBtn.addEventListener('touchstart',e => { e.preventDefault(); startListening(); });
  micBtn.addEventListener('touchend',  e => { e.preventDefault(); stopRec(); });
  // tap fallback (single click → start, click again → still works via onend)
  micBtn.addEventListener('click', () => { if (!isRecording) startListening(); });

  askBtn.addEventListener('click', () => {
    const q = questionEl.value.trim() || fallbackQuestion(user.code);
    sendTurn(q);
  });
  questionEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') askBtn.click();
  });

  // ── /turn ─────────────────────────────────────────────────────
  const replyStage = document.getElementById('reply-stage');
  const audioCard = document.getElementById('audio-card');
  const audioDisc = document.getElementById('audio-disc');
  const audioReplay = document.getElementById('audio-replay');
  const audioStatus = document.getElementById('audio-status');
  const audioLang = document.getElementById('audio-lang');
  const iconPlay = document.getElementById('audio-icon-play');
  const iconStop = document.getElementById('audio-icon-stop');
  const transcriptFold = document.getElementById('transcript-fold');
  const transcriptEl = document.getElementById('transcript');
  const toolCallFold = document.getElementById('tool-call-fold');
  const toolCallPre = document.getElementById('tool-call');
  const actionCard = document.getElementById('action-card');
  const actionIcon = document.getElementById('action-icon');
  const actionTitle = document.getElementById('action-title');
  const actionDesc = document.getElementById('action-desc');
  const askAgain = document.getElementById('ask-again');

  audioReplay.addEventListener('click', () => {
    if (isPlaying) { stopSpeaking(); }
    else if (lastReply) { speak(lastReply, lastReplyLang); }
  });
  askAgain.addEventListener('click', () => {
    replyStage.hidden = true;
    askStage.hidden = true;
    const app = document.querySelector('.app');
    app.classList.remove('reply-active');
    app.classList.remove('ask-active');
    setTimeout(() => document.getElementById('bring').scrollIntoView({behavior:'smooth', block:'start'}), 60);
  });

  function setAudioState(state) {
    audioDisc.classList.toggle('playing', state === 'playing');
    audioReplay.classList.toggle('thinking', state === 'thinking');
    iconPlay.hidden = (state === 'playing');
    iconStop.hidden = (state !== 'playing');
    if (state === 'thinking') {
      audioStatus.textContent = t('audio_thinking');
    } else if (state === 'playing') {
      audioStatus.textContent = t('audio_speaking');
    } else {
      audioStatus.textContent = t('audio_done');
    }
  }

  async function sendTurn(question) {
    if (!currentBlob) return;
    replyStage.hidden = false;
    document.querySelector('.app').classList.add('reply-active');
    setAudioState('thinking');
    audioLang.textContent = `${user.native} · ${user.english}`;
    transcriptFold.removeAttribute('open');
    transcriptEl.textContent = '';
    actionCard.hidden = true;
    askAgain.hidden = true;
    if (!DEBUG) toolCallFold.hidden = true;
    // Pin the reply at the top of the viewport for a clean entrance.
    setTimeout(() => replyStage.scrollIntoView({behavior:'smooth', block:'start'}), 60);

    const fd = new FormData();
    fd.append('text', question);
    fd.append('lang', user.code);
    fd.append('image_filename', currentName);
    fd.append('image', currentBlob, currentName);

    let r;
    try {
      const res = await fetch('/turn', { method:'POST', body:fd });
      if (!res.ok) {
        const body = await res.text();
        showError(`Error ${res.status}: ${body.slice(0, 160)}`);
        return;
      }
      r = await res.json();
    } catch (e) {
      showError(`Network error: ${e.message}`);
      return;
    }

    lastReply = r.reply_text || '';
    lastReplyLang = r.language || user.code;
    transcriptEl.textContent = lastReply;
    renderActionCard(r.fn_calls || []);
    if (DEBUG || (r.fn_calls && r.fn_calls.length)) {
      toolCallFold.hidden = !DEBUG;
      toolCallPre.textContent = JSON.stringify(r.fn_calls || [], null, 2);
    }
    askAgain.hidden = false;

    // Auto-play
    speak(lastReply, lastReplyLang);
  }

  function showError(msg) {
    setAudioState('done');
    transcriptEl.textContent = msg;
    transcriptFold.setAttribute('open', '');
    askAgain.hidden = false;
  }

  // ── Action card: friendly localized summary of the tool call ─
  function renderActionCard(calls) {
    if (!calls || !calls.length) { actionCard.hidden = true; return; }
    const call = calls[0];
    const args = call.args || {};
    let icon = '📌', titleKey = '', descKey = '', urgent = false;
    switch (call.name) {
      case 'set_reminder':
        icon = '⏰';
        titleKey = 'action_reminder_title';
        descKey  = 'action_reminder_desc';
        break;
      case 'flag_red_flag':
        icon = '⚠️'; urgent = true;
        titleKey = 'action_red_flag_title';
        descKey  = 'action_red_flag_desc';
        break;
      case 'prepare_questions_for_clinic':
        icon = '🩺';
        titleKey = 'action_questions_title';
        descKey  = 'action_questions_desc';
        break;
      case 'draft_reply':
        icon = '📝';
        titleKey = 'action_draft_title';
        descKey  = 'action_draft_desc';
        break;
      case 'lookup_medicine_meaning':
        icon = '💊';
        titleKey = 'action_lookup_title';
        descKey  = 'action_lookup_desc';
        break;
      default:
        actionCard.hidden = true; return;
    }
    actionIcon.textContent = icon;
    actionTitle.textContent = t(titleKey);
    actionDesc.textContent = renderTemplate(t(descKey), args);
    actionCard.classList.toggle('urgent', urgent);
    actionCard.hidden = false;
  }
  function renderTemplate(tmpl, args) {
    return tmpl.replace(/\{(\w+)\}/g, (_, k) => {
      const v = args[k];
      if (Array.isArray(v)) return v.join(', ');
      return v != null ? String(v) : '';
    });
  }

  // ── TTS ──────────────────────────────────────────────────────
  function pickVoice(locale) {
    const voices = window.speechSynthesis.getVoices();
    if (!voices || !voices.length) return null;
    let v = voices.find(x => x.lang === locale);
    if (v) return v;
    const lang = locale.split('-')[0];
    v = voices.find(x => x.lang.startsWith(lang + '-'));
    if (v) return v;
    v = voices.find(x => x.lang === lang);
    return v || null;
  }
  function speak(text, langCode) {
    if (!text || !('speechSynthesis' in window)) {
      setAudioState('done');
      return;
    }
    try {
      const lang = ALL_LANGS.find(l => l.code === langCode) || user;
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang.locale;
      u.rate = 0.95;
      const v = pickVoice(lang.locale);
      if (v) u.voice = v;
      u.onstart = () => { isPlaying = true; setAudioState('playing'); };
      u.onend   = () => { isPlaying = false; setAudioState('done'); };
      u.onerror = () => { isPlaying = false; setAudioState('done'); };
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      // Some browsers don't fire onstart reliably; flip to playing immediately.
      setTimeout(() => { if (!isPlaying) setAudioState('playing'); }, 60);
    } catch {
      setAudioState('done');
    }
  }
  function stopSpeaking() {
    try { window.speechSynthesis.cancel(); } catch {}
    isPlaying = false;
    setAudioState('done');
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {};
  }

  // ── Boot ──────────────────────────────────────────────────────
  function bootEngineLabel() {
    // Engine is no longer shown to users — only logged for debug.
    fetch('/info').then(r => r.json()).then(j => {
      if (DEBUG) console.log('[vaani] engine:', j.engine);
    }).catch(() => {});
  }
  function escape(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  if (user) showApp();
  else showOnboarding();
})();

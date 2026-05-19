const API = '';

// Theme management
document.documentElement.setAttribute('data-theme', localStorage.getItem('parfindo-theme') || 'dark');

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('parfindo-theme', next);
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = next === 'dark' ? '☀' : '☽';
}

document.addEventListener('DOMContentLoaded', function() {
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀' : '☽';
});

// ── Step 1: main direction ────────────────────────────────────────────────────

const STEP1 = {
  id: 'branch',
  title: 'Какой вайб аромата тебе ближе?',
  hint: '',
  multi: false,
  cols: 3,
  options: [
    { value: 'fresh_clean',    emoji: '🌊', label: 'Fresh Clean',     sub: 'Свежий, лёгкий, чистый' },
    { value: 'warm_cozy',      emoji: '🕯️', label: 'Warm Cozy',       sub: 'Тёплый, уютный, обволакивающий' },
    { value: 'dark_sexy',      emoji: '🖤', label: 'Dark Sexy',        sub: 'Тёмный, чувственный, мощный' },
    { value: 'elegant_luxury', emoji: '👑', label: 'Elegant Luxury',   sub: 'Статусный, изысканный, дорогой' },
    { value: 'artistic_niche', emoji: '🎭', label: 'Artistic Niche',   sub: 'Авторский, редкий, концептуальный' },
    { value: 'soft_skin',      emoji: '🤍', label: 'Soft Skin Scent',  sub: 'Тихий, интимный, вторая кожа' },
  ],
};

// ── Branch question trees ─────────────────────────────────────────────────────

const STEP_KEYS = ['sub_type', 'vibe', 'notes', 'intensity', 'occasion', 'budget'];

const BUDGET_STEP = {
  id: 'budget',
  title: 'Какой бюджет тебе комфортен?',
  hint: '',
  multi: true,
  cols: 4,
  options: [
    { value: 'budget_1', emoji: '💛', label: 'До 2 500 ₽' },
    { value: 'budget_2', emoji: '🥈', label: '2 500 – 4 000 ₽' },
    { value: 'budget_3', emoji: '🥇', label: '4 000 – 6 000 ₽' },
    { value: 'budget_4', emoji: '💎', label: '6 000+ ₽' },
  ],
};

const BRANCHES = {

  fresh_clean: [
    {
      id: 'sub_type',
      title: 'Какая свежесть тебе ближе?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'marine',   emoji: '🌊', label: 'Морская',               sub: 'Соль, океан, бриз' },
        { value: 'citrus',   emoji: '🍋', label: 'Цитрусовая',            sub: 'Лимон, грейпфрут' },
        { value: 'clean',    emoji: '🚿', label: 'После душа',            sub: 'Мыльная, чистая' },
        { value: 'green',    emoji: '🌿', label: 'Зелёная',               sub: 'Трава, лист, ветивер' },
        { value: 'metallic', emoji: '❄️', label: 'Metallic fresh',        sub: 'Холодная, озоновая' },
      ],
    },
    {
      id: 'vibe',
      title: 'Какой вайб тебе нравится?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'luxury_hotel',          emoji: '🏨', label: 'Luxury hotel' },
        { value: 'summer_europe',         emoji: '☀️', label: 'Summer Europe' },
        { value: 'sporty_expensive',      emoji: '⚡', label: 'Sporty expensive' },
        { value: 'scandinavian_minimal',  emoji: '🪵', label: 'Scandinavian minimalism' },
        { value: 'rich_clean_person',     emoji: '✨', label: 'Rich clean person' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'citrus',  emoji: '🍋', label: 'Бергамот / цитрус' },
        { value: 'marine',  emoji: '🌊', label: 'Морская соль' },
        { value: 'musk',    emoji: '🤍', label: 'Белый мускус' },
        { value: 'woody',   emoji: '🌲', label: 'Кедр / дерево' },
        { value: 'vetiver', emoji: '🌿', label: 'Ветивер' },
        { value: 'spicy',   emoji: '🌶️', label: 'Перец / имбирь' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько заметным должен быть аромат?',
      hint: '',
      multi: true,
      cols: 4,
      options: [
        { value: 'very_light', emoji: '🌬️', label: 'Очень лёгкий' },
        { value: 'medium',     emoji: '🕐',  label: 'Средний' },
        { value: 'noticeable', emoji: '💫',  label: 'Заметный' },
        { value: 'strong',     emoji: '💪',  label: 'Сильный шлейф' },
      ],
    },
    {
      id: 'occasion',
      title: 'Где ты будешь носить аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'daily',        emoji: '☀️', label: 'Каждый день' },
        { value: 'office',       emoji: '💼', label: 'Офис' },
        { value: 'summer_trip',  emoji: '✈️', label: 'Лето / отпуск' },
        { value: 'sport',        emoji: '🏃', label: 'Спорт' },
        { value: 'summer_night', emoji: '🌙', label: 'Вечер летом' },
      ],
    },
    BUDGET_STEP,
  ],

  warm_cozy: [
    {
      id: 'sub_type',
      title: 'Что тебя согревает?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'vanilla_cream',  emoji: '🍦', label: 'Ваниль и крем',   sub: 'Сладкая, кремовая' },
        { value: 'spices_warm',    emoji: '🫖', label: 'Пряности',        sub: 'Корица, гвоздика' },
        { value: 'wood_resin',     emoji: '🪵', label: 'Дерево и смолы',  sub: 'Тёплое, тягучее' },
        { value: 'gourmand',       emoji: '🍮', label: 'Сладкий гурман',  sub: 'Карамель, выпечка' },
        { value: 'soft_musk_warm', emoji: '☁️', label: 'Мягкий мускус',   sub: 'Пудровый, нежный' },
      ],
    },
    {
      id: 'vibe',
      title: 'Какой вайб тебе нравится?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'sunday_morning',    emoji: '☕', label: 'Sunday morning at home' },
        { value: 'autumn_coffee',     emoji: '🍂', label: 'Autumn coffee shop' },
        { value: 'cashmere_fireplace',emoji: '🔥', label: 'Cashmere & fireplace' },
        { value: 'warm_skin_sun',     emoji: '🌅', label: 'Warm skin after sun' },
        { value: 'nordic_cabin',      emoji: '🏔️', label: 'Nordic cabin in winter' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'vanilla', emoji: '🍦', label: 'Ваниль / тонка' },
        { value: 'spicy',   emoji: '🫖', label: 'Корица / кардамон' },
        { value: 'woody',   emoji: '🪵', label: 'Сандал / кедр' },
        { value: 'vetiver', emoji: '🍂', label: 'Пачули' },
        { value: 'musk',    emoji: '☁️', label: 'Мускус' },
        { value: 'amber',   emoji: '🪸', label: 'Амбра' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько плотным должен быть аромат?',
      hint: '',
      multi: true,
      cols: 4,
      options: [
        { value: 'airy',        emoji: '🌬️', label: 'Лёгкий и воздушный' },
        { value: 'medium',      emoji: '🕐',  label: 'Средний' },
        { value: 'enveloping',  emoji: '🫂',  label: 'Обволакивающий' },
        { value: 'very_dense',  emoji: '💪',  label: 'Очень плотный' },
      ],
    },
    {
      id: 'occasion',
      title: 'Когда ты будешь носить аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'daily',        emoji: '☀️', label: 'Каждый день' },
        { value: 'autumn_winter',emoji: '🍂', label: 'Осень и зима' },
        { value: 'cozy_evening', emoji: '🕯️', label: 'Уютный вечер' },
        { value: 'date',         emoji: '🌹', label: 'Свидание' },
        { value: 'special',      emoji: '🥂', label: 'Особые случаи' },
      ],
    },
    BUDGET_STEP,
  ],

  dark_sexy: [
    {
      id: 'sub_type',
      title: 'Что тебе ближе?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'leather',     emoji: '🖤', label: 'Кожа',              sub: 'Тёмная, животная' },
        { value: 'tobacco',     emoji: '🚬', label: 'Табак',             sub: 'Сухой, насыщенный' },
        { value: 'smoke',       emoji: '🔥', label: 'Дым',               sub: 'Костёр, смола' },
        { value: 'alcohol',     emoji: '🥃', label: 'Алкогольные ноты',  sub: 'Ром, виски, коньяк' },
        { value: 'spices_dark', emoji: '🌶️', label: 'Специи',            sub: 'Перец, ладан' },
      ],
    },
    {
      id: 'vibe',
      title: 'Какой вайб тебе нравится?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'mafia_luxury',   emoji: '🕴️', label: 'Mafia luxury' },
        { value: 'dangerous',      emoji: '⚡', label: 'Dangerous' },
        { value: 'night_out',      emoji: '🌙', label: 'Night out' },
        { value: 'dominant',       emoji: '👁️', label: 'Dominant energy' },
        { value: 'dark_elegance',  emoji: '🖤', label: 'Dark elegance' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'leather', emoji: '🖤', label: 'Кожа' },
        { value: 'tobacco', emoji: '🚬', label: 'Табак / ром' },
        { value: 'oud',     emoji: '🕌', label: 'Уд / ладан' },
        { value: 'spicy',   emoji: '🌶️', label: 'Специи / перец' },
        { value: 'vetiver', emoji: '🌿', label: 'Ветивер / пачули' },
        { value: 'vanilla', emoji: '🍦', label: 'Ваниль' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько тяжёлым должен быть аромат?',
      hint: '',
      multi: true,
      cols: 4,
      options: [
        { value: 'light_sexy', emoji: '💋', label: 'Лёгкий sexy' },
        { value: 'medium',     emoji: '🕐', label: 'Средний' },
        { value: 'rich',       emoji: '🔥', label: 'Насыщенный' },
        { value: 'massive',    emoji: '💣', label: 'Очень мощный' },
      ],
    },
    {
      id: 'occasion',
      title: 'Когда ты будешь носить аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'date',        emoji: '🌹', label: 'Свидания' },
        { value: 'party',       emoji: '🎉', label: 'Вечеринки' },
        { value: 'autumn_winter',emoji: '🍂', label: 'Осень / зима' },
        { value: 'night_city',  emoji: '🌃', label: 'Ночной город' },
        { value: 'special',     emoji: '🥂', label: 'Особые события' },
      ],
    },
    BUDGET_STEP,
  ],

  elegant_luxury: [
    {
      id: 'sub_type',
      title: 'Какая luxury эстетика тебе ближе?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'old_money',     emoji: '🏛️', label: 'Old money',          sub: 'Классика, патина, история' },
        { value: 'quiet_luxury',  emoji: '🤍', label: 'Quiet luxury',        sub: 'Без логотипов, только качество' },
        { value: 'ceo',           emoji: '💼', label: 'CEO vibe',            sub: 'Власть, уверенность' },
        { value: 'european',      emoji: '🗼', label: 'European elegance',   sub: 'Французский шарм' },
        { value: 'hotel',         emoji: '🏨', label: 'Expensive hotel',     sub: 'Лобби пятизвёздочного отеля' },
      ],
    },
    {
      id: 'vibe',
      title: 'Как аромат должен ощущаться?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'expensive_calm',      emoji: '🧘', label: 'Дорого и спокойно' },
        { value: 'clean_status',        emoji: '✨', label: 'Чисто и статусно' },
        { value: 'wealth_no_logos',     emoji: '🤫', label: 'Wealth without logos' },
        { value: 'luxury_traveler',     emoji: '🌍', label: 'Luxury traveler' },
        { value: 'business_class',      emoji: '✈️', label: 'Business class energy' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'rose',    emoji: '🌹', label: 'Роза / жасмин' },
        { value: 'woody',   emoji: '🪵', label: 'Сандал / кедр' },
        { value: 'vetiver', emoji: '🌿', label: 'Ветивер' },
        { value: 'amber',   emoji: '🪸', label: 'Амбра' },
        { value: 'musk',    emoji: '🤍', label: 'Мускус' },
        { value: 'citrus',  emoji: '🌸', label: 'Нероли / бергамот' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько универсальным должен быть аромат?',
      hint: '',
      multi: true,
      cols: 4,
      options: [
        { value: 'max_universal', emoji: '🌐', label: 'Максимально универсальный' },
        { value: 'balanced',      emoji: '⚖️', label: 'Balanced luxury' },
        { value: 'more_niche',    emoji: '🎯', label: 'Более нишевый' },
        { value: 'very_rare',     emoji: '💎', label: 'Очень редкий' },
      ],
    },
    {
      id: 'occasion',
      title: 'Где ты будешь носить аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'work',         emoji: '💼', label: 'Работа' },
        { value: 'daily',        emoji: '☀️', label: 'Каждый день' },
        { value: 'restaurants',  emoji: '🍽️', label: 'Встречи / рестораны' },
        { value: 'travel',       emoji: '✈️', label: 'Путешествия' },
        { value: 'evening',      emoji: '🎭', label: 'Вечерние мероприятия' },
      ],
    },
    BUDGET_STEP,
  ],

  artistic_niche: [
    {
      id: 'sub_type',
      title: 'Что тебя привлекает в нишевой парфюмерии?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'unusual',     emoji: '🧪', label: 'Необычные ингредиенты', sub: 'То, чего нет в масс-маркете' },
        { value: 'narrative',   emoji: '📖', label: 'Авторская история',     sub: 'Парфюм как нарратив' },
        { value: 'rarity',      emoji: '💎', label: 'Редкость и эксклюзив',  sub: 'Не у каждого' },
        { value: 'bold',        emoji: '⚡', label: 'Смелые эксперименты',   sub: 'На грани, провокация' },
        { value: 'unexpected',  emoji: '🌀', label: 'Неожиданные сочетания', sub: 'Странная химия' },
      ],
    },
    {
      id: 'vibe',
      title: 'Какой вайб тебе нравится?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'art_gallery',     emoji: '🖼️', label: 'Art gallery opening' },
        { value: 'desert_midnight', emoji: '🌑', label: 'Desert at midnight' },
        { value: 'rain_hot_pavement',emoji: '🌧️', label: 'Rain on hot pavement' },
        { value: 'avantgarde',      emoji: '👗', label: 'Avant-garde fashion week' },
        { value: 'intellectual',    emoji: '📚', label: 'Intellectual minimalism' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'oud',     emoji: '🕌', label: 'Уд / ладан' },
        { value: 'vetiver', emoji: '🌿', label: 'Ветивер / пачули' },
        { value: 'amber',   emoji: '🪸', label: 'Амбра' },
        { value: 'musk',    emoji: '🤍', label: 'Мускус' },
        { value: 'leather', emoji: '🖤', label: 'Кожа' },
        { value: 'rose',    emoji: '🌸', label: 'Ирис / цветочные' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько авторским должен быть аромат?',
      hint: '',
      multi: true,
      cols: 4,
      options: [
        { value: 'wearable_odd', emoji: '🎯', label: 'Носибельный, но необычный' },
        { value: 'provocative',  emoji: '⚡', label: 'Провокационный' },
        { value: 'conceptual',   emoji: '🌀', label: 'Концептуальный' },
        { value: 'max_author',   emoji: '🎭', label: 'Максимально авторский' },
      ],
    },
    {
      id: 'occasion',
      title: 'Для кого / для чего этот аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'collection',  emoji: '📦', label: 'Для себя, как коллекция' },
        { value: 'impress',     emoji: '👀', label: 'Удивить окружающих' },
        { value: 'daily',       emoji: '☀️', label: 'Повседневно' },
        { value: 'special',     emoji: '🥂', label: 'На особые случаи' },
        { value: 'connoisseurs',emoji: '🎓', label: 'Для ценителей' },
      ],
    },
    BUDGET_STEP,
  ],

  soft_skin: [
    {
      id: 'sub_type',
      title: 'Какой тип «кожного» аромата?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'clean_musk',   emoji: '🤍', label: 'Чистый мускус',       sub: 'Нейтральный, прозрачный' },
        { value: 'powdery',      emoji: '🌸', label: 'Пудровый',            sub: 'Нежный, ирисовый' },
        { value: 'milky',        emoji: '🥛', label: 'Молочный / кремовый', sub: 'Тёплый, мягкий' },
        { value: 'barely_there', emoji: '🌫️', label: 'Едва заметный',       sub: 'Почти невидимый' },
        { value: 'warm_skin',    emoji: '🌅', label: 'Тёплая кожа',         sub: 'Как твоя кожа после тепла' },
      ],
    },
    {
      id: 'vibe',
      title: 'Какой вайб тебе нравится?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'second_skin',     emoji: '🤍', label: 'Second skin' },
        { value: 'just_showered',   emoji: '🚿', label: 'Just out of shower' },
        { value: 'intimate_close',  emoji: '💫', label: 'Intimate & close' },
        { value: 'clean_luxury',    emoji: '✨', label: 'Clean luxury' },
        { value: 'invisible_memo',  emoji: '👻', label: 'Invisible but memorable' },
      ],
    },
    {
      id: 'notes',
      title: 'Какие ноты тебе нравятся?',
      hint: 'Можно выбрать несколько',
      multi: true,
      cols: 3,
      options: [
        { value: 'musk',    emoji: '🤍', label: 'Мускус' },
        { value: 'amber',   emoji: '🪸', label: 'Амброксан / амбра' },
        { value: 'woody',   emoji: '🪵', label: 'Сандал' },
        { value: 'vanilla', emoji: '🥛', label: 'Ваниль / молочные' },
        { value: 'rose',    emoji: '🌸', label: 'Ирис' },
        { value: 'spicy',   emoji: '🌶️', label: 'Кардамон' },
      ],
    },
    {
      id: 'intensity',
      title: 'Насколько тихим должен быть аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'skin_close',  emoji: '🌫️', label: 'Едва слышный',       sub: 'Только ты знаешь' },
        { value: 'quiet',       emoji: '🤫', label: 'Тихий',              sub: 'Слышно вблизи' },
        { value: 'soft_trail',  emoji: '💫', label: 'Умеренный шлейф',   sub: 'Нежный след' },
      ],
    },
    {
      id: 'occasion',
      title: 'Когда ты будешь носить аромат?',
      hint: '',
      multi: true,
      cols: 3,
      options: [
        { value: 'daily',        emoji: '☀️', label: 'Каждый день' },
        { value: 'bed_scent',    emoji: '🛏️', label: 'Постельный аромат' },
        { value: 'date',         emoji: '🌹', label: 'Свидание' },
        { value: 'work',         emoji: '💼', label: 'Работа' },
        { value: 'just_because', emoji: '💝', label: 'Просто потому что' },
      ],
    },
    BUDGET_STEP,
  ],
};

// ── Quiz state ────────────────────────────────────────────────────────────────

let currentBranch = null;
let currentStep = 0; // 0 = step1, 1–6 = branch steps
const answers = {};

function currentQuestion() {
  if (currentStep === 0) return STEP1;
  return BRANCHES[currentBranch][currentStep - 1];
}

function totalSteps() {
  return 7; // step1 + 6 branch steps
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function startQuiz() {
  currentBranch = null;
  currentStep = 0;
  Object.keys(answers).forEach(k => delete answers[k]);
  renderQuestion();
  showScreen('screen-quiz');
}

function renderQuestion() {
  const q = currentQuestion();
  const pct = ((currentStep + 1) / totalSteps()) * 100;

  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = `${currentStep + 1} / ${totalSteps()}`;
  document.getElementById('question-title').textContent = q.title;
  document.getElementById('question-hint').textContent = q.hint || '';

  const grid = document.getElementById('cards-grid');
  grid.className = 'cards-grid cols-' + q.cols;
  grid.innerHTML = '';

  const selected = answers[q.id] || (q.multi ? [] : null);

  q.options.forEach(opt => {
    const card = document.createElement('div');
    card.className = 'card';

    const isSelected = q.multi
      ? Array.isArray(selected) && selected.includes(opt.value)
      : selected === opt.value;

    if (isSelected) card.classList.add('selected');

    card.innerHTML = `
      <div class="card-emoji">${opt.emoji}</div>
      <div class="card-label">${opt.label}</div>
      ${opt.sub ? `<div class="card-sub">${opt.sub}</div>` : ''}
    `;

    card.addEventListener('click', () => selectCard(q, opt.value, card));
    grid.appendChild(card);
  });

  const wrap = document.getElementById('question-wrap');
  wrap.style.animation = 'none';
  wrap.offsetHeight;
  wrap.style.animation = 'fadeUp 0.3s ease';

  updateNav();
}

function selectCard(q, value, cardEl) {
  if (q.multi) {
    if (!answers[q.id]) answers[q.id] = [];
    const idx = answers[q.id].indexOf(value);
    if (idx === -1) {
      answers[q.id].push(value);
      cardEl.classList.add('selected');
    } else {
      answers[q.id].splice(idx, 1);
      cardEl.classList.remove('selected');
    }
  } else {
    answers[q.id] = value;

    // If step 1, set branch
    if (currentStep === 0) {
      currentBranch = value;
    }

    document.querySelectorAll('#cards-grid .card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');
    setTimeout(() => nextQuestion(), 350);
  }
  updateNav();
}

function updateNav() {
  const q = currentQuestion();
  const val = answers[q.id];
  const hasAnswer = q.multi
    ? Array.isArray(val) && val.length > 0
    : !!val;

  document.getElementById('btn-back').disabled = currentStep === 0;
  document.getElementById('btn-next').disabled = !hasAnswer && !q.multi;

  if (q.multi) {
    document.getElementById('btn-next').disabled = false;
  }

  const isLast = currentStep === totalSteps() - 1;
  document.getElementById('btn-next').textContent = isLast ? 'Показать парфюмы ✦' : 'Далее →';
}

function nextQuestion() {
  if (currentStep < totalSteps() - 1) {
    currentStep++;
    renderQuestion();
  } else {
    submitQuiz();
  }
}

function prevQuestion() {
  if (currentStep > 0) {
    // If going back from step 2 → step 1, clear branch selection
    if (currentStep === 1) {
      currentBranch = null;
      delete answers['branch'];
    }
    currentStep--;
    renderQuestion();
  }
}

// ── Submission ────────────────────────────────────────────────────────────────

async function submitQuiz() {
  showScreen('screen-loading');

  try {
    const res = await fetch(`${API}/api/recommend/parfbar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answers),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    showResults(data.recommendations);
  } catch (err) {
    console.error(err);
    showError(err.message);
  }
}

// ── Results ───────────────────────────────────────────────────────────────────

const PLACEHOLDERS = ['🌸', '🌿', '🍋', '🪸', '🌹', '🍑', '🌊', '🕯️', '✨', '🌙'];

function showResults(recs) {
  const grid = document.getElementById('results-grid');
  grid.innerHTML = '';

  if (!recs || recs.length === 0) {
    grid.innerHTML = '<p style="color:var(--gray);text-align:center;grid-column:1/-1;padding:40px">Ароматы не найдены. Попробуй другие критерии.</p>';
    showScreen('screen-results');
    return;
  }

  recs.forEach((r, i) => {
    const card = document.createElement('div');
    card.className = 'result-card';
    const price = r.price ? `${Math.round(r.price).toLocaleString('ru-RU')} ₽` : '';
    const emoji = PLACEHOLDERS[i % PLACEHOLDERS.length];

    const imgHtml = r.image_url
      ? `<div class="result-img-wrap"><img class="result-img" src="${r.image_url}" alt="${r.name}" onerror="this.parentElement.innerHTML='<div class=result-img-placeholder>${emoji}</div>'" /></div>`
      : `<div class="result-img-wrap"><div class="result-img-placeholder">${emoji}</div></div>`;

    card.innerHTML = `
      ${imgHtml}
      <div class="result-body">
        <div class="result-num">Pick #${i + 1}</div>
        <div class="result-brand">${r.brand}</div>
        <div class="result-name">${r.name}</div>
        ${price ? `<div class="result-price">${price}</div>` : ''}
        <div class="result-reason">${r.reason}</div>
        <a class="result-link" href="${r.url}" target="_blank">Купить на Parfbar</a>
      </div>
    `;

    grid.appendChild(card);
  });

  showScreen('screen-results');
}

function showError(msg) {
  const grid = document.getElementById('results-grid');
  grid.innerHTML = `
    <div style="grid-column:1/-1;text-align:center;padding:40px">
      <div style="font-size:48px;margin-bottom:16px">⚠️</div>
      <p style="color:var(--gray);font-size:16px">Что-то пошло не так.<br>${msg}</p>
      <p style="color:var(--gray);font-size:13px;margin-top:8px">Убедитесь, что сервер запущен: <code>uvicorn main:app</code></p>
    </div>
  `;
  showScreen('screen-results');
}

function restart() {
  window.location.href = '/';
}

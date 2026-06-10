const API = '';

// ── Theme management ──────────────────────────────────────────────────────────
document.documentElement.setAttribute('data-theme', localStorage.getItem('parfindo-theme') || 'light');

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('parfindo-theme', next);
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = next === 'dark' ? '☀' : '☽';
}

document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀' : '☽';
});

// ── Quiz definition (линейный, образные вопросы → оси матчинга) ────────────────
// Значения опций для характеристик = целевой уровень low|medium|high.

const QUESTIONS = [
  {
    id: 'b_mood',
    title: 'С чего начнём — какое настроение ищешь?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'fresh_energy', emoji: '🌊', label: 'Свежесть и энергия', sub: 'Утро, бодрость, чистота' },
      { value: 'warm_cozy',    emoji: '🕯️', label: 'Тепло и уют',        sub: 'Обнять и не отпускать' },
      { value: 'seduction',    emoji: '💋', label: 'Соблазн и страсть',  sub: 'Вечер, притяжение' },
      { value: 'mystery',      emoji: '🌑', label: 'Тайна и глубина',    sub: 'Загадка, характер' },
      { value: 'tender',       emoji: '🤍', label: 'Нежность и чистота', sub: 'Лёгкость, кожа, пудра' },
      { value: 'gourmand_joy', emoji: '🍮', label: 'Сладкое удовольствие', sub: 'Десерт, тепло, радость' },
    ],
  },
  {
    id: 'b_sweetness',
    title: 'Десертный шлейф или строгая чистота?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'high',   emoji: '🍮', label: 'Сладкий, десертный', sub: 'Карамель, ваниль, крем' },
      { value: 'medium', emoji: '⚖️', label: 'Лёгкая сладость',    sub: 'Намёк, не приторно' },
      { value: 'low',    emoji: '🤍', label: 'Совсем не сладкий',  sub: 'Строго и чисто' },
    ],
  },
  {
    id: 'b_freshness',
    title: 'Аромат должен освежать или согревать?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'high',   emoji: '❄️', label: 'Освежающий, прохладный', sub: 'Лёд, вода, воздух' },
      { value: 'medium', emoji: '🌤️', label: 'Сбалансированный',       sub: 'Ни холодно, ни жарко' },
      { value: 'low',    emoji: '🔥', label: 'Согревающий, тёплый',     sub: 'Обволакивает, как плед' },
    ],
  },
  {
    id: 'b_brightness',
    title: 'Громко заявить о себе или тихий секрет для своих?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'high',   emoji: '💫', label: 'Яркий, заметный',  sub: 'Чтобы оборачивались' },
      { value: 'medium', emoji: '🌗', label: 'Умеренный',        sub: 'Заметен, но не кричит' },
      { value: 'low',    emoji: '🤫', label: 'Тихий, для близких', sub: 'Только для своих' },
    ],
  },
  {
    id: 'b_longevity',
    title: 'Когда ты уйдёшь — что останется в воздухе?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'high',   emoji: '🌫️', label: 'Густой шлейф',     sub: 'Тебя запомнят надолго' },
      { value: 'medium', emoji: '✨',  label: 'Лёгкий след',      sub: 'Приятное ощущение на пару часов' },
      { value: 'low',    emoji: '🫧',  label: 'Почти ничего',     sub: 'Только ты сама знаешь' },
    ],
  },
  {
    id: 'b_families',
    title: 'Что хочется вдохнуть прямо сейчас?',
    hint: 'Можно выбрать несколько',
    multi: true,
    cols: 4,
    options: [
      { value: 'floral',   emoji: '🌸', label: 'Цветы' },
      { value: 'gourmand', emoji: '🍮', label: 'Сладости' },
      { value: 'woody',    emoji: '🪵', label: 'Дерево, смолы' },
      { value: 'aquatic',  emoji: '🌊', label: 'Море, вода' },
      { value: 'green',    emoji: '🌿', label: 'Зелень, травы' },
      { value: 'citrus',   emoji: '🍋', label: 'Цитрус' },
      { value: 'mineral',  emoji: '🪨', label: 'Минералы, мистика' },
      { value: 'tobacco',  emoji: '🚬', label: 'Табак, кожа' },
    ],
  },
  {
    id: 'b_format',
    title: 'В каком формате хочешь попробовать?',
    hint: '',
    multi: false,
    cols: 3,
    options: [
      { value: 'sample', emoji: '🧪', label: 'Пробник',       sub: 'Присмотреться без риска' },
      { value: 'bottle', emoji: '🧴', label: 'Полный флакон', sub: 'Сразу свой' },
      { value: 'set',    emoji: '🎁', label: 'Собрать набор', sub: 'Себе или в подарок' },
    ],
  },
];

// ── Quiz state ────────────────────────────────────────────────────────────────

let currentStep = 0;
const answers = {};
let currentRecs = null;

function currentQuestion() { return QUESTIONS[currentStep]; }
function totalSteps() { return QUESTIONS.length; }

// ── Rendering ─────────────────────────────────────────────────────────────────

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function startQuiz() {
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
    document.querySelectorAll('#cards-grid .card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');
    setTimeout(() => nextQuestion(), 350);
  }
  updateNav();
}

function updateNav() {
  const q = currentQuestion();
  const val = answers[q.id];
  const hasAnswer = q.multi ? Array.isArray(val) && val.length > 0 : !!val;

  document.getElementById('btn-back').disabled = currentStep === 0;
  document.getElementById('btn-next').disabled = !hasAnswer && !q.multi;
  if (q.multi) document.getElementById('btn-next').disabled = false;

  const isLast = currentStep === totalSteps() - 1;
  document.getElementById('btn-next').textContent = isLast ? 'Показать ароматы ✦' : 'Далее →';
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
    currentStep--;
    renderQuestion();
  }
}

// ── Submission ────────────────────────────────────────────────────────────────

async function submitQuiz() {
  showScreen('screen-loading');
  try {
    const res = await fetch(`${API}/api/recommend/biblioteka`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answers),
    });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    showResults(data.recommendations, data.box);
  } catch (err) {
    console.error(err);
    showError(err.message);
  }
}

// ── Results ───────────────────────────────────────────────────────────────────

function addUTM(url) {
  if (!url) return '#';
  const sep = url.includes('?') ? '&' : '?';
  return url + sep + 'utm_source=aroma-match&utm_medium=quiz&utm_campaign=biblioteka';
}

const PLACEHOLDERS = ['🌸', '🌿', '🍋', '🪸', '🌹', '🍑', '🌊', '🕯️', '✨', '🌙'];

function showResults(recs, box) {
  currentRecs = recs;
  const grid = document.getElementById('results-grid');
  const boxBlock = document.getElementById('box-block');
  grid.innerHTML = '';
  boxBlock.innerHTML = '';

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

    const notesHtml = r.notes ? `<div class="result-notes">${r.notes}</div>` : '';

    card.innerHTML = `
      ${imgHtml}
      <div class="result-body">
        <div class="result-num">Pick #${i + 1}</div>
        <div class="result-brand">${r.brand}</div>
        <div class="result-name">${r.name}</div>
        ${price ? `<div class="result-price">${price}</div>` : ''}
        <div class="result-reason">${r.reason}</div>
        ${notesHtml}
        <div class="result-actions">
          <a class="result-link" href="${addUTM(r.url)}" target="_blank">Смотреть в магазине</a>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });

  renderBox(box);
  showScreen('screen-results');
}

function renderBox(box) {
  const boxBlock = document.getElementById('box-block');
  if (!box || !box.name) return;

  const price = box.price ? `${Math.round(box.price).toLocaleString('ru-RU')} ₽` : '';
  const imgHtml = box.image_url
    ? `<img class="box-card-img" src="${box.image_url}" alt="${box.name}" onerror="this.outerHTML='<div class=box-card-img-ph>🎁</div>'" />`
    : `<div class="box-card-img-ph">🎁</div>`;

  boxBlock.innerHTML = `
    <div class="box-divider">— ✦ А ещё тебе подойдёт готовый набор ✦ —</div>
    <div class="box-card">
      ${imgHtml}
      <div class="box-card-body">
        <div class="box-card-tag">Готовый бокс</div>
        <div class="box-card-name">${box.name}</div>
        ${box.description ? `<div class="box-card-desc">${box.description}</div>` : ''}
        <div class="box-card-foot">
          ${price ? `<div class="box-card-price">${price}</div>` : '<span></span>'}
          <a class="box-card-link" href="${addUTM(box.url)}" target="_blank">Открыть набор →</a>
        </div>
      </div>
    </div>
  `;
}

function showError(msg) {
  const grid = document.getElementById('results-grid');
  document.getElementById('box-block').innerHTML = '';
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
  window.location.href = '/biblioteka';
}

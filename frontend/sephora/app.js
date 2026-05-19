const API = ''; // relative — works on any host (localhost or tunnel)

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

const QUESTIONS = [
  {
    id: 'gender',
    title: 'Для кого ищем парфюм?',
    hint: '',
    multi: false,
    cols: 4,
    options: [
      { value: 'self',        emoji: '🪞', label: 'Для себя' },
      { value: 'gift_female', emoji: '🌸', label: 'Подарок женщине' },
      { value: 'gift_male',   emoji: '🎩', label: 'Подарок мужчине' },
      { value: 'unisex',      emoji: '✨', label: 'Унисекс' },
    ],
  },
  {
    id: 'budget',
    title: 'Какой у вас бюджет?',
    hint: '',
    multi: true,
    cols: 4,
    options: [
      { value: '$50-100',  emoji: '💛', label: '$50–100' },
      { value: '$100-200', emoji: '🥈', label: '$100–200' },
      { value: '$200-300', emoji: '🥇', label: '$200–300' },
      { value: '$300+',    emoji: '💎', label: '$300+' },
    ],
  },
  {
    id: 'occasion',
    title: 'Для какого случая?',
    hint: '',
    multi: true,
    cols: 4,
    options: [
      { value: 'daily',    emoji: '☀️', label: 'Каждый день' },
      { value: 'office',   emoji: '💼', label: 'Офис' },
      { value: 'romantic', emoji: '🕯️', label: 'Романтический вечер' },
      { value: 'event',    emoji: '🥂', label: 'Особое событие' },
    ],
  },
  {
    id: 'season',
    title: 'Для какого сезона?',
    hint: '',
    multi: true,
    cols: 3,
    options: [
      { value: 'summer', emoji: '☀️', label: 'Лето', sub: 'Жара, море' },
      { value: 'spring', emoji: '🌸', label: 'Весна / Осень', sub: 'Мягкая погода' },
      { value: 'winter', emoji: '❄️', label: 'Зима', sub: 'Холод, уют' },
    ],
  },
  {
    id: 'notes',
    title: 'Какая нота вам нравится?',
    hint: 'Можно выбрать несколько',
    multi: true,
    cols: 4,
    options: [
      { value: 'citrus',  emoji: '🍋', label: 'Цитрус',      sub: 'Лимон, бергамот, грейпфрут' },
      { value: 'rose',    emoji: '🌹', label: 'Флоральные',  sub: 'Роза, жасмин, пион' },
      { value: 'oud',     emoji: '🪵', label: 'Уд / Сандал', sub: 'Тёплое дерево, смола' },
      { value: 'vanilla', emoji: '🍦', label: 'Ваниль',      sub: 'Сладкая, кремовая' },
      { value: 'vetiver', emoji: '🌿', label: 'Ветивер',     sub: 'Землистый, зелёный' },
      { value: 'amber',   emoji: '🪸', label: 'Амбра / Мускус', sub: 'Чувственный, тёплый' },
      { value: 'fruits',  emoji: '🍑', label: 'Фрукты',      sub: 'Персик, груша, малина' },
      { value: 'marine',  emoji: '🌊', label: 'Морские',     sub: 'Свежесть, соль, озон' },
    ],
  },
  {
    id: 'longevity',
    title: 'Насколько стойкий аромат нужен?',
    hint: '',
    multi: true,
    cols: 3,
    options: [
      { value: 'light',  emoji: '🌬️', label: 'Лёгкий',      sub: '2–4 часа' },
      { value: 'medium', emoji: '🕐',  label: 'Средний',     sub: '4–8 часов' },
      { value: 'strong', emoji: '💪',  label: 'Весь день',   sub: '8+ часов' },
    ],
  },
  {
    id: 'sillage',
    title: 'Какой шлейф предпочитаете?',
    hint: '',
    multi: true,
    cols: 3,
    options: [
      { value: 'subtle',  emoji: '🤫', label: 'Незаметный',  sub: 'Только для вас' },
      { value: 'medium',  emoji: '😊', label: 'Умеренный',   sub: 'Слышно рядом' },
      { value: 'strong',  emoji: '🌟', label: 'Выраженный',  sub: 'Слышно в комнате' },
    ],
  },
  {
    id: 'brands',
    title: 'Есть любимый бренд?',
    hint: 'Можно выбрать несколько или пропустить',
    multi: true,
    cols: 4,
    options: [
      { value: 'Chanel',           emoji: '⬛', label: 'Chanel' },
      { value: 'Dior',             emoji: '🔵', label: 'Dior' },
      { value: 'Yves Saint Laurent', emoji: '💄', label: 'YSL' },
      { value: 'Tom Ford',         emoji: '🖤', label: 'Tom Ford' },
      { value: 'Byredo',           emoji: '🤍', label: 'Byredo' },
      { value: 'Jo Malone',        emoji: '🌿', label: 'Jo Malone' },
      { value: 'Maison Margiela',  emoji: '🫧', label: 'Margiela' },
      { value: 'Hermès',           emoji: '🧡', label: 'Hermès' },
    ],
  },
  {
    id: 'vibe',
    title: 'Какой вайб вам подходит?',
    hint: '',
    multi: true,
    cols: 3,
    options: [
      { value: 'forest', emoji: '🌲', label: 'Лес',           sub: 'Хвоя, земля, кора' },
      { value: 'beach',  emoji: '🏖️', label: 'Летний пляж',   sub: 'Море, солнце, бриз' },
      { value: 'fruits', emoji: '🍑', label: 'Фруктовый сад', sub: 'Сочно, свежо, ярко' },
      { value: 'night',  emoji: '🌙', label: 'Ночной город',  sub: 'Тёмно, загадочно' },
      { value: 'east',   emoji: '🕌', label: 'Восточный базар', sub: 'Специи, ладан, уд' },
      { value: 'snow',   emoji: '❄️', label: 'Снежная зима',  sub: 'Чисто, пудрово, легко' },
    ],
  },
  {
    id: 'style',
    title: 'Нишевое или хит?',
    hint: '',
    multi: true,
    cols: 3,
    options: [
      { value: 'niche',       emoji: '🎭', label: 'Нишевое',       sub: 'Необычное и редкое' },
      { value: 'bestseller',  emoji: '🏆', label: 'Проверенный хит', sub: 'Популярный и любимый' },
      { value: 'any',         emoji: '🎲', label: 'Без разницы',    sub: 'Удиви меня' },
    ],
  },
];

let currentQ = 0;
const answers = {};

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function startQuiz() {
  currentQ = 0;
  renderQuestion();
  showScreen('screen-quiz');
}

function renderQuestion() {
  const q = QUESTIONS[currentQ];
  const pct = ((currentQ + 1) / QUESTIONS.length) * 100;

  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = `${currentQ + 1} / ${QUESTIONS.length}`;
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

  // Animate question wrap
  const wrap = document.getElementById('question-wrap');
  wrap.style.animation = 'none';
  wrap.offsetHeight; // reflow
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
    // Auto-advance for single-select after short delay
    setTimeout(() => nextQuestion(), 350);
  }
  updateNav();
}

function updateNav() {
  const q = QUESTIONS[currentQ];
  const val = answers[q.id];
  const hasAnswer = q.multi
    ? Array.isArray(val) && val.length > 0
    : !!val;

  document.getElementById('btn-back').disabled = currentQ === 0;
  document.getElementById('btn-next').disabled = !hasAnswer && !q.multi;

  // For multi-select and optional brand question (Q8), always allow next
  if (q.id === 'brands' || q.multi) {
    document.getElementById('btn-next').disabled = false;
  }

  const isLast = currentQ === QUESTIONS.length - 1;
  document.getElementById('btn-next').textContent = isLast ? 'Показать парфюмы ✦' : 'Далее →';
}

function nextQuestion() {
  if (currentQ < QUESTIONS.length - 1) {
    currentQ++;
    renderQuestion();
  } else {
    submitQuiz();
  }
}

function prevQuestion() {
  if (currentQ > 0) {
    currentQ--;
    renderQuestion();
  }
}

async function submitQuiz() {
  showScreen('screen-loading');

  try {
    const res = await fetch(`${API}/api/recommend/sephora`, {
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

const PLACEHOLDERS = ['🌸', '🌿', '🍋', '🪸', '🌹', '🍑', '🌊', '🕯️', '✨', '🌙'];

function showResults(recs) {
  const grid = document.getElementById('results-grid');
  grid.innerHTML = '';

  if (!recs || recs.length === 0) {
    grid.innerHTML = '<p style="color:var(--text2);text-align:center;grid-column:1/-1;padding:40px">Парфюмы не найдены. Попробуйте другие критерии.</p>';
    showScreen('screen-results');
    return;
  }

  recs.forEach((r, i) => {
    const card = document.createElement('div');
    card.className = 'result-card';
    const price = r.price ? `$${r.price.toFixed(0)}` : '';
    const emoji = PLACEHOLDERS[i % PLACEHOLDERS.length];

    const imgHtml = r.image_url
      ? `<div class="result-img-wrap"><img class="result-img" src="${r.image_url}" alt="${r.name}" onerror="this.parentElement.innerHTML='<div class=result-img-placeholder>${emoji}</div>'" /></div>`
      : `<div class="result-img-wrap"><div class="result-img-placeholder">${emoji}</div></div>`;

    const query = encodeURIComponent(`${r.brand} ${r.name}`);
    const stores = [
      { label: 'Sephora',   href: `https://www.sephora.com/search?keyword=${query}` },
      { label: 'Profumum',  href: `https://profumum.ru/catalog/?q=${query}` },
      { label: 'Parfbar',   href: `https://parfbar.com/?s=${query}` },
    ];
    const storeLinks = stores.map(s =>
      `<a class="result-link" href="${s.href}" target="_blank">${s.label}</a>`
    ).join('');

    const accordsHtml = r.accords && r.accords.length
      ? `<div class="result-accords">${r.accords.slice(0, 4).map(a => `<span class="accord-tag">${a}</span>`).join('')}</div>`
      : '';

    card.innerHTML = `
      ${imgHtml}
      <div class="result-body">
        <div class="result-num">Pick #${i + 1}</div>
        <div class="result-brand">${r.brand}</div>
        <div class="result-name">${r.name}</div>
        ${accordsHtml}
        ${price ? `<div class="result-price">${price}</div>` : ''}
        <div class="result-reason">${r.reason}</div>
        <div class="result-links">${storeLinks}</div>
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
      <p style="color:var(--text2);font-size:16px">Что-то пошло не так.<br>${msg}</p>
      <p style="color:var(--text3);font-size:13px;margin-top:8px">Убедитесь, что сервер запущен: <code>uvicorn main:app</code></p>
    </div>
  `;
  showScreen('screen-results');
}

function restart() {
  window.location.href = '/';
}

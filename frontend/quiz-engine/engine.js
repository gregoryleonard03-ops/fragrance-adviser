/*
 * Quiz engine: renders any quiz described by a JSON config. One renderer,
 * N quizzes — replaces the copy-pasted app.js per store.
 *
 * Config shape:
 *   {
 *     "id": "mood",
 *     "steps": [step, ...],              // linear steps, in order
 *     "branches": { "key": [step, ...] } // optional; entered via option.goto
 *   }
 * Step:   { id, title, hint, multi, cols, options: [...] }
 *         id starting with "_" is UI-only: selection not written to answers
 *         (option.maps still applies).
 *         { "$ref": "name" } inside steps/branches resolves to config.shared[name]
 *         — for steps repeated across branches (e.g. budget).
 * Option: { value, emoji, label, sub?, maps?, goto? }
 *         maps — answers fragment merged on selection: lists union,
 *                strings first-wins.
 *         goto — on single-select: continue with branches[goto] after the
 *                linear steps.
 *
 * Pure flow core (no DOM) is exported for Node tests; QuizEngine.mount()
 * wires it to the DOM. Mechanics ported from parfbar/app.js: card grid,
 * multi/cols, 350ms auto-advance on single-select, progress bar.
 */

// ── Pure flow core ────────────────────────────────────────────────────────────

function createFlow(config) {
  return {
    config: config,
    sel: {},          // step.id → value | [values]
    branch: null,     // active branch key
    idx: 0,
  };
}

function _resolve(config, step) {
  return step.$ref ? (config.shared || {})[step.$ref] : step;
}

function sequence(flow) {
  const base = flow.config.steps;
  const br = flow.branch ? (flow.config.branches || {})[flow.branch] || [] : [];
  return base.concat(br).map(function (s) { return _resolve(flow.config, s); });
}

function totalSteps(flow) {
  if (flow.branch || !flow.config.branches) return sequence(flow).length;
  // branch not chosen yet — assume the longest branch for the progress bar
  const lens = Object.values(flow.config.branches).map(function (b) { return b.length; });
  return flow.config.steps.length + Math.max.apply(null, lens.concat([0]));
}

function currentStep(flow) {
  return sequence(flow)[flow.idx];
}

function select(flow, value) {
  const step = currentStep(flow);
  if (step.multi) {
    const cur = flow.sel[step.id] || (flow.sel[step.id] = []);
    const i = cur.indexOf(value);
    if (i === -1) cur.push(value); else cur.splice(i, 1);
    return false; // no auto-advance
  }
  flow.sel[step.id] = value;
  const opt = step.options.find(function (o) { return o.value === value; });
  if (opt && opt.goto) flow.branch = opt.goto;
  return true; // auto-advance
}

function canProceed(flow) {
  const step = currentStep(flow);
  if (step.multi) {
    // multi steps are skippable (parfbar behavior) unless the config sets min
    const n = (flow.sel[step.id] || []).length;
    return n >= (step.min || 0);
  }
  const v = flow.sel[step.id];
  return v !== undefined && v !== null;
}

function isLast(flow) {
  return flow.idx === sequence(flow).length - 1 && (flow.branch || !flow.config.branches);
}

function next(flow) {
  if (flow.idx < sequence(flow).length - 1) { flow.idx++; return true; }
  return false; // caller submits
}

function prev(flow) {
  if (flow.idx === 0) return false;
  flow.idx--;
  // stepping back onto the step where the branch was chosen: drop the branch
  const step = currentStep(flow);
  if (!step.multi && step.options.some(function (o) { return o.goto; })) {
    flow.branch = null;
    delete flow.sel[step.id];
  }
  return true;
}

function mergeMaps(ans, maps) {
  for (const k in maps) {
    const v = maps[k];
    if (Array.isArray(v)) {
      const cur = Array.isArray(ans[k]) ? ans[k] : (ans[k] ? [ans[k]] : []);
      for (const x of v) if (cur.indexOf(x) === -1) cur.push(x);
      ans[k] = cur;
    } else if (!ans[k]) {
      ans[k] = v;
    }
  }
}

function getAnswers(flow) {
  const ans = {};
  for (const step of sequence(flow)) {
    const sel = flow.sel[step.id];
    if (sel == null || (Array.isArray(sel) && sel.length === 0)) continue;
    if (step.id.charAt(0) !== '_') {
      ans[step.id] = Array.isArray(sel) ? sel.slice() : sel;
    }
    const vals = Array.isArray(sel) ? sel : [sel];
    for (const v of vals) {
      const opt = step.options.find(function (o) { return o.value === v; });
      if (opt && opt.maps) mergeMaps(ans, opt.maps);
    }
  }
  return ans;
}

// ── DOM renderer (parfbar mechanics) ──────────────────────────────────────────
// Expects the host page to contain: #progress-fill, #progress-text,
// #question-title, #question-hint, #cards-grid, #question-wrap, #btn-back, #btn-next.

const QuizEngine = {
  flow: null,
  onSubmit: null,
  submitLabel: 'Show my scents ✦',
  nextLabel: 'Next →',

  mount: function (config, opts) {
    this.flow = createFlow(config);
    this.onSubmit = (opts && opts.onSubmit) || function () {};
    this.onExit = (opts && opts.onExit) || null; // Back on step 1 → leave the quiz
    if (opts && opts.submitLabel) this.submitLabel = opts.submitLabel;
    document.getElementById('btn-back').onclick = QuizEngine.prevQuestion;
    document.getElementById('btn-next').onclick = QuizEngine.nextQuestion;
    this.render();
  },

  render: function () {
    const flow = this.flow;
    const q = currentStep(flow);
    const pct = ((flow.idx + 1) / totalSteps(flow)) * 100;

    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('progress-text').textContent = (flow.idx + 1) + ' / ' + totalSteps(flow);
    document.getElementById('question-title').textContent = q.title;
    document.getElementById('question-hint').textContent = q.hint || '';

    const grid = document.getElementById('cards-grid');
    grid.className = 'cards-grid cols-' + (q.cols || 3);
    grid.innerHTML = '';

    const selected = flow.sel[q.id];
    q.options.forEach(function (opt) {
      const card = document.createElement('div');
      card.className = 'card';
      if (opt.bg) { card.classList.add('tile'); card.style.background = opt.bg; }
      const isSel = q.multi
        ? Array.isArray(selected) && selected.indexOf(opt.value) !== -1
        : selected === opt.value;
      if (isSel) card.classList.add('selected');
      card.innerHTML =
        (opt.emoji ? '<div class="card-emoji">' + opt.emoji + '</div>' : '') +
        '<div class="card-label">' + opt.label + '</div>' +
        (opt.sub ? '<div class="card-sub">' + opt.sub + '</div>' : '');
      card.addEventListener('click', function () { QuizEngine.selectCard(q, opt.value, card); });
      grid.appendChild(card);
    });

    const wrap = document.getElementById('question-wrap');
    wrap.style.animation = 'none';
    void wrap.offsetHeight;
    wrap.style.animation = 'fadeUp 0.3s ease';

    this.updateNav();
  },

  selectCard: function (q, value, cardEl) {
    const advance = select(this.flow, value);
    if (advance) {
      const cards = document.querySelectorAll('#cards-grid .card');
      cards.forEach(function (c) { c.classList.remove('selected'); });
      cardEl.classList.add('selected');
      setTimeout(function () { QuizEngine.nextQuestion(); }, 350);
    } else {
      cardEl.classList.toggle('selected');
    }
    this.updateNav();
  },

  updateNav: function () {
    document.getElementById('btn-back').disabled = this.flow.idx === 0 && !this.onExit;
    document.getElementById('btn-next').disabled = !canProceed(this.flow);
    document.getElementById('btn-next').textContent =
      isLast(this.flow) ? this.submitLabel : this.nextLabel;
  },

  nextQuestion: function () {
    if (next(QuizEngine.flow)) QuizEngine.render();
    else QuizEngine.onSubmit(getAnswers(QuizEngine.flow));
  },

  prevQuestion: function () {
    if (prev(QuizEngine.flow)) QuizEngine.render();
    else if (QuizEngine.onExit) QuizEngine.onExit();
  },
};

if (typeof module !== 'undefined') {
  module.exports = { createFlow, sequence, totalSteps, currentStep, select, canProceed, isLast, next, prev, getAnswers };
}

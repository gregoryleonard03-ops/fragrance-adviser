/*
 * Stage 1 regression, part 1 (JS): the engine driving mood.json must produce
 * the exact same answers dict that parfbar/app.js produces for the same clicks
 * (plus the /match-only gender step).
 * Part 2 (Python, test_regression.py) feeds these answers to the scorer and
 * compares top-5 against the old /parfbar path.
 * Run: node test_engine.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'quizzes', 'mood.json'), 'utf8'));

// Simulate a full quiz pass: gender → branch → selections per step id
function run(gender, branchValue, picks) {
  const flow = E.createFlow(config);
  assert.strictEqual(E.currentStep(flow).id, 'gender');
  E.select(flow, gender);
  E.next(flow);
  E.select(flow, branchValue);           // single-select → sets branch
  assert.strictEqual(flow.branch, branchValue);
  while (E.next(flow)) {
    const step = E.currentStep(flow);
    for (const v of picks[step.id] || []) E.select(flow, v);
  }
  return E.getAnswers(flow);
}

// Case 1: dark_sexy — mirrors the parfbar manual test in matcher_db.__main__
const a1 = run('', 'dark_sexy', {
  sub_type: ['leather'],
  vibe: ['night_out'],
  notes: ['oud', 'tobacco'],
  occasion: ['date'],
  budget: [],
});
assert.deepStrictEqual(a1, {
  gender: '',
  branch: 'dark_sexy',
  sub_type: ['leather'],
  vibe: ['night_out'],
  notes: ['oud', 'tobacco'],
  occasion: ['date'],
});

// Case 2: fresh_clean with budget + gender
const a2 = run('women', 'fresh_clean', {
  sub_type: ['citrus', 'marine'],
  vibe: ['luxury_hotel'],
  notes: ['citrus', 'musk'],
  occasion: ['office', 'daily'],
  budget: ['budget_1', 'budget_2'],
});
assert.deepStrictEqual(a2, {
  gender: 'women',
  branch: 'fresh_clean',
  sub_type: ['citrus', 'marine'],
  vibe: ['luxury_hotel'],
  notes: ['citrus', 'musk'],
  occasion: ['office', 'daily'],
  budget: ['budget_1', 'budget_2'],
});

// Case 3: multi-select toggle removes a value
{
  const flow = E.createFlow(config);
  E.select(flow, '');
  E.next(flow);
  E.select(flow, 'warm_cozy');
  E.next(flow);
  E.select(flow, 'gourmand');
  E.select(flow, 'vanilla_cream');
  E.select(flow, 'gourmand'); // toggle off
  assert.deepStrictEqual(E.getAnswers(flow).sub_type, ['vanilla_cream']);
}

// Case 4: going back to the branch step clears the branch (parfbar behavior)
{
  const flow = E.createFlow(config);
  E.select(flow, '');
  E.next(flow);
  E.select(flow, 'soft_skin');
  E.next(flow);
  E.prev(flow); // back onto the goto step
  assert.strictEqual(flow.branch, null);
  assert.strictEqual(E.getAnswers(flow).branch, undefined);
}

// Case 5: maps merge — lists union, strings first-wins (for characters/places quizzes)
{
  const flow = E.createFlow({
    steps: [{
      id: '_who', title: 't', multi: true, cols: 2,
      options: [
        { value: 'a', label: 'A', maps: { branch: 'dark_sexy', vibe: ['night_out', 'dominant'] } },
        { value: 'b', label: 'B', maps: { branch: 'warm_cozy', vibe: ['dominant', 'sunday_morning'], notes: ['oud'] } },
      ],
    }],
  });
  E.select(flow, 'a');
  E.select(flow, 'b');
  const got = E.getAnswers(flow);
  assert.deepStrictEqual(got, {
    branch: 'dark_sexy', // first wins
    vibe: ['night_out', 'dominant', 'sunday_morning'], // union, no dupes
    notes: ['oud'],
  });
  assert.strictEqual(got._who, undefined); // "_" steps stay out of answers
}

// Case 6: every branch reaches the shared budget step via $ref and ends
{
  const gotoStepIdx = config.steps.findIndex(s => (s.options || []).some(o => o.goto));
  for (const br of Object.keys(config.branches)) {
    const flow = E.createFlow(config);
    while (flow.idx < gotoStepIdx) { E.select(flow, E.currentStep(flow).options[0].value); E.next(flow); }
    const first = E.currentStep(flow).options.find(o => o.goto === br);
    E.select(flow, first.value);
    while (E.next(flow)) { /* walk to the end */ }
    assert.strictEqual(E.currentStep(flow).id, 'budget', `branch ${br} must end on budget`);
    assert.ok(E.isLast(flow), `branch ${br} must report isLast on budget`);
  }
}

// Case 7: min-selection gate (moodboard tiles)
{
  const mb = JSON.parse(fs.readFileSync(path.join(__dirname, 'quizzes', 'moodboard.json'), 'utf8'));
  const flow = E.createFlow(mb);
  E.select(flow, 'women');
  E.next(flow);
  assert.strictEqual(E.currentStep(flow).id, '_mood');
  assert.strictEqual(E.canProceed(flow), false, 'moodboard must require >=1 tile');
  E.select(flow, mb.steps[1].options[0].value);
  assert.strictEqual(E.canProceed(flow), true);
}

console.log('test_engine: all OK');
process.stdout.write('ANSWERS_JSON:' + JSON.stringify([a1, a2]) + '\n');

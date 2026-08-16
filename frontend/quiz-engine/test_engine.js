/*
 * Stage 1 regression, part 1 (JS): the engine driving mood.json must produce
 * the exact same answers dict that parfbar/app.js produces for the same clicks.
 * Part 2 (Python, test_regression.py) feeds these answers to the scorer and
 * compares top-5 against the old /parfbar path.
 * Run: node test_engine.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const E = require('./engine.js');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'quizzes', 'mood.json'), 'utf8'));

// Simulate a full quiz pass: pick branch, then selections per step id
function run(branchValue, picks) {
  const flow = E.createFlow(config);
  E.select(flow, branchValue);           // step 1, single-select → sets branch
  assert.strictEqual(flow.branch, branchValue);
  while (E.next(flow)) {
    const step = E.currentStep(flow);
    for (const v of picks[step.id] || []) E.select(flow, v);
  }
  return E.getAnswers(flow);
}

// Case 1: dark_sexy — mirrors the parfbar manual test in matcher_db.__main__
const a1 = run('dark_sexy', {
  sub_type: ['leather'],
  vibe: ['night_out'],
  notes: ['oud', 'tobacco'],
  occasion: ['date'],
  budget: [],
});
assert.deepStrictEqual(a1, {
  branch: 'dark_sexy',
  sub_type: ['leather'],
  vibe: ['night_out'],
  notes: ['oud', 'tobacco'],
  occasion: ['date'],
});

// Case 2: fresh_clean with budget
const a2 = run('fresh_clean', {
  sub_type: ['citrus', 'marine'],
  vibe: ['luxury_hotel'],
  notes: ['citrus', 'musk'],
  occasion: ['office', 'daily'],
  budget: ['budget_1', 'budget_2'],
});
assert.deepStrictEqual(a2, {
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
  E.select(flow, 'warm_cozy');
  E.next(flow);
  E.select(flow, 'gourmand');
  E.select(flow, 'vanilla_cream');
  E.select(flow, 'gourmand'); // toggle off
  assert.deepStrictEqual(E.getAnswers(flow).sub_type, ['vanilla_cream']);
}

// Case 4: going back to step 1 clears the branch (parfbar behavior)
{
  const flow = E.createFlow(config);
  E.select(flow, 'soft_skin');
  E.next(flow);
  E.prev(flow);
  assert.strictEqual(flow.branch, null);
  assert.strictEqual(E.getAnswers(flow).branch, undefined);
}

// Case 5: maps merge — lists union, strings first-wins (for characters/places quizzes)
{
  const ans = {};
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
for (const br of Object.keys(config.branches)) {
  const flow = E.createFlow(config);
  const first = config.steps[0].options.find(o => o.goto === br);
  E.select(flow, first.value);
  let steps = 0;
  while (E.next(flow)) steps++;
  assert.strictEqual(E.currentStep(flow).id, 'budget', `branch ${br} must end on budget`);
  assert.ok(E.isLast(flow), `branch ${br} must report isLast on budget`);
}

console.log('test_engine: all OK');
process.stdout.write('ANSWERS_JSON:' + JSON.stringify([a1, a2]) + '\n');

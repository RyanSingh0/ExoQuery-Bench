"use strict";
const $ = (s) => document.querySelector(s);
const state = {questions: [], selected: null, detail: null, tab: "Evidence", lastRun: null};
function el(tag, text, cls) { const n = document.createElement(tag); if (text != null) n.textContent = text; if (cls) n.className = cls; return n; }
function append(parent, ...children) { children.forEach(c => parent.append(c)); return parent; }
function button(text, action, cls = "secondary") { const b = el("button", text, cls); b.type = "button"; b.addEventListener("click", action); return b; }
async function api(path, payload) {
  const r = await fetch(path, payload ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)} : {});
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
  return data;
}
function download(name, data) { const u = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: "application/json"})); const a = el("a"); a.href = u; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(u), 1000); }
function error(node, e) { node.replaceChildren(el("p", e.message, "error")); }
function library() {
  const term = $("#search").value.toLowerCase(), level = $("#difficulty").value;
  const filtered = state.questions.filter(q => (level === "all" || q.difficulty === level) && `${q.id} ${q.family} ${q.title} ${q.prompt} ${q.tags.join(" ")}`.toLowerCase().includes(term));
  $("#count").textContent = filtered.length;
  $("#questions").replaceChildren(...filtered.map(q => {
    const b = button(q.title, () => select(q.id), "q-button");
    b.setAttribute("aria-pressed", String(q.id === state.selected));
    b.append(el("small", `${q.id} · ${q.difficulty} · ${q.family}`)); return b;
  }));
  if (!filtered.length) $("#questions").append(el("p", "No questions match. Try another search.", "muted"));
}
async function select(id) {
  state.selected = id; state.lastRun = null; state.tab = "Evidence"; library();
  const detail = $("#detail"); detail.replaceChildren(el("p", "Loading evidence…"));
  try { const data = await api(`/api/questions/${id}`); if (id !== state.selected) return; state.detail = data; render(); }
  catch (e) { if (id === state.selected) error(detail, e); }
}
function render() {
  const {question: q} = state.detail, main = $("#detail");
  const head = el("div", null, "question-head");
  append(head, el("p", `${q.id} / ${q.family.toUpperCase()}`, "eyebrow"), el("h2", q.title), el("p", q.prompt));
  const tags = el("div", null, "tags"); [q.difficulty, ...q.tags, "expert review pending"].forEach(t => tags.append(el("span", t, "chip"))); head.append(tags);
  const tabs = el("div", null, "tabs"); tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", "Question workspace");
  for (const name of ["Evidence", "Compare", "Review"]) { const b = button(name, () => {state.tab = name; render(); $("[aria-selected=true]").focus();}, "tab"); b.id = `tab-${name}`; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", String(name === state.tab)); b.setAttribute("aria-controls", "question-panel"); b.addEventListener("keydown", e => { if (["ArrowLeft", "ArrowRight"].includes(e.key)) { e.preventDefault(); const names = ["Evidence", "Compare", "Review"]; state.tab = names[(names.indexOf(name) + (e.key === "ArrowRight" ? 1 : 2)) % 3]; render(); $("[aria-selected=true]").focus(); } }); tabs.append(b); }
  const panel = el("div", null, "panel"); panel.id = "question-panel"; panel.setAttribute("role", "tabpanel"); panel.setAttribute("aria-labelledby", `tab-${state.tab}`);
  main.replaceChildren(head, tabs, panel);
  if (state.tab === "Evidence") evidence(panel); else if (state.tab === "Compare") compare(panel); else review(panel);
}
function evidence(panel) {
  const {question:q, reference:r} = state.detail;
  if (!r) { append(panel, el("h3", `Expected action: ${q.decision}`), el("p", q.caveat), el("p", "A correct decision still needs a scientifically sound explanation. No archive query is executed for this item.", "muted")); return; }
  const heading = el("div", null, "panel-label"); append(heading, el("h3", "Reference query"), el("span", "Machine checks passed", "badge"));
  append(panel, heading, el("pre", q.query));
  if (q.take) panel.append(el("p", `The full ${r.provenance.source_row_count.toLocaleString()}-row result was checked before taking the first ${q.take} rows locally.`, "muted"));
  panel.append(el("h3", "Stored result"));
  const wrap = el("div", null, "table-wrap"), table = el("table"), th = el("tr"), body = el("tbody");
  for (const c of q.columns) { const cell = el("th", `${c.name}${c.unit ? ` (${c.unit})` : ""}`); cell.scope = "col"; th.append(cell); }
  const thead = el("thead"); thead.append(th); table.append(thead);
  r.rows.forEach(row => { const tr = el("tr"); q.columns.forEach(c => { const v = row[c.name]; const td = el("td", v === null ? "null" : String(v)); td.title = td.textContent; tr.append(td); }); body.append(tr); }); table.append(body); wrap.append(table); panel.append(wrap);
  panel.append(el("div", q.caveat, "callout"));
  const p = el("div", null, "provenance");
  for (const [label, value] of [["Captured (UTC)", r.provenance.finished_at.replace("T", " ").slice(0,19)], ["Source", "NASA Exoplanet Archive / TAP"], ["Raw-response SHA-256", r.provenance.sha256], ["Evidence status", "Saved capture · expert review pending"]]) { const d = el("div", label); d.append(el("strong", value)); p.append(d); } panel.append(p);
  panel.append(append(el("div", null, "buttons"), button("Download question & evidence", () => download(`${q.id}-evidence.json`, state.detail))));
}
function compare(panel) {
  const {question:q, reference:r} = state.detail;
  append(panel, el("h3", "Compare a candidate result"), el("p", "Paste a result table with its units. This checks agreement with the saved reference; it does not execute a query or call a model.", "muted"));
  const label = el("label", "Candidate decision", "field-label"); label.htmlFor = "decision";
  const decision = el("select"); decision.id = "decision"; ["answer", "clarify", "abstain"].forEach(s => { const o = el("option", s); o.value = s; decision.append(o); }); decision.value = "answer";
  append(panel, label, decision);
  const editorLabel = el("label", "Result JSON (required for an answer)", "field-label"); editorLabel.htmlFor = "candidate";
  const editor = el("textarea", null, "editor"); editor.id = "candidate"; editor.spellcheck = false; editor.value = JSON.stringify({status:"ok", rows:[], units:{}}, null, 2); editor.setAttribute("aria-describedby", "compare-scope");
  let source = "manual_result"; editor.addEventListener("input", () => {source = "manual_result";}); decision.addEventListener("change", () => {source = "manual_result";});
  append(panel, editorLabel, editor);
  const actions = el("div", null, "buttons");
  actions.append(button("Load reference self-check", () => {decision.value = q.decision; editor.value = JSON.stringify(r ? {status:r.status, rows:r.rows, units:r.units} : null, null, 2); source = "reference_replay";}));
  if (r) actions.append(button("Load synthetic wrong value", () => {const sample = structuredClone({status:r.status, rows:r.rows, units:r.units}); const c = q.columns.find(c => c.kind === "number"); if (c) {const row = sample.rows.find(row => row[c.name] !== null); if (row) row[c.name] = row[c.name] * 2 + 1;} decision.value = "answer"; editor.value = JSON.stringify(sample, null, 2); source = "synthetic_failure";}));
  const output = el("div"); output.setAttribute("aria-live", "polite");
  const submit = button("Compare & save check", async () => {
    submit.disabled = true;
    try { const payload = {question_id:q.id, decision:decision.value, result:decision.value === "answer" ? JSON.parse(editor.value) : null}; const run = await api("/api/evaluate", {submission:payload, source}); state.lastRun = run; showVerdict(output, run); await history(); } catch(e) {error(output,e);} finally {submit.disabled = false;}
  }, "primary");
  const scope = el("p", "Reference self-checks verify the comparison workflow. They are not independent evidence of benchmark accuracy.", "muted"); scope.id = "compare-scope";
  append(panel, actions, scope, submit, el("p"), output);
  if (state.lastRun) showVerdict(output, state.lastRun);
}
function showVerdict(output, run) {
  const card = el("div", null, `verdict ${run.verdict.status}`);
  append(card, el("strong", run.verdict.status.replaceAll("_", " ")), el("p", run.verdict.reason), el("p", `Source: ${run.source.replaceAll("_", " ")} · ${run.verdict.scope}`, "muted"));
  output.replaceChildren(card, append(el("div", null, "buttons"), button("Download check report", () => download(`${run.question_id}-check.json`, run))));
}
function review(panel) {
  const q = state.detail.question;
  append(panel, el("h3", "Leave a scientific review"), el("p", "Check the question's meaning, the table and row grain, its filters, units, and reference interpretation. Describe one concrete correction and cite a source when possible.", "muted"));
  const form = el("form"), categoryLabel = el("label", "What needs attention?", "field-label"), category = el("select"); category.id = "category"; categoryLabel.htmlFor = category.id;
  ["question", "query", "units", "reference", "interface", "other"].forEach(s => {const o = el("option", s); o.value=s; category.append(o);});
  const label = el("label", "Review note (10–2,000 characters)", "field-label"), note = el("textarea", null, "review-note"); note.id = "review-note"; label.htmlFor = note.id; note.minLength=10; note.maxLength=2000; note.required=true;
  const consent = el("label", null, "consent"), check = el("input"); check.type="checkbox"; check.required=true; append(consent, check, el("span", "I agree to retain this note locally for benchmark improvement. I have excluded personal and confidential information."));
  const submit = el("button", "Save review locally"); submit.type="submit"; const output = el("div"); output.setAttribute("aria-live", "polite");
  append(form, categoryLabel, category, label, note, consent, submit, el("p"), output);
  form.addEventListener("submit", async e => { e.preventDefault(); submit.disabled=true; try {const payload={question_id:q.id, category:category.value, note:note.value, consent_to_retain:check.checked}; const saved=await api("/api/feedback",payload); output.replaceChildren(el("p", "Review saved locally. Expert approval status is unchanged.", "badge"), append(el("div", null, "buttons"), button("Download my review", () => download(`${q.id}-review.json`, {...payload, ...saved})))); note.value=""; check.checked=false; } catch(err) {error(output,err);} finally {submit.disabled=false;} }); panel.append(form);
}
async function history() {
  const root = $("#history");
  try {const runs = await api("/api/runs"); root.replaceChildren(); if (!runs.length) {root.append(el("p", "No saved checks yet. Open a question and use Compare to begin.", "muted")); return;} runs.slice(0,8).forEach(run => {const row=el("div",null,"history-row"), description=el("div"); append(description, el("strong", `${run.question_id} · ${run.verdict.status.replaceAll("_", " ")}`), el("span", `${run.source.replaceAll("_", " ")} · ${new Date(run.created_at).toLocaleString()}`)); append(row,description,button("Download",()=>download(`${run.id}.json`,run))); root.append(row);}); if(runs.length>8) root.append(button(`Download ${runs.length} recent checks`,()=>download("recent-checks.json",runs))); } catch(e) {error(root,e);}
}
async function start() {
  try {const data=await api("/api/questions"); state.questions=data.questions; const v=data.verification; [[data.questions.length,"development questions"],[v.answerable,"captured references"],[v.checks.filter(c=>c.passed).length,"capture checks passed"],[0,"paid model calls"]].forEach(([value,label])=>$("#metrics").append(append(el("div",null,"metric"),el("strong",String(value)),el("span",label)))); library(); await select(state.questions[0].id); await history();} catch(e) {$("#global-error").hidden=false; $("#global-error").textContent=`Could not load the workbench: ${e.message}. Restart the local server and reload.`;}
}
$("#search").addEventListener("input",library); $("#difficulty").addEventListener("change",library); $("#refresh-history").addEventListener("click",history); start();

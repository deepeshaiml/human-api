const pptxgen = require('pptxgenjs');
const path = require('path');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Human API · Eureka Innovation Hackathon';
pptx.subject = 'Governed employee knowledge continuity';
pptx.title = 'Human API';
pptx.company = 'Presight Eureka';
pptx.lang = 'en-AE';
pptx.theme = {
  headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'en-AE'
};
pptx.defineSlideMaster({
  title: 'BASE', background: { color: 'F4F6F3' },
  objects: [
    { rect: { x: 0.48, y: 7.13, w: 12.35, h: 0.015, line: { color: 'D7E1DB', transparency: 100 }, fill: { color: 'D7E1DB' } } },
    { text: { text: 'HUMAN API  /  EUREKA INNOVATION HACKATHON', options: { x: 0.52, y: 7.18, w: 6.5, h: 0.16, fontFace: 'Aptos', fontSize: 7.5, color: '71847C', charSpacing: 1.1, margin: 0 } } },
    { text: { text: 'CONCEPT FORMULATED  ·  26 OCT 2026', options: { x: 9.25, y: 7.18, w: 3.55, h: 0.16, fontFace: 'Aptos', fontSize: 7.5, color: '71847C', align: 'right', charSpacing: 0.7, margin: 0 } } }
  ],
  slideNumber: { x: 12.78, y: 7.17, color: '71847C', fontFace: 'Aptos', fontSize: 7 }
});

const C = { forest: '17352F', deep: '112B27', green: '2F8069', mint: 'BFE7D6', pale: 'E8F1EC', paper: 'F4F6F3', white: 'FFFFFF', ink: '24342F', muted: '63756D', line: 'D7E1DB', coral: 'E87C65', peach: 'FFF0E9', blue: '5278B8', lavender: 'EEEAF9', gold: 'D1A04A' };
const W = 13.333, H = 7.5;
const sourceLine = 'Background and research sources are in the speaker notes.';
const screenshot = path.resolve(__dirname, '../deliverables/HumanAPI_App_Screenshot.png');

function slide(bg = C.paper) {
  const s = pptx.addSlide('BASE');
  s.background = { color: bg };
  return s;
}
function text(s, value, x, y, w, h, opts = {}) {
  s.addText(value, { x, y, w, h, margin: 0, breakLine: false, fontFace: opts.fontFace || 'Aptos',
    fontSize: opts.fontSize || 14, color: opts.color || C.ink, bold: opts.bold || false,
    align: opts.align || 'left', valign: opts.valign || 'mid', fit: 'shrink',
    paraSpaceAfterPt: opts.paraSpaceAfterPt || 0, bullet: opts.bullet, transparency: opts.transparency || 0,
    charSpacing: opts.charSpacing, isTextBox: true, ...opts });
}
function rect(s, x, y, w, h, fill, radius = true, line = null) {
  s.addShape(radius ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: fill }, line: line ? { color: line, width: 1 } : { color: fill, transparency: 100 }
  });
}
function line(s, x1, y1, x2, y2, color = C.green, width = 1.6, dash = 'solid', endArrowType = 'triangle') {
  s.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width, dashType: dash, endArrowType } });
}
function title(s, kicker, heading, sub = '') {
  text(s, kicker.toUpperCase(), 0.58, 0.38, 11.9, 0.2, { fontSize: 9, bold: true, color: C.green, charSpacing: 1.5 });
  text(s, heading, 0.58, 0.76, 12.1, 0.53, { fontSize: 27, bold: true, color: C.forest, fontFace: 'Aptos Display' });
  if (sub) text(s, sub, 0.6, 1.36, 12, 0.38, { fontSize: 12.5, color: C.muted });
}
function pill(s, label, x, y, w, color = C.pale, labelColor = C.green) {
  rect(s, x, y, w, 0.32, color, true);
  text(s, label, x + 0.1, y + 0.04, w - 0.2, 0.22, { fontSize: 8.5, bold: true, color: labelColor, align: 'center', charSpacing: 0.3 });
}
function card(s, x, y, w, h, heading, body, accent = C.green, fill = C.white) {
  rect(s, x, y, w, h, fill, true, C.line);
  rect(s, x, y, 0.06, h, accent, false);
  text(s, heading, x + 0.22, y + 0.18, w - 0.42, 0.32, { fontSize: 14, bold: true, color: C.forest });
  text(s, body, x + 0.22, y + 0.59, w - 0.44, h - 0.72, { fontSize: 10.5, color: C.muted, valign: 'top', breakLine: false });
}
function notes(s, value) { s.addNotes(value); }
function source(s, value = sourceLine) { text(s, value, 0.6, 6.91, 11.9, 0.16, { fontSize: 7.3, color: C.muted }); }

// 1 — Opening
{
  const s = pptx.addSlide(); s.background = { color: C.deep };
  s.addShape(pptx.ShapeType.ellipse, { x: 9.2, y: -1.0, w: 5.4, h: 5.4, fill: { color: '1A4039', transparency: 10 }, line: { color: '1A4039', transparency: 100 } });
  s.addShape(pptx.ShapeType.ellipse, { x: 10.3, y: 3.5, w: 3.7, h: 3.7, fill: { color: '245B4E', transparency: 20 }, line: { color: '245B4E', transparency: 100 } });
  pill(s, 'FUTURE OF WORK @ PRESIGHT', 0.75, 0.72, 2.65, '254C42', C.mint);
  text(s, 'Human\nAPI', 0.72, 1.6, 6.7, 1.95, { fontSize: 54, bold: true, color: C.white, fontFace: 'Aptos Display', breakLine: false, valign: 'top' });
  text(s, 'Help answer work questions\nwhen the expert is away', 0.8, 3.76, 7.1, 0.9, { fontSize: 23, color: C.mint, valign: 'top' });
  text(s, 'A cited answer when the evidence is clear. A person when it is not.', 0.8, 5.0, 7.1, 0.66, { fontSize: 15, color: 'D0DED8' });
  text(s, 'EUREKA INNOVATION HACKATHON  ·  EARLY CONCEPT', 0.8, 6.75, 8.5, 0.24, { fontSize: 9, color: '9CB7AC', bold: true, charSpacing: 1.0 });
  text(s, 'LOCAL DEMO · FICTIONAL DATA', 9.4, 6.75, 3.15, 0.24, { fontSize: 8, color: '9CB7AC', bold: true, align: 'right', charSpacing: 0.7 });
  notes(s, `Human API is an early concept for handling a work question when the colleague who knows is unavailable. The colleague chooses what questions may be handled and for how long. The person asking must still be allowed to open every source file. The local demo has fictional people and records, real question and approval flows, and a fixed answer template based on matching words. It does not use a large language model and is not connected to a Microsoft tenant. This is a concept-stage demonstration, not a deployed product.`);
}

// 2 — Problem
{
  const s = slide(); title(s, '01 / The problem', 'Work can stop at the person who knows', 'A question needs context, but the right person or file is hard to find.');
  const steps = [
    ['A decision is needed', 'An engineer needs to understand a service change.'],
    ['The expert is away', 'The person who remembers the reason is unavailable.'],
    ['Files are scattered', 'A decision note or operating guide may hold the answer.'],
    ['Work waits or interrupts', 'Someone waits or interrupts another expert.']
  ];
  const xs = [0.65, 3.82, 6.99, 10.16];
  steps.forEach((d, i) => {
    rect(s, xs[i], 2.45, 2.5, 2.1, i === 3 ? C.peach : C.white, true, C.line);
    text(s, `0${i + 1}`, xs[i] + 0.2, 2.68, 0.55, 0.42, { fontSize: 24, bold: true, color: i === 3 ? C.coral : C.green });
    text(s, d[0], xs[i] + 0.2, 3.26, 2.1, 0.35, { fontSize: 13, bold: true, color: C.forest });
    text(s, d[1], xs[i] + 0.2, 3.72, 2.1, 0.58, { fontSize: 10, color: C.muted, valign: 'top' });
    if (i < 3) line(s, xs[i] + 2.58, 3.5, xs[i + 1] - 0.15, 3.5, C.green, 1.5);
  });
  rect(s, 0.65, 5.08, 12.0, 0.82, C.pale, true);
  text(s, 'A problem to test—not a Presight measurement', 0.95, 5.31, 5.3, 0.28, { fontSize: 13.5, bold: true, color: C.forest });
  text(s, 'Measure time spent searching. Do not count waiting time as saved work.', 6.4, 5.31, 5.9, 0.28, { fontSize: 11, color: C.muted, align: 'right' });
  source(s);
  notes(s, `The issue statement here is a product hypothesis rather than a Presight measurement. We are not presenting an external benchmark or claiming that colleagues' absence causes a particular number of lost hours. The chain is familiar to engineering and operations teams: a decision needs context, the subject expert is unavailable, the source may be distributed across repositories, and work either waits or another person is interrupted. The MVP helps by turning that dependency into a durable request with an explicit deadline, consent and evidence path. During a pilot, measure active time spent searching or reconstructing context. Do not count elapsed wait time as productive savings unless the employee can show the blocked time became useful work.`);
}

// 3 — Scenario
{
  const s = slide(); title(s, '02 / A realistic example', 'Why did the service setting change?', 'Alice asks Bob about a fictional Project Alpha change.');
  rect(s, 0.72, 2.05, 4.15, 3.78, C.white, true, C.line);
  pill(s, 'ASKED BY ALICE', 1.0, 2.35, 1.65, C.lavender, C.blue);
  text(s, 'Why did the timeout change from 90 to 120 seconds? Is 120 seconds still needed?', 1.0, 2.92, 3.48, 1.25, { fontSize: 21, bold: true, color: C.forest, valign: 'top' });
  text(s, 'Directed to Bob · DevOps / project owner\nSynthetic out-of-office status', 1.0, 4.72, 3.4, 0.62, { fontSize: 11, color: C.muted, valign: 'top' });
  line(s, 5.1, 3.86, 6.2, 3.86, C.green, 2);
  rect(s, 6.48, 2.05, 6.05, 3.78, C.pale, true);
  pill(s, 'SOFTWARE ANSWER · PARTIAL', 6.82, 2.35, 2.8, 'D5EDE2', C.green);
  text(s, 'The decision note says the timeout rose because setup sometimes took longer than 90 seconds. The change was approved for release 5.2. The note does not say whether 120 seconds is still needed today.', 6.82, 2.95, 5.25, 1.65, { fontSize: 16.5, color: C.forest, valign: 'top' });
  text(s, 'SOURCE  ADR-024 · written decision · version 1.0', 6.82, 5.03, 5.25, 0.35, { fontSize: 10, bold: true, color: C.green });
  text(s, 'This is not a reply written by Bob.', 6.82, 5.46, 5.25, 0.25, { fontSize: 9.5, color: C.muted });
  source(s);
  notes(s, `This synthetic Project Alpha example is implemented in the local demo. An ADR, or architecture decision record, is a written note explaining a technical decision. ADR-024 says startup setup sometimes took longer than 90 seconds and that the increase to 120 seconds was approved for release 5.2. It does not establish whether the setting is still needed. The answer is therefore partial and includes that limitation. The app's “AI-generated” label means software-produced and distinguishes the fixed-template text from a human reply; no language model generates it. A later operating guide records a different 180-second value, so a question about the current value is sent to a human instead of choosing one.`);
}

// 4 — Impact
{
  const s = slide(); title(s, '03 / Business impact', 'What time might the idea save?', 'A planning example—not a measured Presight figure.');
  const annual = 50000;
  text(s, '50,000', 0.76, 2.05, 2.9, 0.78, { fontSize: 46, bold: true, color: C.forest, fontFace: 'Aptos Display' });
  text(s, 'possible work questions each year', 0.8, 2.87, 3.3, 0.32, { fontSize: 11, color: C.muted });
  text(s, '500 employees × 2 questions/week × 50 weeks', 0.8, 3.36, 3.8, 0.36, { fontSize: 12.5, bold: true, color: C.green });
  card(s, 0.75, 4.0, 3.75, 1.55, 'Count search time', 'Time people actually spend finding and checking the answer.', C.green);
  card(s, 4.78, 4.0, 3.75, 1.55, 'Do not count waiting', 'Time spent waiting is not automatically saved work.', C.coral, C.peach);
  card(s, 8.8, 4.0, 3.75, 1.55, 'Measure real use', 'Count answers people accept and time the pilot can verify.', C.blue);
  pill(s, 'EXAMPLE ASSUMPTIONS · NOT MEASURED BENEFIT', 0.78, 5.91, 3.8, C.lavender, C.blue);
  source(s);
  notes(s, `The question volume is illustrative math: 500 employees multiplied by two knowledge-blocking questions per week and 50 working weeks gives 50,000 annual opportunities. It is not a measured count of Presight questions. An economic model should include only the share that can be safely handled, the share employees actually adopt, the share that resolves successfully, and active minutes that are demonstrably avoided. Waiting time should not be included by default. Also avoid counting a saved expert interruption separately when the same benefit is already part of the active minutes estimate. The business case later shows a base capacity value below illustrative annual operating costs, making measurement and a Microsoft configuration comparison important gates.`);
}

// 5 — Solution
{
  const s = slide(); title(s, '04 / The solution', 'Owner consent does not give file access', 'Two separate checks protect the person asking and the person sharing knowledge.');
  card(s, 0.72, 2.2, 3.8, 2.15, 'The owner agrees', 'Choose the dates, project, topic, coworkers, files and backup. Pause or stop at any time.', C.green);
  card(s, 4.78, 2.2, 3.8, 2.15, 'The asker has access', 'Use only files the signed-in requester is already allowed to open.', C.blue);
  card(s, 8.84, 2.2, 3.8, 2.15, 'Answer or get help', 'Show the source and limits. Deny restricted requests. Ask a human when evidence is weak.', C.coral);
  line(s, 4.55, 3.26, 4.75, 3.26, C.green);
  line(s, 8.61, 3.26, 8.81, 3.26, C.green);
  rect(s, 0.72, 4.9, 11.92, 0.9, C.forest, true);
  text(s, 'Every answer shows', 1.02, 5.19, 3.0, 0.31, { fontSize: 15, bold: true, color: C.white });
  text(s, 'Who wrote it  /  which file supports it  /  what is unknown  /  who can help next', 4.05, 5.21, 8.2, 0.28, { fontSize: 12.5, color: C.mint, align: 'right' });
  source(s);
  notes(s, `Human API treats delegation consent as an explicit policy object: the knowledge owner chooses the active dates, project, topics, approved sources, audience, backup and response window. A manager can approve scoped policy changes. Authorization is a separate gate; an owner cannot make restricted source data available to a requester who lacks permission. The answer can be supported or partial, but source evidence and limitations are visible. When policy disallows access, the response is generic and reveals no hidden title or snippet. When evidence is missing or contradictory, the workflow escalates. The owner retains control and can revoke. Generated language is never attributed to the owner unless the owner actually answered.`);
}

// 6 — Workflow
{
  const s = slide(); title(s, '05 / How it works', 'One question, five clear steps', 'The app records what happened and checks file access before searching.');
  const labels = [
    ['01', 'Save the\nquestion'], ['02', "Check owner's\nlimits"], ['03', "Check asker's\nfile access"], ['04', 'Search\napproved files'], ['05', 'Answer or\nask a person']
  ];
  const x0 = 0.78, gap = 2.47;
  labels.forEach((item, i) => {
    const x = x0 + i * gap;
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.39, y: 2.43, w: 0.72, h: 0.72,
      fill: { color: i === 4 ? C.coral : C.green }, line: { color: C.white, width: 2 } });
    text(s, item[0], x + 0.39, 2.62, 0.72, 0.26, { fontSize: 14, bold: true, color: C.white, align: 'center' });
    text(s, item[1], x + 0.01, 3.34, 1.5, 0.7, { fontSize: 13, bold: true, color: C.forest, align: 'center', valign: 'top' });
    if (i < labels.length - 1) line(s, x + 1.35, 2.8, x + gap + 0.3, 2.8, C.green, 1.5);
  });
  rect(s, 0.85, 4.65, 5.65, 1.05, C.white, true, C.line);
  text(s, 'A source supports the answer', 1.1, 4.88, 3.6, 0.3, { fontSize: 13, bold: true, color: C.forest });
  text(s, 'Show the file, version and known limits', 1.1, 5.27, 4.8, 0.22, { fontSize: 10.5, color: C.green });
  rect(s, 6.78, 4.65, 5.65, 1.05, C.peach, true);
  text(s, 'No proof, restricted or conflicting', 7.03, 4.88, 3.85, 0.3, { fontSize: 13, bold: true, color: C.forest });
  text(s, 'Give a safe denial or ask an approved person', 7.03, 5.27, 4.9, 0.22, { fontSize: 10.5, color: C.coral });
  source(s);
  notes(s, `The workflow uses a deterministic state machine in a modular monolith, not a collection of independent LLM agents. Question creation persists the requester, owner, project, status and response deadline. When the deadline or approved absence condition applies, the policy engine checks consent, dates, topic, project, audience and manager approval. The authorization module filters approved content using the requester's current project membership and source ACL before ranking. The evidence step checks whether relevant support exists and whether sources conflict. A supported response is cited; otherwise the engine denies or escalates. Database-backed jobs survive process restarts. The local scanner is single-process and requires stronger locking, notification outbox and observability before multi-instance deployment.`);
}

// 7 — Delegate policy
{
  const s = slide(); title(s, "06 / Owner's choice", 'What Bob has agreed to', 'The owner can pause or stop the helper at any time.');
  rect(s, 0.75, 2.05, 7.45, 3.75, C.white, true, C.line);
  const config = [
    ['DATES', '20 Oct – 02 Nov'], ['PROJECT', 'Project Alpha'], ['QUESTION TOPICS', 'Deployment · timeout'],
    ['WHO MAY ASK', 'Approved project colleagues'], ['FILES TO CHECK', 'Selected decision notes / guides'], ['BACKUP PERSON', 'Carla Mendez']
  ];
  config.forEach((v, i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 1.05 + col * 3.55, y = 2.38 + row * 1.0;
    text(s, v[0], x, y, 2.85, 0.18, { fontSize: 8, color: C.muted, bold: true, charSpacing: 1.1 });
    text(s, v[1], x, y + 0.27, 3.0, 0.32, { fontSize: 13, bold: true, color: C.forest });
  });
  rect(s, 8.6, 2.05, 3.95, 3.75, C.forest, true);
  pill(s, 'OWNER CONTROL', 8.95, 2.38, 1.65, '254C42', C.mint);
  text(s, 'Pause or stop', 8.95, 3.0, 3.2, 0.42, { fontSize: 20, bold: true, color: C.white });
  text(s, 'A manager reviews changes. Being Busy or away never counts as permission.', 8.95, 3.67, 2.95, 0.9, { fontSize: 12, color: 'D1E1D9', valign: 'top' });
  text(s, 'Every change is recorded.', 8.95, 5.15, 3.15, 0.3, { fontSize: 9.5, bold: true, color: C.mint });
  source(s);
  notes(s, `This is a fictional example of the limits Bob chooses: dates, one project, a short list of question topics, named coworkers, selected files and a backup. Bob can pause or revoke the policy. A manager reviews a scope change. The demo's out-of-office status is fictional and is only used after an owner-approved policy already exists; Busy status is not consent. “Delegation” here means limited permission for the software workflow to help. It never means the software pretends to be Bob or gives Alice access to Bob's files.`);
}

// 8 — Integrations
{
  const s = slide(); title(s, '07 / Possible Microsoft connection', 'Where a Microsoft connection could fit', 'These connections are not part of the tested local demo.');
  card(s, 0.72, 2.18, 2.87, 2.5, 'Work sign-in', 'Check who is signed in with a Microsoft work account. Early code only; needs tenant testing.', C.blue);
  pill(s, 'NOT CONNECTED', 0.95, 4.28, 1.65, C.lavender, C.blue);
  card(s, 3.77, 2.18, 2.87, 2.5, 'SharePoint files', "Search and open files as Alice, using Alice's existing access. Adapter not tenant-tested.", C.green);
  pill(s, 'NOT TENANT TESTED', 4.0, 4.28, 1.9, C.pale, C.green);
  card(s, 6.82, 2.18, 2.87, 2.5, 'Out-of-office status', "Possible future check of the owner's status and dates only. No inbox or message text.", C.gold);
  pill(s, 'EARLY ADAPTER', 7.05, 4.28, 1.72, 'FFF3DB', '956D21');
  card(s, 9.87, 2.18, 2.87, 2.5, 'Teams', 'No bot yet. A future app needs registration, a secure web address and tenant approval.', C.coral);
  pill(s, 'FUTURE WORK', 10.1, 4.28, 1.5, C.peach, C.coral);
  rect(s, 0.75, 5.15, 11.95, 0.62, C.forest, true);
  text(s, "A future file search must use the requester's own Microsoft permissions.", 1.0, 5.34, 11.45, 0.21, { fontSize: 12, bold: true, color: C.white, align: 'center' });
  source(s);
  notes(s, `The local demo uses fictional identities and files; none of these Microsoft connections is active. Microsoft Entra ID is the work sign-in service. Microsoft Graph is the interface applications use to access files and settings. A future “on behalf of” (OBO) sign-in flow should make every SharePoint search as the signed-in requester, not as the knowledge owner. The adapter code exists but has not been tested in a tenant. The Outlook adapter is designed to read only an owner's automatic-reply status and dates, not message text or inbox. A Teams bot is future work and needs an app registration, a publicly reachable secure web address and tenant approval. Sources: Microsoft Graph Search API, Get mailbox settings, Graph permissions reference, and Teams SDK Register App quickstart.`);
}

// 9 — Architecture
{
  const s = slide(); title(s, '08 / Safety', 'The requester keeps control of file access', "The owner's permission never unlocks files for another person.");
  const nodes = [
    ['Who is asking?', 'Work identity · project\nquestion · deadline', 0.75, C.white],
    ["What did owner allow?", 'Dates · topic\npeople · files', 3.2, C.pale],
    ['Can asker open file?', 'Project access\nfile permissions', 5.65, C.white],
    ['Does source answer?', 'Approved file\nmissing · conflict', 8.1, C.pale],
    ['What happens next?', 'Show source\ndeny · ask human', 10.55, C.white]
  ];
  nodes.forEach(([h, b, x, fill]) => {
    rect(s, x, 2.35, 2.05, 1.55, fill, true, C.line);
    text(s, h, x + 0.18, 2.63, 1.7, 0.3, { fontSize: 12.5, bold: true, color: C.forest, align: 'center' });
    text(s, b, x + 0.16, 3.05, 1.73, 0.58, { fontSize: 9.5, color: C.muted, align: 'center', valign: 'top' });
  });
  for (let i = 0; i < 4; i++) line(s, nodes[i][2] + 2.08, 3.12, nodes[i + 1][2] - 0.06, 3.12, C.green, 1.4);
  rect(s, 0.75, 4.55, 5.4, 1.15, C.peach, true);
  text(s, 'If access is denied', 1.03, 4.8, 1.6, 0.28, { fontSize: 13, bold: true, color: C.coral });
  text(s, 'Give no file name, content or clue that it exists.', 2.65, 4.76, 3.15, 0.42, { fontSize: 10.5, color: C.ink });
  rect(s, 6.48, 4.55, 6.12, 1.15, C.forest, true);
  text(s, 'Audit trail', 6.78, 4.8, 1.4, 0.28, { fontSize: 13, bold: true, color: C.mint });
  text(s, "Record the owner's choice, file check, source and result.", 8.35, 4.76, 3.85, 0.42, { fontSize: 10.5, color: C.white });
  text(s, 'Not built for production yet: encrypted storage, deletion controls, real file labels, multi-server safety or independent security review.', 0.82, 6.12, 11.75, 0.38, { fontSize: 10, bold: true, color: C.muted, align: 'center' });
  source(s);
  notes(s, `The order matters: first verify who is asking, then check what the owner approved, then check whether the requester can open a file, and only then search. “ACL” means access control list, or the list of people allowed to open a file. Owner consent allows the workflow to operate; it never grants file access to another person. The app checks access again before showing a saved answer. A denial should not reveal a hidden file name or excerpt. The demo governance page shows counts and audit details, not private question content. Encryption, deletion controls, real file labels, multi-server coordination and independent security review still need to be built before a production pilot.`);
}

// 10 — Working app
{
  const s = slide(); title(s, '09 / Working demo', 'A real local app with fictional data', 'Question records and approval steps work; all people and files are examples.');
  s.addImage({ path: screenshot, x: 0.72, y: 1.9, w: 7.25, h: 5.03, sizingContain: true });
  card(s, 8.35, 2.05, 4.15, 1.05, 'The question is saved', 'See its status, response deadline and history.', C.green);
  card(s, 8.35, 3.34, 4.15, 1.05, 'The answer shows its source', 'The decision note explains the change, not whether it is still needed.', C.blue);
  card(s, 8.35, 4.63, 4.15, 1.05, 'A person handles gaps', 'Unclear answers go to a human; reuse needs approval.', C.coral);
  pill(s, 'FICTIONAL DATA · NO LIVE MICROSOFT OR AI MODEL', 8.35, 6.03, 4.25, C.pale, C.green);
  source(s);
  notes(s, `This screenshot is from the running local app after Alice submitted a Project Alpha question to Bob. The app shows real local question status and evidence, but all people and documents are fictional. The current answer path matches words in approved files and uses fixed text; it does not call an AI language model or Microsoft Graph. A presenter can use this page to show the question, the cited written decision and its limitation. Then ask for restricted budget data to show a safe denial, and ask about an undocumented change to show the human backup route.`);
}

// 11 — Agentic design
{
  const s = slide(); title(s, '10 / AI and human roles', 'AI may explain evidence; people and rules keep control', 'The demo uses no language model. A future AI must never decide who may see a file.');
  const cols = [
    ['SOFTWARE RULES', 'Verify identity\nCheck owner approval\nCheck file access\nHonor revocation', C.pale, C.green],
    ['POSSIBLE FUTURE AI', 'Summarize allowed files\nDraft a cited answer\nSay what is unknown', C.white, C.blue],
    ['PEOPLE DECIDE', 'Resolve uncertainty\nApprove corrections\nChange or stop policy', C.peach, C.coral]
  ];
  cols.forEach((v, i) => {
    const x = 0.82 + i * 4.18;
    rect(s, x, 2.22, 3.65, 3.22, v[2], true, C.line);
    text(s, v[0], x + 0.25, 2.5, 3.1, 0.24, { fontSize: 9, bold: true, color: v[3], charSpacing: 1.2 });
    text(s, v[1], x + 0.25, 2.98, 3.1, 1.85, { fontSize: 15, bold: true, color: C.forest, valign: 'top', breakLine: false, lineSpacingMultiple: 1.2 });
  });
  line(s, 4.53, 3.87, 4.84, 3.87, C.green, 1.6);
  line(s, 8.7, 3.87, 9.0, 3.87, C.green, 1.6);
  text(s, 'The current demo follows a small set of steps. Add more AI only if a pilot shows it helps.', 0.92, 5.88, 11.55, 0.54, { fontSize: 12, color: C.muted, align: 'center' });
  source(s);
  notes(s, `The product uses agentic workflow in the sense of a routed, persistent work item with policy, evidence, feedback and human review. It does not need an LLM for each module. Identity, deadlines, permission decisions, revocation and approval remain deterministic. The current response composer is also deterministic, avoiding hallucinations while we validate the workflow. If a model is added, it should only receive requester-authorized evidence and produce a draft with citations. An objective evidence checker should validate citation IDs and coverage; no model confidence score should authorize disclosure. We did not add LangGraph because the workflow is a small state machine with one human interruption. Reconsider orchestration only when multiple tools/checkpoints show measurable value.`);
}

// 12 — Competition
{
  const s = slide(); title(s, '11 / What already exists', 'Search is common. The workflow is the question.', 'Microsoft and other tools already find files, show sources and respect file permissions.');
  card(s, 0.72, 2.18, 3.8, 2.35, 'Tools already do', 'Search company files, summarize them, show sources and follow file permissions.', C.blue);
  card(s, 4.78, 2.18, 3.8, 2.35, 'Workflow to test', 'Owner opts in. A response time is set. The requester keeps existing file access. A person handles gaps.', C.green);
  card(s, 8.84, 2.18, 3.8, 2.35, 'Open question', 'Do teams need this extra handoff, or can they configure Copilot or another tool?', C.coral, C.peach);
  text(s, 'No public review proves this exact workflow is unique.', 0.82, 5.24, 11.65, 0.38, { fontSize: 16, bold: true, color: C.forest, align: 'center' });
  source(s, 'Sources: Microsoft Autopilot (25 Sep), SharePoint team knowledge base (14 Oct), Glean and Moveworks.');
  notes(s, `The comparison is deliberately cautious. Microsoft 365 Copilot and SharePoint agents already ground on Microsoft sources and respect existing document permissions. Copilot Studio can build workflows and has a human assistance node. On 25 September 2026 Microsoft announced Autopilot, formerly Scout, as a persistent, proactive personal agent with tenant identity, governance and Microsoft IQ context; the announcement described private preview expansion at month end, not general availability. On 14 October Microsoft announced a SharePoint team knowledge base curated by Copilot and agents in Frontier Preview; Copilot in SharePoint began its general availability rollout on 30 September. Glean documents permission-filtered cross-app search, citations, people context and agents. Moveworks documents search, sources, action plugins and Smart Handoff. The exact combination of owner-specific consent, unanswered-question deadline and approved correction lifecycle was not proven in the public sources reviewed. That is a hypothesis, not a uniqueness claim. Vendor features and preview availability should be rechecked during a proof of concept. Sources: https://blogs.microsoft.com/blog/2026/09/25/introducing-the-new-copilot-with-home-code-and-autopilot/ ; https://techcommunity.microsoft.com/blog/spblog/introducing-a-team-knowledge-base-curated-by-copilot-and-agents/4564203 ; https://techcommunity.microsoft.com/blog/spblog/what%E2%80%99s-new-in-copilot-in-sharepoint-october-2026/4535423 ; https://docs.glean.com/user-guide/about/what-is-glean ; https://help.moveworks.com/ai-assistant/capabilities`);
}

// 13 — ROI
{
  const s = slide(); title(s, '12 / Example economics', 'Time value is not the same as cash saved', 'Compare estimated recovered work time with costs in AED (UAE dirhams).');
  const values = [125, 700, 1611]; const labels = ['LOW', 'BASE', 'HIGH']; const colorsSet = [C.blue, C.green, C.mint];
  const chartX = 1.05, chartY = 2.1, chartH = 3.45, baseY = chartY + chartH, scale = chartH / 1800;
  line(s, chartX, baseY, 8.5, baseY, C.muted, 0.8, 'solid', 'none');
  values.forEach((v, i) => {
    const x = 1.55 + i * 2.22, h = v * scale;
    rect(s, x, baseY - h, 1.15, h, colorsSet[i], true);
    text(s, `AED ${v.toLocaleString()}k`, x - 0.25, baseY - h - 0.42, 1.65, 0.28, { fontSize: 11.5, bold: true, color: C.forest, align: 'center' });
    text(s, labels[i], x - 0.05, baseY + 0.18, 1.25, 0.23, { fontSize: 9, bold: true, color: C.muted, align: 'center', charSpacing: 1.2 });
  });
  const costY = baseY - 740 * scale;
  line(s, 1.0, costY, 8.45, costY, C.coral, 2, 'dash', 'none');
  text(s, 'Example annual operating cost: AED 740k', 5.4, costY - 0.33, 3.05, 0.22, { fontSize: 8.7, bold: true, color: C.coral, align: 'right' });
  rect(s, 9.08, 2.18, 3.43, 3.45, C.white, true, C.line);
  text(s, 'BASE EXAMPLE · VALUE OF TIME', 9.38, 2.52, 2.8, 0.23, { fontSize: 8.4, bold: true, color: C.green, charSpacing: 0.8 });
  text(s, 'AED 700k', 9.38, 2.97, 2.8, 0.62, { fontSize: 32, bold: true, color: C.forest, fontFace: 'Aptos Display' });
  text(s, '8,400 answers people accept\n× 20 minutes of search saved\n× AED 250 per work hour', 9.38, 3.85, 2.65, 0.9, { fontSize: 11, color: C.muted, valign: 'top' });
  text(s, 'Time value is AED 40k below example cost', 9.38, 5.06, 2.75, 0.42, { fontSize: 9.8, bold: true, color: C.coral });
  text(s, 'Assumptions only. No work time or financial benefit has been measured.', 0.82, 6.19, 11.8, 0.25, { fontSize: 10.2, bold: true, color: C.muted, align: 'center' });
  source(s);
  notes(s, `This is an example of possible employee work time made available, not a cash-savings claim. The base assumptions are 50,000 possible questions a year; 40% are suitable for the workflow, 60% of those are used, and 70% get an answer the requester accepts. That gives 8,400 accepted answers. At 20 active minutes saved each and an assumed AED 250 per work hour, the time is valued at AED 700,000. The example annual operating cost is AED 740,000 before Microsoft licensing, so the base estimate is AED 40,000 below cost. The cost assumes partial engineering and support roles plus infrastructure, security review and adoption. A pilot must measure actual active time, acceptance and cost. Waiting time is excluded.`);
}

// 14 — Feasibility and roadmap
{
  const s = slide(); title(s, '13 / Next steps', 'A path from demo to a safe pilot', 'First review security and file access. Then connect Microsoft. Then measure value.');
  const phases = [
    ['NOW', 'Local demo', 'Fictional people and files\nRules and file-access checks\nAnswer or human handoff', 'Working', C.green],
    ['STEP 1', 'Safety review', 'Review file labels\nCheck owner permission\nAgree on data handling', 'Needs review', C.blue],
    ['STEP 2', 'Connect Microsoft', 'Work sign-in\nRequester file access\nTeams app', 'Needs tenant setup', C.gold],
    ['STEP 3', 'Small pilot', 'One opt-in team\nLow-risk files\nMeasure time and trust', '6–10 weeks', C.coral]
  ];
  phases.forEach((p, i) => {
    const x = 0.72 + i * 3.13;
    rect(s, x, 2.16, 2.78, 3.2, C.white, true, C.line);
    pill(s, p[0], x + 0.23, 2.42, 1.0, i === 0 ? C.pale : C.lavender, i === 0 ? C.green : C.blue);
    text(s, p[1], x + 0.23, 2.97, 2.25, 0.36, { fontSize: 17, bold: true, color: C.forest });
    text(s, p[2], x + 0.23, 3.5, 2.23, 1.15, { fontSize: 11.5, color: C.muted, valign: 'top' });
    text(s, p[3], x + 0.23, 4.93, 2.28, 0.22, { fontSize: 9.5, bold: true, color: p[4] });
    if (i < phases.length - 1) line(s, x + 2.82, 3.72, x + 3.08, 3.72, C.green, 1.4);
  });
  text(s, 'No live Microsoft connection has been tested. The demo uses no language model and is not security-certified.', 0.82, 5.88, 11.75, 0.4, { fontSize: 11, bold: true, color: C.coral, align: 'center' });
  source(s);
  notes(s, `The local demo is working with fictional data. Before using real Microsoft files, a security and privacy review must decide what data can be processed, how long it is kept, and how access is removed. The Microsoft proof must test that work sign-in and every file search preserve the requester's own permissions. A future Teams app needs registration, tenant approval and a secure web endpoint. Only then should one opt-in team try low-risk files with a human fallback. Measure active search time, answer acceptance and trust. No live Microsoft connection has been exercised; no language model is bundled; this prototype is not security-certified.`);
}

// 15 — Recommendation
{
  const s = pptx.addSlide(); s.background = { color: C.deep };
  pill(s, 'PILOT PROPOSAL', 0.8, 0.72, 1.65, '254C42', C.mint);
  text(s, 'Test the workflow\nwith one willing team.', 0.8, 1.42, 8.9, 1.35, { fontSize: 34, bold: true, color: C.white, fontFace: 'Aptos Display', valign: 'top' });
  const items = [
    ['01', 'One willing team', 'Use existing, low-risk files'],
    ['02', '6–10 weeks', 'Review security and connect Microsoft'],
    ['03', 'Safety first', 'Stop if anyone sees a file they should not'],
    ['04', 'Measure value', 'Search time saved, accepted answers, cost']
  ];
  items.forEach((d, i) => {
    const y = 3.35 + i * 0.7;
    text(s, d[0], 0.92, y, 0.52, 0.25, { fontSize: 12, bold: true, color: C.mint });
    text(s, d[1], 1.62, y, 2.85, 0.28, { fontSize: 14, bold: true, color: C.white });
    text(s, d[2], 4.5, y, 4.5, 0.28, { fontSize: 11, color: 'BDD0C7' });
  });
  rect(s, 9.45, 3.45, 3.0, 1.85, '254C42', true);
  text(s, 'The ask', 9.78, 3.78, 2.2, 0.3, { fontSize: 12, bold: true, color: C.mint, charSpacing: 1 });
  text(s, 'Sponsor a security review, Microsoft setup and one pilot manager.', 9.78, 4.27, 2.25, 0.75, { fontSize: 12, color: C.white, valign: 'top' });
  text(s, 'Human API  ·  Evidence, boundaries, and a human path when the answer is not there.', 0.82, 6.75, 8.7, 0.3, { fontSize: 10, color: '9CB7AC' });
  notes(s, `The ask is to test, not to fund a full product. Sponsor a security and privacy review, Microsoft tenant setup, and one manager-led pilot with a willing team. Use low-risk files and a human fallback. Stop immediately if anyone receives information they are not allowed to see. Measure active time spent searching, whether answers are accepted, how often questions go to a person, and the full cost including Microsoft licensing. Compare with what the organization can already configure in Microsoft tools. The goal is a clear decision based on evidence, not a claim that a benefit has already been achieved.`);
}

pptx.writeFile({ fileName: path.resolve(__dirname, '../deliverables/HumanAPI_Pitch_Deck.pptx') })
  .then(() => console.log('Wrote HumanAPI_Pitch_Deck.pptx'))
  .catch(error => { console.error(error); process.exitCode = 1; });

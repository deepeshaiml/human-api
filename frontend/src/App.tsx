import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowDownRight, ArrowUpRight, BookOpen, Check, CheckCheck,
  ChevronDown, CircleHelp, Clock3, FileText, Fingerprint, Inbox, KeyRound,
  LayoutDashboard, LockKeyhole, MessageCircleQuestion, RefreshCw, Send, Shield,
  ShieldCheck, Sparkles, UserRound, Users, WandSparkles,
} from 'lucide-react'

type Person = { id: string; name: string; role: string; availability?: string; availability_is_simulated?: boolean }
type Project = { id: string; name: string }
type Evidence = { document_id: string; title: string; version: string; passage: string; updated_at: string }
type Question = {
  id: string; question: string; status: string; topic: string; urgency: string;
  requester?: Person; owner?: Person; project?: Project; created_at: string; response_deadline: string;
  answer?: string | null; answer_type?: string | null; answer_origin?: string | null;
  validation?: { outcome: string; reasons: string[] } | null; evidence: Evidence[];
  human_answer?: string | null; knowledge_entry?: { id: string; status: string } | null;
  feedback: { rating: string; note?: string | null }[]
}
type Dashboard = { scope: string; metrics: Record<string, number>; recent_questions: Question[]; pending_notifications: number; delegation_enabled: boolean | null; simulated_presence?: string }
type Delegation = { owner_id: string; enabled: boolean; starts_at: string | null; ends_at: string | null; timeout_minutes: number; project_ids: string[]; topics: string[]; audience_ids: string[]; source_ids: string[]; backup_id: string | null; version: number; manager_approved: boolean; currently_active: boolean }
type Options = { projects: Project[]; audiences: Person[]; backups: Person[]; sources: { id: string; name: string; project_id: string }[] }
type Escalation = { id: string; question_id: string; reason: string; status: string; assignee_id: string; question: Question }
type PendingEntry = { id: string; question_id: string; project_id: string; project_name: string; content: string; created_by: string; created_at: string }
type PendingPolicy = { owner_id: string; owner_name: string; version: number; project_count: number; source_count: number; audience_count: number; timeout_minutes: number }
type Governance = { counts: Record<string, number>; delegations: { owner_id: string; enabled: boolean; version: number; project_count: number; source_count: number; manager_approved: boolean }[]; audit_events: { action: string; resource_type: string; resource_id: string; actor_id: string | null; at: string }[]; note: string }
type Page = 'home' | 'ask' | 'delegate' | 'inbox' | 'governance'

const scenarios = [
  { label: 'Why did the timeout change?', question: 'Why was the Project Alpha startup timeout increased to 120 seconds, and is it still required?', project: 'alpha', owner: 'bob' },
  { label: 'Ask for a confidential budget', question: 'What is the confidential budget for Project Alpha?', project: 'alpha', owner: 'bob' },
  { label: 'Ask about an undocumented decision', question: 'Why was the undocumented blue deployment approval skipped?', project: 'alpha', owner: 'bob' },
  { label: 'Check conflicting values', question: 'What is the current Project Alpha startup timeout value?', project: 'alpha', owner: 'bob' },
]

const nav = [
  { id: 'home' as const, label: 'Overview', icon: LayoutDashboard },
  { id: 'ask' as const, label: 'Ask a question', icon: MessageCircleQuestion },
  { id: 'delegate' as const, label: 'My AI delegate', icon: WandSparkles },
  { id: 'inbox' as const, label: 'Escalation inbox', icon: Inbox },
  { id: 'governance' as const, label: 'Governance', icon: Shield },
]

async function api<T>(path: string, actor: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('X-Demo-User', actor)
  if (init.body) headers.set('Content-Type', 'application/json')
  const response = await fetch(path, { ...init, headers })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body as T
}

function prettyStatus(value: string) {
  return value.toLowerCase().replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function timeAgo(value: string) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60000))
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  return `${Math.round(hours / 24)} days ago`
}

function initials(name = '') { return name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() }

export default function App() {
  const [actor, setActor] = useState('alice')
  const [page, setPage] = useState<Page>('home')
  const [people, setPeople] = useState<Person[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [escalations, setEscalations] = useState<Escalation[]>([])
  const [pendingEntries, setPendingEntries] = useState<PendingEntry[]>([])
  const [pendingPolicies, setPendingPolicies] = useState<PendingPolicy[]>([])
  const [governance, setGovernance] = useState<Governance | null>(null)
  const [delegation, setDelegation] = useState<Delegation | null>(null)
  const [delegateOptions, setDelegateOptions] = useState<Options | null>(null)
  const [selected, setSelected] = useState<Question | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const currentPerson = useMemo(() => people.find((person) => person.id === actor), [people, actor])

  const refresh = useCallback(async (identity = actor) => {
    setLoading(true); setError('')
    try {
      const [reference, data, list, escalationsData, pending] = await Promise.all([
        api<{ projects: Project[]; employees: Person[] }>('/api/reference', identity),
        api<Dashboard>('/api/dashboard', identity),
        api<Question[]>('/api/questions', identity),
        api<Escalation[]>('/api/escalations', identity),
        api<PendingEntry[]>('/api/knowledge/pending', identity),
      ])
      setProjects(reference.projects); setPeople(reference.employees); setDashboard(data)
      setQuestions(list); setEscalations(escalationsData); setPendingEntries(pending)
      setPendingPolicies(await api<PendingPolicy[]>('/api/delegation/pending', identity).catch(() => []))
      const person = reference.employees.find((item) => item.id === identity)
      if (person?.role === 'Security Administrator') {
        setGovernance(await api<Governance>('/api/governance', identity))
      } else setGovernance(null)
      const policy = await api<Delegation>('/api/delegation', identity).catch(() => null)
      setDelegation(policy)
      if (policy) setDelegateOptions(await api<Options>('/api/delegation/options', identity))
      else setDelegateOptions(null)
      if (selected) {
        const next = list.find((item) => item.id === selected.id)
        if (next) setSelected(next)
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load Human API.')
    } finally { setLoading(false) }
  }, [actor, selected])

  useEffect(() => { void refresh(actor) }, [actor])
  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 2800)
    return () => window.clearTimeout(timer)
  }, [toast])

  function changedActor(value: string) {
    setActor(value); setSelected(null); setPage('home'); setDelegation(null)
  }

  async function showQuestion(question: Question) {
    const detail = await api<Question>(`/api/questions/${question.id}`, actor)
    setSelected(detail); setPage('ask')
  }

  async function saveFeedback(question: Question, rating: 'useful' | 'incorrect') {
    try {
      await api(`/api/questions/${question.id}/feedback`, actor, { method: 'POST', body: JSON.stringify({ rating }) })
      setToast('Feedback saved for the review record.')
      await refresh()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Feedback could not be saved.') }
  }

  const activeNav = page === 'governance' && currentPerson?.role !== 'Security Administrator' ? 'home' : page

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand-lockup"><div className="brand-mark"><Activity size={20} strokeWidth={2.4} /></div><div><div className="brand-name">human<span>api</span></div><div className="brand-sub">KNOWLEDGE CONTINUITY</div></div></div>
      <div className="workspace-label">WORKSPACE <ChevronDown size={13} /></div>
      <div className="workspace-card"><div className="workspace-monogram">P</div><div><b>Presight Eureka</b><small>Innovation workspace</small></div><span className="workspace-dot" /></div>
      <div className="nav-caption">YOUR WORK</div>
      <nav aria-label="Main navigation">
        {nav.filter((item) => item.id !== 'governance' || currentPerson?.role === 'Security Administrator')
          .map((item) => <button key={item.id} className={`nav-link ${activeNav === item.id ? 'active' : ''}`} onClick={() => { setPage(item.id); setSelected(null) }}>
            <item.icon size={18} strokeWidth={1.9} /><span>{item.label}</span>
            {item.id === 'inbox' && escalations.filter((entry) => entry.status === 'OPEN').length > 0 && <span className="nav-count">{escalations.filter((entry) => entry.status === 'OPEN').length}</span>}
          </button>)}
      </nav>
      <div className="sidebar-spacer" />
      <div className="privacy-card"><div className="privacy-icon"><ShieldCheck size={15} /></div><div><b>Permission-aware by design</b><span>Access is checked before retrieval.</span></div></div>
      <div className="sidebar-footer"><span className="demo-dot" /> Synthetic demo · local data</div>
    </aside>

    <main className="main-area">
      <header className="topbar">
        <div className="breadcrumb"><span>Presight Eureka</span><span className="crumb-sep">/</span><b>{nav.find((item) => item.id === activeNav)?.label ?? 'Overview'}</b></div>
        <div className="topbar-actions">
          <span className="demo-badge"><span /> DEMO ENVIRONMENT</span>
          <button className="icon-button" title="Refresh data" onClick={() => void refresh()}><RefreshCw size={16} /></button>
          <div className="topbar-divider" />
          <label className="identity-switch"><span className="avatar avatar-small">{initials(currentPerson?.name)}</span><select aria-label="Switch demo identity" value={actor} onChange={(event) => changedActor(event.target.value)}>{people.map((person) => <option key={person.id} value={person.id}>{person.name} · {person.role}</option>)}</select><ChevronDown size={14} /></label>
        </div>
      </header>
      <div className="page-wrap">
        {error && <div className="alert alert-error" role="alert"><CircleHelp size={17} /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss">×</button></div>}
        {loading && !dashboard ? <div className="loading"><span className="spinner" /> Loading your workspace…</div> : <>
          {page === 'home' && <HomePage actor={currentPerson} dashboard={dashboard} questions={questions} onAsk={() => { setPage('ask'); setSelected(null) }} onOpen={showQuestion} onNavigate={(next) => setPage(next === 'governance' && currentPerson?.role !== 'Security Administrator' ? 'delegate' : next)} />}
          {page === 'ask' && <AskPage actor={actor} people={people} projects={projects} selected={selected} onSubmitted={async (question) => { setSelected(question); setToast('Your question is now in the Human API workflow.'); await refresh() }} onFeedback={saveFeedback} onAnswer={async (question, answer) => { await api(`/api/questions/${question.id}/answer`, actor, { method: 'POST', body: JSON.stringify({ answer }) }); setToast('Human response saved. Knowledge publication is pending review.'); await refresh() }} />}
          {page === 'delegate' && <DelegatePage actor={actor} person={currentPerson} policy={delegation} options={delegateOptions} onSaved={async () => { setToast('Delegation policy saved.'); await refresh() }} />}
          {page === 'inbox' && <InboxPage actor={actor} escalations={escalations} pending={pendingEntries} pendingPolicies={pendingPolicies} people={people} onOpen={showQuestion} onAnswer={async (question, answer) => { await api(`/api/questions/${question.id}/answer`, actor, { method: 'POST', body: JSON.stringify({ answer }) }); setToast('Expert response recorded.'); await refresh() }} onApprove={async (entry) => { await api(`/api/knowledge/${entry.id}/approve`, actor, { method: 'POST' }); setToast('Correction approved for the project knowledge scope.'); await refresh() }} onApprovePolicy={async (policy) => { await api(`/api/delegation/${policy.owner_id}/approve`, actor, { method: 'POST' }); setToast('Delegation policy approved for the configured scope.'); await refresh() }} />}
          {page === 'governance' && currentPerson?.role === 'Security Administrator' && <GovernancePage actor={actor} data={governance} people={people} projects={projects} onRevoked={async () => { setToast('Project membership revoked; active answer caches were invalidated.'); await refresh() }} />}
        </>}
      </div>
      <footer className="page-footer"><span>Human API · Internal innovation prototype</span><span><LockKeyhole size={12} /> Demo identities and documents are synthetic</span></footer>
    </main>
    {toast && <div className="toast" role="status"><Check size={17} />{toast}</div>}
  </div>
}

function HomePage({ actor, dashboard, questions, onAsk, onOpen, onNavigate }: { actor?: Person; dashboard: Dashboard | null; questions: Question[]; onAsk: () => void; onOpen: (q: Question) => void; onNavigate: (p: Page) => void }) {
  const counts = dashboard?.metrics ?? {}
  const resolved = (counts.AI_ANSWERED ?? 0) + (counts.RESOLVED ?? 0)
  const pending = (counts.WAITING_FOR_HUMAN ?? 0) + (counts.HUMAN_REVIEW_REQUIRED ?? 0)
  const openEscalations = (counts.HUMAN_REVIEW_REQUIRED ?? 0)
  return <>
    <section className="hero-row">
      <div><div className="eyebrow"><span className="eyebrow-line" /> A BETTER WAY TO KEEP WORK MOVING</div><h1>Good morning, {actor?.name.split(' ')[0] ?? 'there'}<span className="heading-dot">.</span></h1><p className="page-intro">Keep project knowledge moving, even when the person who knows is away.</p></div>
      <button className="primary-button" onClick={onAsk}><MessageCircleQuestion size={17} /> Ask a question <span className="button-arrow">↗</span></button>
    </section>
    <div className="signal-banner"><div className="signal-icon"><ShieldCheck size={18} /></div><div><b>Every answer follows the same trust path</b><span>Owner consent · your access · cited evidence · human review when needed</span></div><span className="signal-status"><i /> ALL SYSTEMS SIMULATED</span></div>
    <section className="metrics-grid" aria-label="Your activity">
      <MetricCard label="Questions you've sent" value={questions.filter((q) => q.requester?.id === actor?.id).length} note="Your direct requests" icon={MessageCircleQuestion} tone="blue" />
      <MetricCard label="AI answers" value={resolved} note="Answers and human resolutions" icon={Sparkles} tone="green" />
      <MetricCard label="Needs a person" value={openEscalations} note="Escalations requiring review" icon={Users} tone="amber" />
      <MetricCard label="Waiting on a reply" value={pending} note="Inside the configured response window" icon={Clock3} tone="violet" />
    </section>
    <div className="content-columns">
      <section className="panel activity-panel">
        <div className="panel-heading"><div><div className="section-kicker">YOUR ACTIVITY</div><h2>Recent questions</h2></div><button className="text-button" onClick={onAsk}>New question <ArrowUpRight size={15} /></button></div>
        {questions.length === 0 ? <EmptyState icon={Inbox} title="Nothing is waiting on you" text="Questions you ask or receive will appear here." action="Ask your first question" onClick={onAsk} /> : <div className="question-list">
          {questions.slice(0, 5).map((question) => <button key={question.id} className="question-row" onClick={() => onOpen(question)}>
            <div className={`question-mark ${question.status === 'AI_ANSWERED' ? 'mark-green' : question.status === 'HUMAN_REVIEW_REQUIRED' ? 'mark-amber' : 'mark-blue'}`}>{question.status === 'AI_ANSWERED' ? <Sparkles size={16} /> : question.status === 'HUMAN_REVIEW_REQUIRED' ? <Users size={16} /> : <MessageCircleQuestion size={16} />}</div>
            <div className="question-row-main"><b>{question.question}</b><span>{question.project?.name} <span className="dot-sep">·</span> {question.requester?.id === actor?.id ? `Asked of ${question.owner?.name}` : `Asked by ${question.requester?.name}`}</span></div>
            <div className="question-row-meta"><StatusBadge value={question.status} /><small>{timeAgo(question.created_at)}</small></div>
          </button>)}
        </div>}
      </section>
      <aside className="right-rail">
        <section className="panel delegate-card">
          <div className="panel-heading"><div><div className="section-kicker">YOUR PRESENCE</div><h2>Knowledge delegate</h2></div><span className="small-sim-tag">SIMULATED</span></div>
          <div className="delegate-person"><div className="avatar avatar-large">{initials(actor?.name)}</div><div><b>{actor?.name}</b><span>{actor?.role} · {actor?.availability === 'out_of_office' ? 'Out of office' : 'Available'}</span></div><span className={`presence-dot ${actor?.availability === 'out_of_office' ? 'away' : ''}`} /></div>
          <div className="delegate-state"><div className={`state-symbol ${dashboard?.delegation_enabled ? 'state-on' : ''}`}>{dashboard?.delegation_enabled ? <Check size={15} /> : <Clock3 size={15} />}</div><div><b>{dashboard?.delegation_enabled ? 'Delegation is enabled' : 'No delegation policy enabled'}</b><span>{dashboard?.delegation_enabled ? 'Your approved scope is active.' : 'Questions wait for your configured response window.'}</span></div></div>
          <button className="secondary-button full-width" onClick={() => onNavigate('delegate')}>Review delegate settings <ArrowDownRight size={15} /></button>
        </section>
        <section className="panel guide-card"><div className="guide-icon"><Fingerprint size={20} /></div><div className="section-kicker">BUILT FOR TRUST</div><h3>AI can help. You stay in control.</h3><p>Human API never speaks as another employee. Every answer shows its source, limits, and review path.</p><button className="link-button" onClick={() => onNavigate(actor?.role === 'Security Administrator' ? 'governance' : 'delegate')}>{actor?.role === 'Security Administrator' ? 'See how decisions are logged' : 'Review your delegation controls'} <ArrowUpRight size={14} /></button></section>
      </aside>
    </div>
  </>
}

function MetricCard({ label, value, note, icon: Icon, tone }: { label: string; value: number; note: string; icon: typeof Activity; tone: string }) {
  return <article className="metric-card"><div className={`metric-icon tone-${tone}`}><Icon size={17} /></div><div className="metric-number">{value}</div><div className="metric-label">{label}</div><div className="metric-note">{note}</div></article>
}

function AskPage({ actor, people, projects, selected, onSubmitted, onFeedback, onAnswer }: { actor: string; people: Person[]; projects: Project[]; selected: Question | null; onSubmitted: (q: Question) => void; onFeedback: (q: Question, rating: 'useful' | 'incorrect') => void; onAnswer: (q: Question, answer: string) => Promise<void> }) {
  const [question, setQuestion] = useState('')
  const [projectId, setProjectId] = useState('alpha')
  const [ownerId, setOwnerId] = useState('bob')
  const [urgency, setUrgency] = useState('normal')
  const [sending, setSending] = useState(false)
  const [humanText, setHumanText] = useState('')
  const [localError, setLocalError] = useState('')
  const canAnswer = selected && (actor === selected.owner?.id || actor === 'carla') && selected.status !== 'RESOLVED' && selected.status !== 'ACCESS_DENIED'

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setSending(true); setLocalError('')
    try {
      const result = await api<Question>('/api/questions', actor, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ owner_id: ownerId, project_id: projectId, question, urgency }) })
      onSubmitted(result); setQuestion('')
    } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Question could not be submitted.') }
    finally { setSending(false) }
  }

  async function sendHumanAnswer(event: React.FormEvent) {
    event.preventDefault()
    if (!selected || !humanText.trim()) return
    try { await onAnswer(selected, humanText); setHumanText('') }
    catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Could not save the human answer.') }
  }

  return <>
    <section className="page-heading"><div className="eyebrow"><span className="eyebrow-line" /> ASK WITH CONTEXT</div><h1>What are you blocked on?</h1><p className="page-intro">Route a question to the person who knows. Human API checks their delegation policy and your access before it looks for evidence.</p></section>
    <div className="ask-layout">
      <section className="panel ask-composer">
        <div className="composer-title"><div className="composer-icon"><MessageCircleQuestion size={19} /></div><div><h2>New project question</h2><p>The owner sees that a question was directed to them.</p></div></div>
        {localError && <div className="alert alert-error compact"><CircleHelp size={15} />{localError}</div>}
        <form onSubmit={submit}>
          <label className="field-label" htmlFor="ask-text">Your question</label><textarea id="ask-text" rows={5} minLength={10} maxLength={3000} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What project context do you need to keep moving?" required />
          <div className="textarea-foot"><span>Be specific about the decision, system, or time period.</span><span>{question.length}/3000</span></div>
          <div className="form-two"><div><label className="field-label" htmlFor="ask-project">Project</label><select id="ask-project" value={projectId} onChange={(event) => setProjectId(event.target.value)}>{projects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div><div><label className="field-label" htmlFor="ask-owner">Ask a knowledge owner</label><select id="ask-owner" value={ownerId} onChange={(event) => setOwnerId(event.target.value)}>{people.filter((person) => person.id !== actor).map((person) => <option key={person.id} value={person.id}>{person.name} · {person.role}</option>)}</select></div></div>
          <div className="form-two form-last"><div><label className="field-label" htmlFor="ask-urgency">Urgency</label><select id="ask-urgency" value={urgency} onChange={(event) => setUrgency(event.target.value)}><option value="normal">Normal · standard response window</option><option value="high">High · blocking a release</option><option value="low">Low · when available</option></select></div><div className="consent-hint"><ShieldCheck size={16} /><span>Delegation only runs when the owner has enabled it for you and this project.</span></div></div>
          <button className="primary-button submit-button" type="submit" disabled={sending || question.trim().length < 10}>{sending ? <><span className="spinner spinner-light" /> Sending…</> : <><Send size={16} /> Submit question</>}</button>
        </form>
        <div className="demo-scenarios"><div className="section-kicker">TRY A DEMO SCENARIO</div><div className="scenario-buttons">{scenarios.map((item) => <button key={item.label} onClick={() => { setQuestion(item.question); setProjectId(item.project); setOwnerId(item.owner) }}>{item.label}</button>)}</div></div>
      </section>
      <aside className="answer-column">
        {selected ? <QuestionDetail question={selected} actor={actor} onFeedback={onFeedback} /> : <div className="panel empty-answer"><div className="empty-answer-icon"><BookOpen size={21} /></div><div className="section-kicker">YOUR ANSWER SPACE</div><h3>Evidence belongs next to the answer.</h3><p>After you submit, Human API shows the current status, authorized sources, document dates, and any limits on the answer.</p><div className="evidence-mini"><div><span className="mini-check"><Check size={12} /></span><span>Requester access checked first</span></div><div><span className="mini-check"><Check size={12} /></span><span>Owner consent checked separately</span></div><div><span className="mini-check"><Check size={12} /></span><span>Unsupported claims are escalated</span></div></div></div>}
        {canAnswer && selected && <div className="panel human-reply-panel"><div className="section-kicker">HUMAN RESPONSE</div><h3>Share a verified correction</h3><p>The response is visible to the requester. It remains pending knowledge publication approval.</p><form onSubmit={sendHumanAnswer}><textarea rows={3} value={humanText} onChange={(event) => setHumanText(event.target.value)} placeholder="Add the verified project answer…" required minLength={5} /><button className="secondary-button full-width" type="submit"><Send size={15} /> Send expert response</button></form></div>}
      </aside>
    </div>
  </>
}

function QuestionDetail({ question, actor, onFeedback }: { question: Question; actor: string; onFeedback: (q: Question, rating: 'useful' | 'incorrect') => void }) {
  return <section className="panel answer-card">
    <div className="answer-card-head"><div><div className="section-kicker">QUESTION STATUS</div><div className="answer-statusline"><StatusBadge value={question.status} /><span className="answer-time">{timeAgo(question.created_at)}</span></div></div><span className="ticket-id">#{question.id.slice(0, 8).toUpperCase()}</span></div>
    <h2 className="submitted-question">{question.question}</h2><div className="question-context"><span>{question.project?.name}</span><span className="dot-sep">·</span><span>To {question.owner?.name}</span><span className="dot-sep">·</span><span>{question.urgency} priority</span></div>
    {question.answer && <div className={`answer-result ${question.answer_type === 'ACCESS_DENIED' ? 'answer-denied' : question.answer_type === 'REQUIRES_CLARIFICATION' ? 'answer-needs-human' : ''}`}>
      <div className="answer-result-top"><div className="answer-result-icon">{question.answer_type === 'ACCESS_DENIED' ? <LockKeyhole size={16} /> : question.answer_type === 'REQUIRES_CLARIFICATION' || question.answer_type === 'SUPERSEDED' ? <Users size={16} /> : <Sparkles size={16} />}</div><div><b>{question.answer_type === 'ACCESS_DENIED' ? 'Access decision' : question.answer_type === 'SUPERSEDED' ? 'Human response replaced the AI result' : question.answer_type === 'REQUIRES_CLARIFICATION' ? 'Human clarification needed' : 'AI-generated answer'}</b><span>{question.answer_origin}</span></div></div>
      <p>{question.answer}</p>
      {question.validation?.reasons?.length ? <div className="answer-caveat"><CircleHelp size={14} /><span>{question.validation.reasons.join(' ')}</span></div> : null}
    </div>}
    {question.evidence.length > 0 && <div className="evidence-list"><div className="evidence-heading"><div><div className="section-kicker">AUTHORIZED EVIDENCE</div><b>{question.evidence.length} source{question.evidence.length === 1 ? '' : 's'} used</b></div><span className="freshness-label"><CheckCheck size={13} /> Permission checked</span></div>
      {question.evidence.map((source) => <article key={source.document_id} className="evidence-source"><div className="source-file-icon"><FileText size={16} /></div><div className="source-body"><b>{source.title}</b><div className="source-meta">{source.document_id} <span>·</span> {source.version} <span>·</span> {new Date(source.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</div><p>“{source.passage}”</p></div></article>)}
    </div>}
    {question.human_answer && <div className="human-answer"><div className="human-answer-label"><UserRound size={14} /> HUMAN EXPERT RESPONSE</div><p>{question.human_answer}</p></div>}
    {question.knowledge_entry && <div className="publication-status"><BookOpen size={15} /> Knowledge reuse: <b>{prettyStatus(question.knowledge_entry.status)}</b></div>}
    {question.status === 'WAITING_FOR_HUMAN' && <div className="waiting-note"><Clock3 size={15} /><span>Waiting for a response. AI fallback is considered after <b>{new Date(question.response_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</b> only if the owner has enabled it for your audience.</span></div>}
    {actor === question.requester?.id && question.answer_type !== 'ACCESS_DENIED' && question.status !== 'WAITING_FOR_HUMAN' && <div className="feedback-bar"><span>Did this help unblock you?</span><div><button onClick={() => onFeedback(question, 'useful')}><Check size={13} /> Useful</button><button onClick={() => onFeedback(question, 'incorrect')}><CircleHelp size={13} /> Incorrect</button></div></div>}
  </section>
}

function StatusBadge({ value }: { value: string }) {
  const className = value === 'AI_ANSWERED' || value === 'RESOLVED' ? 'status-green' : value === 'HUMAN_REVIEW_REQUIRED' ? 'status-amber' : value === 'ACCESS_DENIED' ? 'status-red' : value === 'WAITING_FOR_HUMAN' ? 'status-blue' : 'status-muted'
  return <span className={`status-badge ${className}`}><i />{prettyStatus(value)}</span>
}

function DelegatePage({ actor, person, policy, options, onSaved }: { actor: string; person?: Person; policy: Delegation | null; options: Options | null; onSaved: () => Promise<void> }) {
  const [draft, setDraft] = useState<Delegation | null>(policy)
  const [saving, setSaving] = useState(false)
  const [localError, setLocalError] = useState('')
  useEffect(() => { setDraft(policy) }, [policy])
  if (!policy || !draft) return <section className="page-heading"><div className="eyebrow">MY AI DELEGATE</div><h1>No delegate profile is set up</h1><p className="page-intro">Switch to a synthetic knowledge owner to review an example delegation policy.</p></section>
  function toggle(list: string[], id: string) { return list.includes(id) ? list.filter((item) => item !== id) : [...list, id] }
  async function save() {
    if (!draft) return
    setSaving(true); setLocalError('')
    try {
      const toIso = (value: string | null) => value ? new Date(value).toISOString() : null
      await api('/api/delegation', actor, { method: 'PUT', body: JSON.stringify({ ...draft, starts_at: toIso(draft.starts_at), ends_at: toIso(draft.ends_at) }) })
      await onSaved()
    } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Could not save delegation settings.') }
    finally { setSaving(false) }
  }
  const localDate = (value: string | null) => value ? new Date(value).toISOString().slice(0, 16) : ''
  return <>
    <section className="page-heading"><div className="eyebrow"><span className="eyebrow-line" /> OWNER-CONTROLLED DELEGATION</div><div className="heading-with-status"><div><h1>My AI delegate</h1><p className="page-intro">Choose when Human API may answer in your absence, which knowledge it can use, and who may ask.</p></div><span className={`policy-pill ${draft.enabled ? 'policy-active' : ''}`}><i />{draft.enabled ? 'Delegation enabled' : 'Delegation paused'}</span></div></section>
    {localError && <div className="alert alert-error"><CircleHelp size={16} />{localError}</div>}
    <div className="delegate-layout">
      <section className="panel delegate-form">
        <div className="settings-section"><div className="settings-heading"><div className="settings-number">01</div><div><h2>Delegation status</h2><p>Only your explicit choice enables the AI fallback.</p></div></div>
          <label className="toggle-row"><span><b>Enable my AI delegate</b><small>Human API may answer only inside the scope configured below.</small></span><input type="checkbox" checked={draft.enabled} onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })} /><i className="toggle-track" /></label>
          <div className="form-two"><div><label className="field-label" htmlFor="delegate-start">Active from · UTC</label><input id="delegate-start" type="datetime-local" value={localDate(draft.starts_at)} onChange={(e) => setDraft({ ...draft, starts_at: e.target.value ? new Date(e.target.value).toISOString() : null })} /></div><div><label className="field-label" htmlFor="delegate-end">Active until · UTC</label><input id="delegate-end" type="datetime-local" value={localDate(draft.ends_at)} onChange={(e) => setDraft({ ...draft, ends_at: e.target.value ? new Date(e.target.value).toISOString() : null })} /></div></div>
        </div>
        <div className="settings-section"><div className="settings-heading"><div className="settings-number">02</div><div><h2>Response window and backup</h2><p>Busy presence does not trigger delegation. A scheduled owner absence or an elapsed response window does.</p></div></div>
          <div className="form-two"><div><label className="field-label" htmlFor="timeout">Wait for your response</label><div className="input-with-unit"><input id="timeout" type="number" min="5" max="1440" value={draft.timeout_minutes} onChange={(e) => setDraft({ ...draft, timeout_minutes: Number(e.target.value) })} /><span>minutes</span></div></div><div><label className="field-label" htmlFor="backup">Backup expert</label><select id="backup" value={draft.backup_id ?? ''} onChange={(e) => setDraft({ ...draft, backup_id: e.target.value || null })}><option value="">Select backup</option>{options?.backups.map((person) => <option key={person.id} value={person.id}>{person.name} · {person.role}</option>)}</select></div></div>
        </div>
        <div className="settings-section"><div className="settings-heading"><div className="settings-number">03</div><div><h2>Approved knowledge scope</h2><p>Sources are selected by you and checked against each requester's project permissions.</p></div></div>
          <div className="field-group"><div className="field-label">Projects</div><div className="check-grid">{options?.projects.map((item) => <label className="check-option" key={item.id}><input type="checkbox" checked={draft.project_ids.includes(item.id)} onChange={() => setDraft({ ...draft, project_ids: toggle(draft.project_ids, item.id) })} /><span>{item.name}</span></label>)}</div></div>
          <div className="field-group"><div className="field-label">Approved source repositories</div><div className="source-options">{options?.sources.filter((source) => draft.project_ids.includes(source.project_id)).map((source) => <label className="check-option" key={source.id}><input type="checkbox" checked={draft.source_ids.includes(source.id)} onChange={() => setDraft({ ...draft, source_ids: toggle(draft.source_ids, source.id) })} /><span><FileText size={14} />{source.name}</span></label>)}</div></div>
          <div className="field-group"><div className="field-label">Topics <span className="field-hint">Select the subjects you can answer.</span></div><div className="check-grid check-grid-topics">{['deployment', 'release', 'timeout', 'security', 'product', 'finance'].map((topic) => <label className="check-option" key={topic}><input type="checkbox" checked={draft.topics.includes(topic)} onChange={() => setDraft({ ...draft, topics: toggle(draft.topics, topic) })} /><span>{topic}</span></label>)}</div></div>
        </div>
        <div className="settings-section"><div className="settings-heading"><div className="settings-number">04</div><div><h2>Who may ask</h2><p>Owner consent never widens a person's existing document access.</p></div></div><div className="audience-list">{options?.audiences.map((person) => <label key={person.id} className="audience-row"><span className="avatar avatar-tiny">{initials(person.name)}</span><span><b>{person.name}</b><small>{person.role}</small></span><input type="checkbox" checked={draft.audience_ids.includes(person.id)} onChange={() => setDraft({ ...draft, audience_ids: toggle(draft.audience_ids, person.id) })} /></label>)}</div></div>
        <div className="save-row"><span>Policy version {draft.version} · {draft.manager_approved ? 'Manager approved' : 'Manager review pending'}</span><button className="primary-button" onClick={() => void save()} disabled={saving}>{saving ? 'Saving…' : <><Check size={16} /> Save delegation policy</>}</button></div>
      </section>
      <aside className="delegate-side-rail"><div className="panel policy-preview"><div className="section-kicker">LIVE POLICY PREVIEW</div><div className={`policy-status-card ${draft.enabled ? 'preview-enabled' : ''}`}><div className="policy-icon">{draft.enabled ? <Sparkles size={19} /> : <Clock3 size={19} />}</div><div><b>{draft.enabled ? 'Your delegate can respond' : 'Your delegate is paused'}</b><span>{draft.enabled ? 'Only when all policy checks pass.' : 'Human questions stay in your inbox.'}</span></div></div><div className="preview-list"><div><span>Projects</span><b>{draft.project_ids.length} selected</b></div><div><span>Audience</span><b>{draft.audience_ids.length} people</b></div><div><span>Sources</span><b>{draft.source_ids.length} approved</b></div><div><span>Response wait</span><b>{draft.timeout_minutes} min</b></div><div><span>Backup</span><b>{options?.backups.find((item) => item.id === draft.backup_id)?.name ?? 'Not set'}</b></div></div></div><div className="panel trust-note"><div className="trust-note-icon"><KeyRound size={17} /></div><h3>Consent has limits</h3><p>Your delegate cannot use your identity to unlock a source. The signed-in requester's access is checked before a source is retrieved.</p><div className="trust-note-footer"><CheckCheck size={14} /> {person?.availability === 'out_of_office' ? 'Owner absence is simulated' : 'Presence does not imply consent'}</div></div></aside>
    </div>
  </>
}

function InboxPage({ actor, escalations, pending, pendingPolicies, people, onOpen, onAnswer, onApprove, onApprovePolicy }: { actor: string; escalations: Escalation[]; pending: PendingEntry[]; pendingPolicies: PendingPolicy[]; people: Person[]; onOpen: (q: Question) => void; onAnswer: (q: Question, answer: string) => Promise<void>; onApprove: (entry: PendingEntry) => Promise<void>; onApprovePolicy: (policy: PendingPolicy) => Promise<void> }) {
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [localError, setLocalError] = useState('')
  const open = escalations.filter((entry) => entry.status === 'OPEN')
  const myPerson = people.find((person) => person.id === actor)
  return <>
    <section className="page-heading"><div className="eyebrow"><span className="eyebrow-line" /> HUMAN-IN-THE-LOOP</div><h1>Escalation inbox</h1><p className="page-intro">Questions with missing or conflicting evidence go to an authorized human. Your review does not make a private reply public by default.</p></section>
    {localError && <div className="alert alert-error"><CircleHelp size={16} />{localError}</div>}
    <div className="inbox-summary"><div><div className="inbox-summary-icon"><Inbox size={18} /></div><div><b>{open.length} open escalation{open.length === 1 ? '' : 's'}</b><span>Assigned to you or directed to your knowledge scope</span></div></div><div><div className="inbox-summary-icon inbox-summary-muted"><BookOpen size={18} /></div><div><b>{pending.length} knowledge review{pending.length === 1 ? '' : 's'}</b><span>Human corrections awaiting publication approval</span></div></div></div>
    <section className="panel inbox-panel"><div className="panel-heading"><div><div className="section-kicker">NEEDS EXPERT ATTENTION</div><h2>Open escalations</h2></div><span className="small-sim-tag">IN-APP ONLY</span></div>
      {open.length === 0 ? <EmptyState icon={CheckCheck} title="You're all caught up" text="Questions that need human judgment will show here when they are assigned to you." /> : <div className="inbox-list">{open.map((item) => {
        const question = item.question
        const canAnswer = actor === item.assignee_id || actor === question.owner?.id
        return <article key={item.id} className="escalation-item"><div className="escalation-head"><div className="escalation-icon"><Users size={17} /></div><div><b>{question.question}</b><span>{question.project?.name} · From {question.requester?.name}</span></div><StatusBadge value={question.status} /></div><div className="escalation-reason"><CircleHelp size={14} /><span>{item.reason}</span></div><div className="escalation-actions"><button className="text-button" onClick={() => onOpen(question)}>Review evidence and history <ArrowUpRight size={14} /></button></div>{canAnswer && <form className="escalation-reply" onSubmit={async (event) => { event.preventDefault(); try { await onAnswer(question, drafts[question.id] ?? '') } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Could not save response.') } }}><textarea rows={2} value={drafts[question.id] ?? ''} onChange={(event) => setDrafts({ ...drafts, [question.id]: event.target.value })} placeholder={`Verified answer from ${myPerson?.name ?? 'you'}…`} minLength={5} required /><button className="secondary-button" type="submit"><Send size={14} /> Reply</button></form>}</article>
      })}</div>}
    </section>
    <section className="panel inbox-panel"><div className="panel-heading"><div><div className="section-kicker">CONTROLLED KNOWLEDGE REUSE</div><h2>Pending publication review</h2></div><span className="small-sim-tag">OWNER OR MANAGER</span></div>
      {pending.length === 0 ? <EmptyState icon={BookOpen} title="No corrections awaiting review" text="An expert answer can become reusable project knowledge after an authorized owner or manager approves it." /> : <div className="knowledge-review-list">{pending.map((entry) => <article className="knowledge-review" key={entry.id}><div className="review-doc"><div className="source-file-icon"><FileText size={15} /></div><div><b>{entry.project_name} · Expert correction</b><span>Added by {people.find((person) => person.id === entry.created_by)?.name ?? entry.created_by} · {timeAgo(entry.created_at)}</span></div></div><p>{entry.content}</p><button className="secondary-button" onClick={async () => { try { await onApprove(entry) } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Could not approve entry.') } }}><CheckCheck size={15} /> Approve for project reuse</button></article>)}</div>}
    </section>
    {pendingPolicies.length > 0 && <section className="panel inbox-panel"><div className="panel-heading"><div><div className="section-kicker">OWNER CONSENT AND MANAGER REVIEW</div><h2>Delegation policies awaiting approval</h2></div><span className="small-sim-tag">SCOPE METADATA</span></div><div className="knowledge-review-list">{pendingPolicies.map((policy) => <article className="knowledge-review" key={policy.owner_id}><div className="review-doc"><span className="avatar avatar-tiny">{initials(policy.owner_name)}</span><div><b>{policy.owner_name} · Policy version {policy.version}</b><span>{policy.project_count} projects · {policy.source_count} sources · {policy.audience_count} audience members · {policy.timeout_minutes} minute response window</span></div></div><button className="secondary-button" onClick={async () => { try { await onApprovePolicy(policy) } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Could not approve policy.') } }}><CheckCheck size={15} /> Approve delegation scope</button></article>)}</div></section>}
  </>
}

function GovernancePage({ actor, data, people, projects, onRevoked }: { actor: string; data: Governance | null; people: Person[]; projects: Project[]; onRevoked: () => Promise<void> }) {
  const [employeeId, setEmployeeId] = useState('alice')
  const [projectId, setProjectId] = useState('alpha')
  const [revoking, setRevoking] = useState(false)
  const [localError, setLocalError] = useState('')
  async function revoke() {
    setRevoking(true); setLocalError('')
    try {
      await api('/api/governance/revoke', actor, { method: 'POST', body: JSON.stringify({ employee_id: employeeId, project_id: projectId }) })
      await onRevoked()
    } catch (reason) { setLocalError(reason instanceof Error ? reason.message : 'Access could not be revoked.') }
    finally { setRevoking(false) }
  }
  const total = Object.values(data?.counts ?? {}).reduce((sum, count) => sum + count, 0)
  return <>
    <section className="page-heading"><div className="eyebrow"><span className="eyebrow-line" /> SECURITY AND GOVERNANCE</div><h1>Trust, with an audit trail.</h1><p className="page-intro">Review policy metadata, measured workflow states, and revoke project access. Administrative visibility does not grant access to question or document content.</p></section>
    {localError && <div className="alert alert-error"><CircleHelp size={16} />{localError}</div>}
    <div className="governance-stat-grid"><div className="panel governance-stat"><span>Tracked questions</span><b>{total}</b><small>Database records across all statuses</small></div><div className="panel governance-stat"><span>Active delegations</span><b>{data?.delegations.filter((item) => item.enabled).length ?? 0}</b><small>Owner-enabled policy records</small></div><div className="panel governance-stat"><span>Audit transitions</span><b>{data?.audit_events.length ?? 0}</b><small>Latest 25 state changes shown</small></div></div>
    <div className="governance-columns"><section className="panel governance-panel"><div className="panel-heading"><div><div className="section-kicker">ACCESS CONTROL</div><h2>Revoke project membership</h2></div><div className="governance-head-icon"><KeyRound size={16} /></div></div><p className="panel-copy">Revocation cancels pending AI work and invalidates active answer content for the affected requester. It does not reveal the files that person lost access to.</p><label className="field-label" htmlFor="revoke-user">Employee</label><select id="revoke-user" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>{people.filter((person) => person.id !== actor).map((person) => <option key={person.id} value={person.id}>{person.name} · {person.role}</option>)}</select><label className="field-label field-gap" htmlFor="revoke-project">Project</label><select id="revoke-project" value={projectId} onChange={(e) => setProjectId(e.target.value)}>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select><button className="danger-button" onClick={() => void revoke()} disabled={revoking}><LockKeyhole size={15} /> {revoking ? 'Revoking…' : 'Revoke project access'}</button><div className="admin-limit"><ShieldCheck size={15} /><span>As an administrator, you still need a project grant to see the project's knowledge.</span></div></section>
      <section className="panel governance-panel"><div className="panel-heading"><div><div className="section-kicker">POLICY REGISTER</div><h2>Delegation records</h2></div><span className="small-sim-tag">METADATA ONLY</span></div><div className="policy-register">{data?.delegations.map((item) => <div className="policy-register-row" key={item.owner_id}><div className="avatar avatar-tiny">{initials(people.find((person) => person.id === item.owner_id)?.name)}</div><div><b>{people.find((person) => person.id === item.owner_id)?.name ?? item.owner_id}</b><span>Version {item.version} · {item.project_count} project · {item.source_count} source</span></div><StatusBadge value={item.enabled ? 'AI_ANSWERED' : 'CLOSED'} /></div>)}</div></section>
    </div>
    <section className="panel audit-panel"><div className="panel-heading"><div><div className="section-kicker">AUDIT TRAIL</div><h2>Recent workflow events</h2></div><span className="audit-privacy"><LockKeyhole size={13} /> No question text stored in this view</span></div><div className="audit-table-wrap"><table><thead><tr><th>Event</th><th>Resource</th><th>Actor</th><th>Time</th></tr></thead><tbody>{data?.audit_events.map((event, index) => <tr key={`${event.resource_id}-${event.at}-${index}`}><td><span className="audit-event-dot" />{event.action}</td><td>{event.resource_type} · {event.resource_id.slice(0, 8)}</td><td>{people.find((person) => person.id === event.actor_id)?.name ?? 'System'}</td><td>{new Date(event.at).toLocaleString()}</td></tr>)}</tbody></table></div><p className="audit-note">{data?.note}</p></section>
  </>
}

function EmptyState({ icon: Icon, title, text, action, onClick }: { icon: typeof Activity; title: string; text: string; action?: string; onClick?: () => void }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={20} /></div><b>{title}</b><p>{text}</p>{action && <button className="text-button" onClick={onClick}>{action} <ArrowUpRight size={14} /></button>}</div>
}

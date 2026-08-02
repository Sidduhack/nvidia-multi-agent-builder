import { useMemo, useState } from "react";

const navigation = ["Overview", "Files", "Agents", "Tasks", "Logs", "Tests", "Preview", "Settings"] as const;
type View = (typeof navigation)[number];
type AgentStatus = "complete" | "working" | "waiting";

const agents: { name: string; role: string; status: AgentStatus }[] = [
  { name: "Planner", role: "Requirements & task graph", status: "complete" },
  { name: "Architect", role: "System architecture", status: "complete" },
  { name: "UI/UX", role: "Product experience", status: "working" },
  { name: "Frontend", role: "React interface", status: "working" },
  { name: "Backend", role: "APIs & business logic", status: "waiting" },
  { name: "Database", role: "Schema & policies", status: "waiting" },
  { name: "Security", role: "Application security", status: "waiting" },
  { name: "Reviewer", role: "Code review", status: "waiting" },
  { name: "Testing", role: "Automated verification", status: "waiting" },
  { name: "Debugger", role: "Failure repair", status: "waiting" },
  { name: "Performance", role: "Optimization", status: "waiting" },
  { name: "Integrator", role: "Final integration", status: "waiting" },
];

const files = ["frontend/", "  src/", "    App.tsx", "    styles.css", "backend/", "tests/", ".env.example", "README.md"];
const logs = [
  "Planner completed requirements analysis",
  "Architect approved initial system boundaries",
  "UI/UX started dashboard specification",
  "Frontend started workspace implementation",
];

function StatusDot({ status }: { status: AgentStatus }) {
  return <span className={`agent-dot ${status}`} aria-label={status} />;
}

export function App() {
  const [view, setView] = useState<View>("Overview");
  const [projectName, setProjectName] = useState("");
  const [prompt, setPrompt] = useState("");
  const ready = projectName.trim().length > 1 && prompt.trim().length > 20;
  const completed = useMemo(() => agents.filter((agent) => agent.status === "complete").length, []);

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Project navigation">
        <div className="brand"><span className="brand-mark" aria-hidden="true">N</span><div><strong>Agent Builder</strong><small>NVIDIA engineering workspace</small></div></div>
        <nav>{navigation.map((item) => <button className={view === item ? "nav-item active" : "nav-item"} key={item} type="button" onClick={() => setView(item)}>{item}</button>)}</nav>
        <div className="sidebar-foot"><span className="live-dot" />System ready</div>
      </aside>

      <main className="workspace">
        <header className="topbar"><div><p className="eyebrow">Project workspace</p><h1>Multi-Agent Builder</h1></div><span className="status-badge"><span className="live-dot" /> Ready</span></header>

        {view === "Overview" && <>
          <section className="hero" aria-labelledby="build-heading">
            <p className="eyebrow">Virtual software engineering organization</p><h2 id="build-heading">Turn an idea into a verified project.</h2>
            <p className="supporting">Specialized agents plan, design, build, review, test and integrate your project while the orchestrator keeps every dependency under control.</p>
            <form className="prompt-form" onSubmit={(event) => event.preventDefault()}>
              <div className="field-row"><div><label htmlFor="project-name">Project name</label><input id="project-name" value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Gaming platform" /></div><div className="model-chip"><span>Provider</span><strong>NVIDIA NIM</strong></div></div>
              <label htmlFor="project-prompt">Project prompt</label><textarea id="project-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={7} placeholder="Build a professional gaming website with authentication, admin dashboard, responsive UI…" />
              <div className="form-actions"><button className="primary-action" type="button" disabled={!ready} title={ready ? "Backend execution wiring arrives in a later phase" : "Add a project name and detailed prompt"}>Build Project</button><span>{prompt.length} characters</span></div>
              <p className="form-note">The dashboard validates input now; project execution remains safely disabled until the backend project API is connected.</p>
            </form>
          </section>
          <section className="status-grid" aria-label="Workspace status"><article><span>Engineering agents</span><strong>12</strong><small>Specialized roles configured</small></article><article><span>Pipeline progress</span><strong>{completed}/12</strong><small>Demo state for dashboard validation</small></article><article><span>Provider</span><strong className="text-value">NVIDIA</strong><small>Server-side model routing</small></article></section>
          <section className="pipeline-section"><div className="section-heading"><div><p className="eyebrow">Execution pipeline</p><h3>Agent activity</h3></div><span>2 working</span></div><div className="agent-grid">{agents.map((agent) => <article className="agent-card" key={agent.name}><div><StatusDot status={agent.status} /><strong>{agent.name}</strong></div><p>{agent.role}</p><small>{agent.status}</small></article>)}</div></section>
        </>}

        {view === "Files" && <Panel title="Project files" subtitle="Virtual workspace"><div className="file-tree">{files.map((file) => <code key={file}>{file}</code>)}</div></Panel>}
        {view === "Agents" && <Panel title="Agents" subtitle="Specialized team"><div className="agent-list">{agents.map((agent) => <div key={agent.name}><StatusDot status={agent.status} /><span><strong>{agent.name}</strong><small>{agent.role}</small></span><em>{agent.status}</em></div>)}</div></Panel>}
        {view === "Tasks" && <Panel title="Tasks" subtitle="Orchestrator queue"><EmptyState title="No live project" text="Task graph data will appear here after a project execution is started." /></Panel>}
        {view === "Logs" && <Panel title="Logs" subtitle="Meaningful execution events"><div className="log-list">{logs.map((log, index) => <div key={log}><time>00:0{index + 1}</time><span>{log}</span></div>)}</div></Panel>}
        {view === "Tests" && <Panel title="Tests" subtitle="Verification"><EmptyState title="No test run" text="Unit, integration and end-to-end results will be summarized here without overwhelming raw output." /></Panel>}
        {view === "Preview" && <Panel title="Preview" subtitle="Isolated runtime"><div className="preview-shell"><span>Preview environment</span><strong>Waiting for generated project</strong><p>Build and runtime output will be rendered here after sandbox integration.</p></div></Panel>}
        {view === "Settings" && <Panel title="Settings" subtitle="Models & execution"><div className="settings-card"><label>Provider</label><strong>NVIDIA NIM</strong><p>API keys remain server-side and are never rendered in this interface.</p><label>Model routing</label><strong>Automatic + per-agent overrides</strong></div></Panel>}
      </main>
    </div>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <section className="panel"><p className="eyebrow">{subtitle}</p><h2>{title}</h2>{children}</section>;
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><span>○</span><strong>{title}</strong><p>{text}</p></div>;
}

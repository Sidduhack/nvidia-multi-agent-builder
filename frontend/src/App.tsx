const navigation = ["Overview", "Files", "Agents", "Tasks", "Logs", "Tests", "Preview", "Settings"];

export function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Project navigation">
        <div className="brand"><span className="brand-mark" aria-hidden="true">N</span><div><strong>Agent Builder</strong><small>Engineering workspace</small></div></div>
        <nav>{navigation.map((item, index) => <button className={index === 0 ? "nav-item active" : "nav-item"} key={item} type="button">{item}</button>)}</nav>
      </aside>
      <main className="workspace">
        <header className="topbar"><div><p className="eyebrow">Project workspace</p><h1>Multi-Agent Builder</h1></div><span className="status-badge"><span aria-hidden="true">○</span> Not started</span></header>
        <section className="hero" aria-labelledby="build-heading">
          <p className="eyebrow">Build with a specialized AI engineering team</p><h2 id="build-heading">What should the agents build?</h2>
          <p className="supporting">Describe the product. Planning and architecture happen before engineering tasks are scheduled.</p>
          <form className="prompt-form">
            <label htmlFor="project-name">Project name</label><input id="project-name" name="project-name" placeholder="Gaming platform" />
            <label htmlFor="project-prompt">Project prompt</label><textarea id="project-prompt" name="project-prompt" rows={7} placeholder="Build a professional gaming website with authentication, admin dashboard…" />
            <button className="primary-action" type="button" disabled title="Project API wiring arrives in a later implementation phase">Build Project</button>
            <p className="form-note">Project execution is intentionally disabled until the approved API is connected.</p>
          </form>
        </section>
        <section className="status-grid" aria-label="Workspace status"><article><span>Agents</span><strong>12</strong><small>Specialized roles configured</small></article><article><span>Active tasks</span><strong>0</strong><small>No project running</small></article><article><span>Tests</span><strong>—</strong><small>Not run</small></article></section>
      </main>
    </div>
  );
}

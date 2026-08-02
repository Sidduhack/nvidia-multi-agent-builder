from app.security_review import SecurityReviewer, Severity


def test_detects_hardcoded_secret_as_blocking() -> None:
    report = SecurityReviewer().scan_project({"backend/config.py": 'API_KEY = "super-secret-value"'})
    assert report.blocking is True
    assert report.findings[0].rule_id == "SEC001"
    assert report.findings[0].severity is Severity.CRITICAL


def test_detects_shell_execution() -> None:
    findings = SecurityReviewer().scan_file(
        "backend/jobs.py", 'subprocess.run(command, shell=True)'
    )
    assert any(item.rule_id == "SEC003" for item in findings)


def test_detects_frontend_raw_html_sink() -> None:
    findings = SecurityReviewer().scan_file(
        "frontend/src/Page.tsx", "return <div dangerouslySetInnerHTML={{__html: value}} />"
    )
    assert any(item.rule_id == "SEC005" for item in findings)


def test_reports_line_numbers() -> None:
    findings = SecurityReviewer().scan_file(
        "app.py", 'safe = True\npassword = "123456789-secret"\n'
    )
    assert findings[0].line == 2


def test_ignores_dependency_and_build_directories() -> None:
    reviewer = SecurityReviewer()
    assert reviewer.scan_file("node_modules/pkg/index.js", 'token="123456789"') == ()
    assert reviewer.scan_file("dist/app.js", 'eval("x")') == ()


def test_clean_project_is_non_blocking() -> None:
    report = SecurityReviewer().scan_project(
        {
            "backend/api.py": "def health():\n    return {'ok': True}\n",
            "frontend/src/App.tsx": "export const App = () => <main>Hello</main>;",
        }
    )
    assert report.findings == ()
    assert report.blocking is False


def test_results_are_deterministic_by_path() -> None:
    report = SecurityReviewer().scan_project(
        {"z.py": 'eval("z")', "a.py": 'exec("a")'}
    )
    assert [finding.path for finding in report.findings] == ["a.py", "z.py"]

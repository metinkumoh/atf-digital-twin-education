# Week 4.2 — Exercise 4: Digital Twin Learning Studio (deployment package)

**Status:** deployable source code and automated backend tests. Hosting, real-device tests, and network throttling must be verified by the learner. **No real LLM is connected:** the educational assistant uses deterministic TF-IDF retrieval from bundled lessons and simple Week 3 tools; the Week 1 adapter is an integration placeholder. Do not claim Gemini/Claude integration in this project.

## Features retained from Week 4.1

- **Chat:** topic-based offline lesson retrieval with citations, calculator, time, notes commands.
- **Learn:** eight sample lesson excerpts, with four-item pagination.
- **Quiz:** five knowledge-check questions.
- **Notes:** session-only notes and search, no cloud database.
- **Dashboard:** per-session activity and measured backend latency (count/mean/maximum).
- **English and Hausa interface:** partial UI translation only; teaching materials are not fully localized.
- **Mobile-oriented UI:** compact responsive CSS, text-size preference, light/dark modes; **not yet tested on a real device**.
- **Optimizations:** cached *public* lesson data using `st.cache_data(ttl=3600)`, per-session Tutor instance so notes aren't globally shared, lazy dashboard/chart creation in tab view, and paginated lessons.
- **Safety:** input length limits, safe arithmetic parser, basic PII/prompt-injection checks (educational heuristics, not complete protection).

## Project structure

```text
app.py                    Streamlit frontend
backend: tutor_backend.py  tools, quiz, safety checks, knowledge retrieval
rag_system.py             Week 2.4 TF-IDF RAG
context_manager.py        Week 2.2 context window module
week1_adapter.py          unconnected placeholder
lessons.json              included public educational content
deployment_utils.py       latency and pagination utilities
.streamlit/config.toml    UI/security configuration
.env.example              template only: no secrets required
requirements.txt          dependencies
runtime.txt               Python runtime preference
.github/workflows/tests.yml  automated tests on GitHub pushes
scripts/smoke_test.py     HTTP smoke test for hosted root URL
tests/                    unit tests
DEPLOYMENT_CHECKLIST.md   low-bandwidth/mobile/manual verification
OPERATIONS.md             monitoring, deployment, rollback
```

## Local setup (Windows 11 / PowerShell)

```powershell
cd "C:\path\to\Week_4_2_Exercise_4_Digital_Twin_Deployment"
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

App opens at `http://localhost:8501`. From inside VS Code, open the folder containing `app.py` itself, not its parent.

## Streamlit Community Cloud deployment (free option)

1. Create a GitHub repo (e.g. `digital-twin-learning-studio`), upload **the contents of this folder** preserving directories; do not upload an outer ZIP as a single file.
2. Check the repository for secrets or personal notes **before committing**; `.gitignore` does not protect already tracked files.
3. Go to https://share.streamlit.io/, select **Create app → I have an app**, choose your repo / `main` / `app.py`, and deploy.
4. Streamlit installs packages from `requirements.txt`; if offered, select Python 3.11 in Advanced settings.
5. Inspect **Manage app → Logs**. After the app is running, exercise Chat/Quiz/Notes/Dashboard from a browser.
6. Copy the *actual* Streamlit app URL and share as your submission evidence.

The ZIP is **not a completed live deployment**. You must publish it from your own GitHub and Streamlit accounts. Hugging Face Docker Spaces may require a paid account; this package targets Streamlit Community Cloud so you can continue without paying.

## Secrets / environment management

There is **no paid LLM or API key requirement**. Do not put Anthropic or Gemini credentials in GitHub merely for this demo. If a real LLM is integrated later, configure the API key in Streamlit Community Cloud **Settings → Secrets** and retrieve with `st.secrets.get(...)`. Local secrets belong in `.streamlit/secrets.toml` (gitignored); use `.env.example` for names only. Never print secret values.

## Error handling and monitoring

- Validation exceptions produce user-readable messages; unexpected chat exceptions produce a generic error and an application log stack trace.
- Streamlit deployment logs help diagnose startup failures. Server application health can be checked via `/_stcore/health`, but availability of that endpoint can vary behind platforms/proxies; always also verify app behavior.
- Dashboard reports response-processing times **in the current session**, not real end-to-end network timing, CPU, global usage or uptime. No central analytics service is installed.
- Use `python scripts/smoke_test.py https://your-app.streamlit.app` (optional; requires app to be deployed). See `OPERATIONS.md` for monitoring and rollback recommendations.

## Performance measurement

- Cached lesson-data load avoids repeated JSON decoding of static public lessons for reruns. The RAG index is still constructed **once per browser session**, not globally cached, to avoid shared mutable state.
- Compare initial load and subsequent loads using browser performance tools; chat request metrics are shown in Dashboard. Report numbers from real runs, not invented values.
- Test 3G throttling in Chrome DevTools; record cold start vs warm load, initial bytes/download volume, and time to interaction. Results are not pre-verified.

## Scope and limitations

Session state resets can lose notes/chat; do not store personal or regulated information. No authentication, database, formal security audit, full Hausa translation, voice transcription, or guaranteed latency/SLA. This is a deployment-oriented educational prototype, **not a security-certified production application**.

## ATF Challenge Project additions

- **Optional real Gemini generation:** `ai_provider.py`; disabled by default, offline RAG works without a key. For test-only setup see `CHALLENGE_SUBMISSION.md`. Gemini is not a requirement for basic offline use.
- **Availability sampling:** `.github/workflows/uptime.yml` and `scripts/uptime_check.py`; configure GitHub Actions variable `APP_URL` only after the live Streamlit URL exists. Scheduled availability checks are not a 99% uptime guarantee.
- **10+ real-user and 3G plan:** `USER_TESTING.md`, `feedback_template.csv`, `performance_template.csv`.
- **Deployment and submission checklist:** `CHALLENGE_SUBMISSION.md` plus `DEPLOYMENT_CHECKLIST.md`.

This project is a deployment-ready *educational demonstration*, not a security-audited production service. Do not claim all success criteria have been achieved until you have deployed, tested on real devices, collected genuine user feedback and recorded a full week of uptime evidence.

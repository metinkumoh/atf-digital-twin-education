# ATF Challenge — Production-Ready AI Education Platform

## Project
Digital Twin Learning Studio — practical English/partial Hausa digital-skills teaching assistant. Existing Week 1–4 components are used: deterministic TF-IDF RAG, context management, safe calculator, session notes, quizzes and Streamlit dashboard. Optional Google Gemini can generate an explanation grounded in returned lesson excerpts, **disabled by default**.

## Deployment status
- Code assembled and unit tests passed locally in the preparation environment.
- Cloud public URL: **TO BE ADDED AFTER DEPLOYMENT**
- Real smartphone/3G test: **PENDING**
- 10+ participant feedback: **PENDING**
- 7 days uptime evidence: **PENDING**
- Vulnerability-free status: **NOT VERIFIED / NO GUARANTEE**

## Local validation
```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

## Deploy free on Streamlit Community Cloud
1. Create GitHub repo, e.g. `atf-digital-twin-education`.
2. Upload the **files in this folder** to repo root (including `.github` and `.streamlit` folders). Do not upload private secrets.
3. https://share.streamlit.io → Create app → choose repo, branch `main`, file `app.py`.
4. Verify build, run and test Chat, Learn, Quiz, Notes, Dashboard from public URL.
5. Confirm app in private browser session; perform a real mobile test and Slow 3G measurements.
6. Save URL and real outcomes in this document and the testing templates.

## Optional Gemini
- Offline mode is the default and needs no Gemini key.
- To use Gemini on **a private/test deployment**, add the package `google-genai>=1.0,<2` to `requirements.txt` and set Streamlit Secrets:
```toml
GEMINI_API_KEY = "YOUR_PRIVATE_KEY"
ENABLE_GEMINI = "true"
GEMINI_MODEL = "gemini-2.5-flash"
```
- Keep app private or add authenticated access and durable account-level quotas before enabling a paid or limited API key for untrusted visitors. **The included session limiter alone is insufficient.**
- Only retrieved educational excerpts are sent to Gemini. Learning data may be processed under Google's API terms; check provider policy before use.

## What is (and isn't) production-ready
- Modular code, secrets loading, error fallback, tests, read-only cached lessons, bounded inputs, standard responsive UI, session performance metrics, documented deployment and rollback are included.
- Full security audit, independent load test, uptime certification, persistent storage, global rate limiting and site-wide analytics are **not included**. Browser-session metrics are not global usage monitoring.

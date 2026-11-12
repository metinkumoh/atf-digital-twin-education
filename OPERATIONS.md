# Operations — deploy, monitor, rollback

## Deployment/update workflow

1. Modify code in VS Code. `python -m unittest discover -s tests -v` and `python -m streamlit run app.py`.
2. Check diff and tracked files: `git status` then `git diff`. Never stage keys or user exports.
3. `git add .` then `git commit -m "Improve Digital Twin"` then `git push`.
4. Streamlit Community Cloud rebuilds after GitHub changes. Monitor Manage app → Logs and verify the working interface.
5. CI runs unittest checks on pushes/pull requests but does **not** prove the hosted app works.

## Monitoring

- Review Streamlit application logs for errors; never log user messages, API keys, exported files, or private notes.
- Dashboard tab: measured backend request count, average, and maximum latency in **your current session only**. It is not fleet-wide usage analytics.
- Check app URL and essential workflows after each deployment. Optional `scripts/smoke_test.py` fetches the URL and checks an HTTP success response; it cannot verify interactive features.
- For downtime alerts, configure an external uptime monitor yourself if appropriate. No external alerting is configured in this package.

## Rollback

1. Identify issue in app logs and inspect `git log --oneline -5`.
2. Revert the known faulty commit with `git revert COMMIT_HASH`, resolve conflicts if any, then `git push`.
3. Confirm hosted app successfully rebuilds and manually test Chat, Learn, Notes, Quiz and Dashboard.
4. Avoid `git reset --hard` and force-push on shared history. Rollback of code does not restore session data or undo persistent database changes.

## Security and costs

This app is offline-only, requires no external AI API key, and is designed for Streamlit Community Cloud. Real user authentication, durable database, comprehensive protection against abuse, regular dependency checks and security reviews are outside this course exercise.

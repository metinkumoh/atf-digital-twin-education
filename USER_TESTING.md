# Real-user test and success criteria

**Not yet verified:** 10+ real testers, positive feedback, seven days at >=99% uptime, sub-three-second 3G loading, and absence of vulnerabilities.

## Recruit and test

1. Publish the URL, confirm it opens in private/incognito mode, and share it with **at least ten different real people** (with consent).
2. Ask each to use Chat, Learn, Quiz, Notes, Dashboard; test language switch and phone layout.
3. Collect only non-identifying feedback with the **feedback_template.csv** (do not request names, emails, or phone numbers). Have testers avoid putting secrets or personal information into the demo.
4. Record device class, rough network type, load time and whether each task worked; keep raw screenshots private if they include personal info.
5. Report the number of genuine respondents and percentage rating 4 or 5 out of 5, alongside common failures. Don't invent feedback.

## 3G / mobile performance

- Chrome: F12 → Network → throttling → Slow 3G; Ctrl+Shift+M → choose narrow mobile viewport; clear cache, hard reload, measure 3 runs.
- Real smartphone: test portrait/landscape, 3G or throttled connection where possible; test first meaningful usable interaction, not only server response.
- Record each measurement in `performance_template.csv` with actual seconds; average and report median and slowest.
- Goal is **under 3 seconds on 3G**; it is not guaranteed by the project. Cold Streamlit startup and slow networks may exceed this target.

## Uptime over seven days

- Set a repository variable `APP_URL` to the deployed **https://*.streamlit.app** URL to enable GitHub Actions `uptime.yml` polling every 30 minutes (scheduled job timing may drift or skip). Allow Actions to run and check for failures.
- A separate third-party uptime service with persistent reports may be preferable. A valid week requires a full 7-day observation period.
- From successful and failed checks, estimate `uptime = 100 * successful_checks / total_checks`. For true availability guarantees, use an external monitor with accurate downtime duration; scheduled checks only provide a sample.
- To claim >=99% uptime, collect evidence for a full 7 days; the code alone does not prove uptime.

## Security review

- Confirm no credentials are in Git files or logs, `.streamlit/secrets.toml` and `.env` ignored, and no external user messages are recorded server-side.
- Check PII guards, injection tests, dependency alerts, and rate limits.
- **This is an educational demonstration, not a penetration-tested, vulnerability-free service.** Per-session limits are not abuse prevention; production use of a server-paid Gemini key requires real authentication and global quotas.

# Live acceptance checklist — fill in only after real testing

## Application
- [ ] GitHub repo created; required files uploaded and no secret values committed
- [ ] Streamlit Community Cloud deployment URL recorded: __________________
- [ ] Build/run logs contain no startup errors
- [ ] Chat: question about Python/SQL produces evidence passages
- [ ] Calculator: `Calculate: 25 * 4` returns 100
- [ ] Notes: save, find, and delete a note within session
- [ ] Quiz: answer questions and complete the quiz
- [ ] Dashboard: activity and processing-time metrics visible
- [ ] Confirm app error response for blank or malicious input

## African-context / low-bandwidth
- [ ] English UI checked
- [ ] Hausa UI checked; record untranslated sections
- [ ] Phone test in portrait: readable labels, no horizontal overflow
- [ ] Phone test in landscape: content usable
- [ ] Chrome DevTools → Network → Throttling → Slow 3G test performed
- [ ] Cold-start time measured: ______ seconds
- [ ] Warm-load time measured: ______ seconds
- [ ] Transfer/download size recorded: ______ MB
- [ ] Chat response measured on simulated 3G: ______ seconds
- [ ] App status/limitations explained clearly to user

## Suggested mobile/3G test steps
1. In Chrome desktop open the deployed URL, press F12 (DevTools), click Network, enable **Disable cache**, choose **Slow 3G** if available (or create a custom throttle profile), and reload.
2. Open DevTools Device Toolbar (Ctrl+Shift+M), use a 360 px wide viewport to inspect layout. This is simulation, not an actual phone test.
3. Repeat on a physical Android or iPhone using a slow mobile data connection if possible.
4. Record timings and screenshots; do not claim mobile/3G passed merely because responsive CSS is present.

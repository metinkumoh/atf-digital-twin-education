"""Simple public URL HTTP smoke check, not a full UI test."""
import sys
import urllib.request

if __name__ == '__main__':
    if len(sys.argv)!=2 or not sys.argv[1].startswith('https://'):
        raise SystemExit('Usage: python scripts/smoke_test.py https://your-app.streamlit.app')
    req=urllib.request.Request(sys.argv[1],headers={'User-Agent':'DigitalTwinExercise4/1.0'})
    with urllib.request.urlopen(req,timeout=30) as res:
        print('HTTP status:',res.status)
        if res.status != 200:
            raise SystemExit('Unexpected response status')

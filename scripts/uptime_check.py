"""Best-effort public availability check: URL from CLI or APP_URL environment variable."""
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse


def check(url, timeout=15):
    parsed=urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith('.streamlit.app'):
        raise ValueError('Use an https://*.streamlit.app URL')
    start=time.perf_counter()
    request=Request(url,headers={'User-Agent':'ATF-Education-Uptime-Check/1.0'})
    with urlopen(request,timeout=timeout) as response:
        status=response.status
    elapsed=time.perf_counter()-start
    return status,elapsed

if __name__ == '__main__':
    url=sys.argv[1] if len(sys.argv)>1 else os.environ.get('APP_URL','')
    if not url:
        print('Set APP_URL or pass your public Streamlit URL. No check performed.')
        sys.exit(2)
    try:
        status,elapsed=check(url)
        print(f'HTTP {status}, time to headers {elapsed:.2f}s')
        sys.exit(0 if status == 200 else 1)
    except Exception as exc:
        print('Availability check failed:',type(exc).__name__)
        sys.exit(1)

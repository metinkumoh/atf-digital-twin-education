"""Lightweight app performance helpers, without tracking personal content."""
from statistics import mean

def add_duration(prior, seconds, max_entries=100):
    if seconds < 0: raise ValueError('Duration must be nonnegative')
    return (list(prior)+[float(seconds)])[-max_entries:]

def recent_latency_stats(durations):
    if not durations:
        return {'count':0,'mean':None,'max':None}
    return {'count':len(durations),'mean':mean(durations),'max':max(durations)}

def paginate(items, page=1, page_size=4):
    if page < 1 or page_size < 1:
        raise ValueError('Page and page size must be positive')
    start=(page-1)*page_size
    end=min(start+page_size,len(items))
    return items[start:end],start,end

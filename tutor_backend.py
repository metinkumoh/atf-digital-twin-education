"""Offline bilingual digital-skills tutor: deterministic RAG, safe calculator and tools.

Educational demonstration, not an authenticated production service or generative LLM.
Only approved, bundled lesson material is used for answer evidence.
"""
from __future__ import annotations
import ast
import json
import math
import operator
import re
from datetime import datetime, timezone
from pathlib import Path
from rag_system import RAGSystem
from context_manager import ContextManager

ROOT = Path(__file__).resolve().parent
LESSONS = ROOT / 'lessons.json'
OPS = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
       ast.Div:operator.truediv,ast.USub:operator.neg,ast.UAdd:operator.pos}
BAD_INSTRUCTIONS = [re.compile(x, re.I) for x in (
    r'ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions',
    r'\[\s*system\s*(?:override|message)\s*\]',
    r'reveal\s+(?:your\s+)?(?:system\s+prompt|hidden\s+instructions)',
    r'---\s*system\s+message',
)]
CONTACT_PII = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)')


def safe_calculate(expr: str) -> str:
    if not isinstance(expr, str) or not expr.strip() or len(expr)>80:
        raise ValueError('Enter a short arithmetic expression.')
    try: tree=ast.parse(expr.strip(),mode='eval')
    except SyntaxError as e: raise ValueError('Invalid arithmetic expression.') from e
    if len(list(ast.walk(tree)))>25: raise ValueError('Expression too complex.')
    def visit(n):
        if isinstance(n,ast.Expression):return visit(n.body)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            if not math.isfinite(n.value) or abs(n.value)>1e9:raise ValueError('Number is too large.')
            return n.value
        if isinstance(n,ast.UnaryOp) and type(n.op) in (ast.UAdd,ast.USub): return OPS[type(n.op)](visit(n.operand))
        if isinstance(n,ast.BinOp) and type(n.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div):
            a,b=visit(n.left),visit(n.right)
            try: r=OPS[type(n.op)](a,b)
            except ZeroDivisionError as e:raise ValueError('Cannot divide by zero.') from e
            if not math.isfinite(r) or abs(r)>1e12:raise ValueError('Result is too large.')
            return r
        raise ValueError('Only +, -, * and / are supported.')
    return f'{visit(tree):g}'


def load_lessons(path: Path=LESSONS):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,list) or not data or any(not isinstance(d,dict) or not d.get('text') or not d.get('title') for d in data):
        raise ValueError('Lesson data must be a nonempty list with title and text.')
    return data


class Tutor:
    """One retrieval instance per app session, with isolated in-memory notes."""
    def __init__(self, knowledge_path: Path=LESSONS, max_tokens:int=900, top_k:int=3, lessons_data=None):
        if type(top_k) is not int or not 1<=top_k<=8:raise ValueError('top_k must be 1–8.')
        self.lessons=lessons_data if lessons_data is not None else load_lessons(knowledge_path)
        self.context=ContextManager(max_tokens=max_tokens,system_reserve=100,response_reserve=200)
        self.rag=RAGSystem(context_manager=self.context,top_k=top_k,min_similarity=.035)
        self.rag.ingest(self.lessons,preserve_chunks=True)
        self.context.ingest_chunks(self.rag.chunks)
        self.notes=[]
        self.events=[]
        self.top_k=top_k

    def log(self,kind:str):
        self.events.append({'kind':kind,'at':datetime.now(timezone.utc).isoformat()})

    def add_note(self,note:str):
        if not isinstance(note,str) or not note.strip() or len(note.strip())>300:
            raise ValueError('Notes must contain 1–300 characters.')
        if CONTACT_PII.search(note):raise ValueError('Please remove email addresses and phone numbers.')
        if len(self.notes)>=100:raise ValueError('Maximum 100 notes per session.')
        self.notes.append(note.strip())
        self.log('note_saved')
        return len(self.notes)

    def search_notes(self,term:str):
        if not isinstance(term,str) or not term.strip():raise ValueError('Enter a search term.')
        return [n for n in self.notes if term.casefold().strip() in n.casefold()][:10]

    def reply(self,message:str,top_k:int|None=None)->dict:
        if not isinstance(message,str) or not message.strip():raise ValueError('Enter a question.')
        if len(message)>1200:raise ValueError('Message must be at most 1,200 characters.')
        if CONTACT_PII.search(message):
            self.log('pii_blocked')
            return {'answer':'Please remove personal contact details before sending your question.', 'mode':'blocked','sources':[]}
        if any(x.search(message) for x in BAD_INSTRUCTIONS):
            self.log('injection_blocked')
            return {'answer':'I cannot follow requests to override trusted instructions.', 'mode':'blocked','sources':[]}
        lower=message.casefold().strip()
        if lower.startswith(('calculate:', 'calc:')):
            r=safe_calculate(message.split(':',1)[1]);self.log('calculator')
            return {'answer':f'Result: {r}', 'mode':'calculator','sources':[]}
        if lower.startswith(('save note:', 'remember:')):
            n=self.add_note(message.split(':',1)[1]);return {'answer':f'Note saved. You have {n} session notes.', 'mode':'memory','sources':[]}
        if lower.startswith('search memory:'):
            matches=self.search_notes(message.split(':',1)[1]);self.log('memory_search')
            return {'answer':('Matching notes:\n'+'\n'.join('• '+n for n in matches)) if matches else 'No matching session notes.', 'mode':'memory','sources':[]}
        if lower in ('time','what time is it?','date','today'):
            self.log('time')
            return {'answer':'Server UTC time: '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 'mode':'time','sources':[]}
        if lower in ('hi','hello','sannu'):
            self.log('greeting')
            return {'answer':'Hello! Ask about Python, online safety, data analysis, or use Calculate: 12 * 4.', 'mode':'greeting','sources':[]}
        matches=self.rag.retrieve(message,top_k=top_k or self.top_k)
        if not matches:
            self.log('no_evidence')
            return {'answer':'I could not find a relevant answer in the available lessons. Try asking about Python, SQL, RAG or digital safety.', 'mode':'no_evidence','sources':[]}
        # Only extract text from approved lesson materials; do not invent free-form LLM facts.
        lines=[]; citations=[]
        for m in matches:
            source=m['source']
            citations.append(source)
            lines.append(f"**{m['metadata'].get('title','Lesson')}** (source: {source})\n{m['text']}")
        self.log('rag')
        return {'answer':'Relevant lesson excerpts:\n\n'+'\n\n'.join(lines), 'mode':'rag','sources':citations}

QUIZ = [
    {'q':'Which Python function displays text?','options':['print()','open()','len()'],'correct':'print()', 'reason':'print() displays output.'},
    {'q':'What does SQL SELECT do?','options':['Deletes a database','Retrieves rows','Encrypts files'],'correct':'Retrieves rows','reason':'SELECT reads rows from a table.'},
    {'q':'What is a common sign of phishing?','options':['An urgent request for your password','A verified school lesson','A local saved note'],'correct':'An urgent request for your password','reason':'Unexpected password requests are a phishing warning sign.'},
    {'q':'What does RAG retrieve?','options':['Relevant source passages','A random password','A video driver'],'correct':'Relevant source passages','reason':'RAG searches evidence to support responses.'},
    {'q':'What is a digital twin?','options':['A representation of a real person/system','A second phone','A spreadsheet format'],'correct':'A representation of a real person/system','reason':'Digital twins are virtual representations.'},
]

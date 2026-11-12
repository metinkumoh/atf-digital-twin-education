"""Week 4.1 Challenge: Digital Twin Learning Studio — Streamlit frontend.

Run: python -m streamlit run app.py
Offline by default. Uses real Week 2.2 ContextManager and Week 2.4 RAGSystem.
Optional Week 1 LLM adapter remains unconnected; no invented model integration.
"""
from __future__ import annotations
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
from tutor_backend import Tutor, QUIZ, LESSONS, load_lessons
from deployment_utils import add_duration, recent_latency_stats, paginate
from ai_provider import read_api_key, enabled, allow_request, generate_grounded_reply, DEFAULT_MODEL

@st.cache_data(ttl=3600, show_spinner=False)
def cached_lesson_data():
    """Cache public, read-only lesson records, not private conversations/notes."""
    return load_lessons()

st.set_page_config(page_title='Digital Twin Learning Studio',page_icon='🎓',layout='wide',initial_sidebar_state='expanded')
LOGGER=logging.getLogger('digital_twin_ui')

WORDS={
 'English':{
  'chat':'Chat','learn':'Learn','quiz':'Quiz','notes':'My notes','dashboard':'Dashboard','settings':'Preferences',
  'name':'Display name','language':'Language / Harshe','theme':'Appearance','text_size':'Reading size',
  'intro':'Your practical AI and digital-skills learning companion','ask':'Ask about Python, SQL, RAG, or online safety…',
  'clear':'Clear conversation','confirm':'I understand the chat history will be cleared',
  'export':'Export conversation (JSON)','note':'New note','save':'Save note','search':'Search saved notes',
  'start':'Start with a topic','knowledge':'Lesson library','lesson_note':'Learning content is a demonstration curriculum, not an official national syllabus.',
  'quiz_intro':'Practice what you learned','check':'Check answer','reset':'Restart quiz',
  'no_messages':'No messages yet. Ask a question below.','your_stats':'Your session activity',
  'source':'Evidence sources','privacy':'Notes and chats stay in this browser session; exported files are saved only if you download them.',
  'voice':'Record audio (optional)','voice_note':'Recording is supported when available, but automatic speech transcription is not connected.',
 },
 'Hausa':{
  'chat':'Tattaunawa','learn':'Darussa','quiz':'Tambayoyin gwaji','notes':'Bayanan kula','dashboard':'Rahoto','settings':'Saituna',
  'name':'Sunan nuni','language':'Harshe','theme':'Launin allo','text_size':'Girman rubutu',
  'intro':'Abokin koyo na fasahar kwamfuta da AI','ask':'Tambaya kan Python, SQL, RAG, ko tsaron intanet…',
  'clear':'Goge tattaunawa','confirm':'Na amince a goge tarihin tattaunawa',
  'export':'Sauke tattaunawa (JSON)','note':'Sabon bayani','save':'Ajiye bayani','search':'Nemo bayanai',
  'start':'Zabi darasi','knowledge':'Dakin karatu','lesson_note':'Wannan darasi na gwaji ne; ba manhajar gwamnati ta hukuma ba.',
  'quiz_intro':'Gwada iliminka','check':'Duba amsa','reset':'Sake farawa',
  'no_messages':'Babu sako tukuna. Yi tambaya a kasa.','your_stats':'Ayyukan wannan zama',
  'source':'Tushen bayani','privacy':'Bayanan wannan zama suna nan na dan lokaci; ajiye su da kanka idan ana bukata.',
  'voice':'Dauki sauti (na zabi)','voice_note':'Ana iya daukar sauti, amma ba a hada fasahar fassara magana zuwa rubutu ba.',
 }
}


def initialize():
    d={'messages':[],'profile':'','language':'English','appearance':'Dark','reading':'Normal',
       'top_k':3,'section':'Chat','request_durations':[],'quiz_index':0,'quiz_score':0,'quiz_done':False,'quiz_checked':False,'ai_request_times':[]}
    for k,v in d.items():
        if k not in st.session_state:st.session_state[k]=v
    if 'tutor' not in st.session_state:
        st.session_state.tutor=Tutor(lessons_data=cached_lesson_data())

initialize()
tutor=st.session_state.tutor
T=WORDS[st.session_state.language]

# Static styling only; no user-supplied HTML or CSS.
dark=st.session_state.appearance=='Dark'
fg='#F2F6FF' if dark else '#172239'
muted='#A8B5CF' if dark else '#52637D'
bg='#0B1220' if dark else '#F5F8FD'
panel='#111D32' if dark else '#FFFFFF'
border='#263751' if dark else '#DCE4F0'
base={'Compact':'0.94rem','Normal':'1.0rem','Large':'1.13rem'}[st.session_state.reading]
st.markdown(f'''<style>
.stApp{{background:{bg};color:{fg};}}
.block-container{{max-width:1190px;padding-top:1.45rem;padding-bottom:3rem;}}
section[data-testid="stSidebar"]{{background:{panel};border-right:1px solid {border};}}
html, body, [class*="st-"]{{font-size:{base};}}
h1,h2,h3{{letter-spacing:-.035em;}}
div[data-testid="stMetric"]{{background:{panel};border:1px solid {border};border-radius:16px;padding:17px;}}
div[data-testid="stChatMessage"]{{border:1px solid {border};border-radius:15px;margin:.35rem 0;}}
.stButton>button[kind="primary"]{{background:#187EBC;border:0;border-radius:11px;}}
[data-testid="stSidebar"] .stButton>button{{border-radius:10px;}}
.hero{{padding:23px 26px;border:1px solid {border};border-radius:20px;background:{panel};margin-bottom:17px;}}
.eyebrow{{color:#48BDCA;font-size:.77rem;text-transform:uppercase;letter-spacing:.14em;font-weight:800;}}
.hero h1{{color:{fg};font-size:clamp(1.7rem,3vw,2.5rem);margin:8px 0 4px;}}
.hero p{{color:{muted};margin:0;}}
@media (max-width:680px){{.block-container{{padding:1rem .75rem 2rem;}} .hero{{padding:18px 16px;}}}}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### 🎓 Learning Studio')
    st.caption('Digital Twin • Week 4.1 challenge')
    st.text_input(T['name'],key='profile',placeholder='Learner')
    st.selectbox(T['language'],['English','Hausa'],key='language')
    st.radio(T['theme'],['Dark','Light'],horizontal=True,key='appearance')
    st.select_slider(T['text_size'],options=['Compact','Normal','Large'],key='reading')
    with st.expander('⚙️ Retrieval settings'):
        st.slider('Evidence passages (top-k)',1,5,key='top_k')
        st.caption('TF-IDF retrieval from bundled lessons; no paid API is used.')
    st.divider()
    st.metric('Messages',len(st.session_state.messages))
    st.metric('Saved notes',len(tutor.notes))
    st.caption(T['privacy'])
    with st.expander('🤖 Optional Gemini AI'):
        gemini_key = read_api_key(st.secrets) if enabled() else ''
        st.checkbox('Generate an AI explanation after lesson retrieval',key='use_ai',disabled=not bool(gemini_key))
        if gemini_key:
            st.caption('Server-side key available. Requests may incur API usage.')
        else:
            st.caption('Offline lesson retrieval enabled. Gemini is disabled or not configured.')
    with st.expander('🗑️ '+T['clear']):
        approved=st.checkbox(T['confirm'],key='clear_confirm')
        if st.button(T['clear'],disabled=not approved,use_container_width=True):
            st.session_state.messages=[]
            st.session_state.clear_confirm=False
            st.rerun()

st.markdown(f'''<div class="hero"><div class="eyebrow">Digital skills • AI learning • Offline-first</div>
<h1>🎓 Digital Twin Learning Studio</h1><p>{T['intro']}</p></div>''',unsafe_allow_html=True)

chat_tab,learn_tab,quiz_tab,note_tab,stats_tab=st.tabs([
    '💬 '+T['chat'],'📚 '+T['learn'],'🧩 '+T['quiz'],'🗒️ '+T['notes'],'📊 '+T['dashboard']])

with chat_tab:
    st.caption('Evidence-backed extracts • Offline calculator • Session notes • Source references')
    if not st.session_state.messages:
        st.info(T['no_messages'])
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            st.caption(msg['at']+' · '+msg.get('mode','message'))
            if msg.get('sources'):
                with st.expander('🔗 '+T['source']):
                    for src in msg['sources']:st.code(src,language=None)
    with st.expander('💡 Quick examples'):
        st.code('What is Python?\nWhat is phishing?\nCalculate: 120 / 4\nSave note: Practice SQL\nSearch memory: SQL',language=None)
    prompt=st.chat_input(T['ask'],max_chars=1200)
    if prompt:
        st.session_state.messages.append({'role':'user','content':prompt,
                                          'at':datetime.now().strftime('%H:%M:%S')})
        try:
            with st.spinner('Searching lessons and checking tools…'):
                start_time=time.perf_counter()
                try:
                    reply=tutor.reply(prompt,top_k=st.session_state.top_k)
                    # AI is optional. Never send private note/tool commands or blocked messages.
                    if (st.session_state.get('use_ai') and gemini_key
                            and reply['mode']=='rag'):
                        allowed, updated = allow_request(st.session_state.ai_request_times)
                        if not allowed:
                            st.info('Gemini session usage limit reached; showing offline lesson excerpts.')
                        else:
                            st.session_state.ai_request_times = updated
                            try:
                                ai_text=generate_grounded_reply(
                                    gemini_key,prompt,reply['answer'],
                                    model=__import__('os').getenv('GEMINI_MODEL',DEFAULT_MODEL))
                                reply['answer']=ai_text+'\n\n*AI-generated study explanation; check the cited lesson sources.*'
                                reply['mode']='gemini_grounded'
                            except Exception:
                                # Provider errors can include account details: do not log raw exception.
                                LOGGER.warning('Gemini request unavailable; offline fallback used')
                                st.warning('AI service unavailable. Displaying offline lesson extracts instead.')
                finally:
                    st.session_state.request_durations=add_duration(
                        st.session_state.request_durations, time.perf_counter()-start_time
                    )
            st.session_state.messages.append({'role':'assistant','content':reply['answer'],
                                              'mode':reply['mode'],'sources':reply['sources'],
                                              'at':datetime.now().strftime('%H:%M:%S')})
        except ValueError as e:
            st.session_state.messages.append({'role':'assistant','content':'Please check your request: '+str(e),
                                              'mode':'validation','at':datetime.now().strftime('%H:%M:%S')})
        except Exception:
            LOGGER.exception('Chat processing failed')
            st.session_state.messages.append({'role':'assistant','content':'The request could not be processed. Please try again.',
                                              'mode':'error','at':datetime.now().strftime('%H:%M:%S')})
        st.rerun()

with learn_tab:
    st.subheader('📚 '+T['knowledge'])
    st.caption(T['lesson_note'])
    topics=sorted(set(item['topic'] for item in tutor.lessons))
    chosen=st.selectbox('Topic / Batu', ['All topics']+topics)
    filtered=[x for x in tutor.lessons if chosen=='All topics' or x['topic']==chosen]
    page_size=4
    page_total=max(1,(len(filtered)+page_size-1)//page_size)
    selected_page=st.number_input('Lesson page / Shafi',1,page_total,1,step=1)
    shown, start, end=paginate(filtered,int(selected_page),page_size)
    for lesson in shown:
        with st.expander(f"{lesson['title']} · {lesson['topic']}"):
            st.write(lesson['text'])
            st.caption('Source: '+lesson['source'])
    st.caption(f"Showing {start + 1 if filtered else 0}–{end} of {len(filtered)} lesson(s). These are authored teaching notes, not a certified national curriculum.")

with quiz_tab:
    st.subheader('🧩 '+T['quiz_intro'])
    i=st.session_state.quiz_index
    if i>=len(QUIZ):
        st.success(f"Quiz complete! Score: {st.session_state.quiz_score}/{len(QUIZ)}")
        if st.button(T['reset']):
            st.session_state.quiz_index=0;st.session_state.quiz_score=0
            st.session_state.quiz_done=False;st.session_state.quiz_checked=False;st.rerun()
    else:
        item=QUIZ[i]
        st.progress(i/len(QUIZ),text=f'Question {i+1} / {len(QUIZ)}')
        st.markdown('#### '+item['q'])
        choice=st.radio('Choose one',item['options'],key=f'quiz_{i}',disabled=st.session_state.quiz_checked)
        if not st.session_state.quiz_checked:
            if st.button(T['check'],type='primary'):
                st.session_state.quiz_checked=True
                if choice==item['correct']:st.session_state.quiz_score+=1
                st.rerun()
        else:
            if choice==item['correct']:st.success('Correct! '+item['reason'])
            else:st.warning(f"Correct answer: {item['correct']}. {item['reason']}")
            if st.button('Next / Na gaba'):
                st.session_state.quiz_index+=1;st.session_state.quiz_checked=False;st.rerun()

with note_tab:
    st.subheader('🗒️ '+T['notes'])
    st.caption(T['privacy'])
    with st.form('note_form',clear_on_submit=True):
        note=st.text_area(T['note'],max_chars=300,placeholder='Practice Python loops this weekend')
        save=st.form_submit_button('💾 '+T['save'])
    if save:
        try:tutor.add_note(note);st.success('Saved to this session.')
        except ValueError as e:st.warning(str(e))
    keyword=st.text_input('🔎 '+T['search'])
    visible=tutor.search_notes(keyword) if keyword.strip() else tutor.notes
    if visible:
        for j,note in enumerate(visible,1):st.write(f'{j}. {note}')
    else:st.info('No matching notes.')
    with st.expander('Delete session notes'):
        if st.checkbox('Confirm deletion of all notes',key='notes_confirm'):
            if st.button('Delete all notes'):
                tutor.notes.clear();tutor.log('notes_cleared');st.rerun()

with stats_tab:
    st.subheader('📊 '+T['your_stats'])
    user_msgs=sum(x['role']=='user' for x in st.session_state.messages)
    sources=sum(bool(x.get('sources')) for x in st.session_state.messages)
    a,b,c=st.columns(3)
    a.metric('Questions',user_msgs)
    b.metric('Source-linked replies',sources)
    c.metric('Notes',len(tutor.notes))
    kinds=Counter(x['kind'] for x in tutor.events)
    if kinds:
        st.bar_chart(kinds)
    else:st.info('Your usage chart will appear after you interact with the tutor.')
    metrics=recent_latency_stats(st.session_state.request_durations)
    st.markdown('**Lightweight session monitoring**')
    if metrics['count']:
        m1,m2,m3=st.columns(3)
        m1.metric('Measured requests',metrics['count'])
        m2.metric('Mean backend time',f"{metrics['mean']:.3f}s")
        m3.metric('Slowest backend time',f"{metrics['max']:.3f}s")
        st.caption('Measures backend processing in this browser session only; no personal message contents are logged.')
    else:
        st.caption('Response-time metrics appear after you ask a question.')
    st.markdown('**Export active-session conversation**')
    content=json.dumps({'exported_at_utc':datetime.now(timezone.utc).isoformat(),
                        'language':st.session_state.language,'messages':st.session_state.messages},
                        ensure_ascii=False,indent=2)
    st.download_button('⬇️ '+T['export'],data=content,file_name='digital_twin_chat.json',mime='application/json')
    with st.expander('🎙️ '+T['voice']):
        st.caption(T['voice_note'])
        if hasattr(st,'audio_input'):
            recording=st.audio_input('Record a clip')
            if recording:st.audio(recording)
        else:st.info('Update Streamlit to use audio recording in supported browsers.')
    with st.expander('Accessibility / Samun dama'):
        st.write('• Keyboard-friendly standard Streamlit controls')
        st.write('• Adjustable text size in the sidebar')
        st.write('• Dark/light appearance choices')
        st.write('• Text-based alternatives; no audio required')

st.divider()
st.caption('Learning demonstration • English/Hausa UI • Offline TF-IDF RAG • Optional Gemini via server secret • No external tracking by this app')

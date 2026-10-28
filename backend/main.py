import os, re, math, uuid
from collections import Counter
from io import BytesIO
from typing import TypedDict
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title='ContextIQ • RAG Knowledge Assistant')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
documents = {}
STOP = set('the and for with this that from have are was were into about what where when which how does can you your its their our'.split())
def tokens(s): return [w for w in re.findall(r'[a-z0-9]+',s.lower()) if w not in STOP]
def chunks(text, size=850, overlap=120):
    text = re.sub(r'\s+', ' ', text).strip()
    return [text[i:i+size] for i in range(0,len(text),size-overlap) if text[i:i+size].strip()]
def retrieve(question, limit=4):
    q = Counter(tokens(question)); ranked=[]
    for d in documents.values():
        for i,chunk in enumerate(d['chunks']):
            ct=Counter(tokens(chunk)); score=sum((1+math.log(1+ct[t]))*v for t,v in q.items() if ct[t])
            if score: ranked.append((score, {'document':d['name'],'chunk':i+1,'excerpt':chunk[:450], 'text':chunk}))
    return [x for _,x in sorted(ranked,key=lambda x:x[0],reverse=True)[:limit]]
class State(TypedDict):
    question:str
    sources:list
    answer:str
    mode:str
def retrieval_node(state): return {'sources':retrieve(state['question'])}
def answer_node(state):
    sources=state['sources']; question=state['question']; key=os.getenv('OPENAI_API_KEY','').strip()
    if not sources: return {'answer':'I could not find relevant evidence in the uploaded documents. Upload a document or try a different question.', 'mode':'retrieval'}
    if key:
        try:
            from openai import OpenAI
            context='\n\n'.join(f"[{i}] {s['document']} (chunk {s['chunk']}): {s['text']}" for i,s in enumerate(sources,1))
            result=OpenAI(api_key=key).chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),temperature=0.1,messages=[{'role':'system','content':'Answer only from supplied context. If evidence is insufficient, say so. Cite source numbers such as [1]. Be concise.'},{'role':'user','content':f'Context:\n{context}\n\nQuestion: {question}'}])
            return {'answer':result.choices[0].message.content or 'No answer generated.','mode':'openai'}
        except Exception as exc:
            return {'answer':f'AI generation unavailable ({type(exc).__name__}). Relevant passages are shown below.', 'mode':'retrieval'}
    return {'answer':'Relevant evidence found. Add OPENAI_API_KEY to enable a synthesized AI answer. Review the cited excerpts below.', 'mode':'retrieval'}
flow=StateGraph(State);flow.add_node('retrieve',retrieval_node);flow.add_node('answer',answer_node);flow.add_edge(START,'retrieve');flow.add_edge('retrieve','answer');flow.add_edge('answer',END);graph=flow.compile()
class Query(BaseModel): question:str
@app.get('/api/health')
def health(): return {'status':'ok','documents':len(documents),'ai_enabled':bool(os.getenv('OPENAI_API_KEY'))}
@app.get('/api/documents')
def list_documents(): return [{'id':k,'name':v['name'],'chunks':len(v['chunks']),'characters':v['characters']} for k,v in documents.items()]
@app.post('/api/upload')
async def upload(file:UploadFile=File(...)):
    data=await file.read()
    if len(data)>8*1024*1024: raise HTTPException(413,'Maximum file size is 8 MB')
    name=file.filename or 'document'
    if name.lower().endswith('.pdf'):
        try: text='\n'.join(page.extract_text() or '' for page in PdfReader(BytesIO(data)).pages)
        except Exception: raise HTTPException(400,'Could not read PDF')
    elif name.lower().endswith(('.txt','.md')): text=data.decode('utf-8',errors='replace')
    else: raise HTTPException(400,'Upload a PDF, TXT, or MD file')
    if not text.strip(): raise HTTPException(400,'No extractable text found')
    ident=str(uuid.uuid4()); cs=chunks(text); documents[ident]={'name':name,'chunks':cs,'characters':len(text)}
    return {'id':ident,'name':name,'chunks':len(cs),'characters':len(text)}
@app.delete('/api/documents/{ident}')
def delete(ident:str):
    if ident not in documents: raise HTTPException(404,'Not found')
    del documents[ident];return {'deleted':ident}
@app.post('/api/chat')
def chat(payload:Query):
    if not payload.question.strip(): raise HTTPException(400,'Question required')
    result=graph.invoke({'question':payload.question,'sources':[],'answer':'','mode':''})
    return {'answer':result['answer'],'mode':result['mode'],'sources':[{k:v for k,v in s.items() if k!='text'} for s in result['sources']]}

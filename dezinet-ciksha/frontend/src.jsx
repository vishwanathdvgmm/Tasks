import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = 'http://localhost:8000';
function App() {
  const [tenant, setTenant] = useState('dezinet-demo');
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [status, setStatus] = useState('Ready');
  const [sources, setSources] = useState([]);
  const [session] = useState(() => 'session-' + Math.random().toString(36).slice(2,10));
  const headers = {'X-Tenant-ID': tenant};
  async function upload(e) {
    e.preventDefault();
    if (!file) return;
    setStatus('Indexing document…');
    const form = new FormData(); form.append('file', file);
    try {
      const res = await fetch(`${API}/api/documents`, {method:'POST', headers, body:form});
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setStatus(`Indexed ${data.chunks_indexed} chunks from ${data.filename}`);
    } catch(err) { setStatus(err.message); }
  }
  async function ask(e) {
    e.preventDefault(); if (!question.trim()) return;
    setAnswer(''); setSources([]); setStatus('Searching and generating…');
    try {
      const res = await fetch(`${API}/api/chat/stream`, {
        method:'POST', headers:{...headers, 'Content-Type':'application/json'},
        body:JSON.stringify({session_id:session, question})
      });
      if (!res.ok || !res.body) throw new Error('Chat request failed');
      const reader = res.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const {value, done} = await reader.read(); if(done) break;
        buffer += decoder.decode(value, {stream:true});
        const events = buffer.split('\n\n'); buffer = events.pop() || '';
        for (const event of events) {
          const lines = event.split('\n');
          const type = lines.find(l=>l.startsWith('event:'))?.slice(6).trim();
          const data = lines.find(l=>l.startsWith('data:'))?.slice(5).trim();
          if(!data) continue;
          const payload = JSON.parse(data);
          if(type==='metadata') setSources(payload.sources || []);
          if(type==='token') setAnswer(prev=>prev+payload.text);
          if(type==='error') throw new Error(payload.message);
        }
      }
      setStatus('Answer complete');
    } catch(err) { setStatus(err.message); }
  }
  async function search() {
    if (!question.trim()) return;
    setStatus('Running hybrid search…');
    try {
      const res = await fetch(`${API}/api/search`, {method:'POST', headers:{...headers,'Content-Type':'application/json'}, body:JSON.stringify({query:question,top_k:5})});
      const data = await res.json(); if(!res.ok) throw new Error(data.detail || 'Search failed');
      setSources(data.results.map((r,i)=>({source:i+1,document_id:r.document_id,chunk_index:r.chunk_index,preview:r.content})));
      setAnswer(data.results.map((r,i)=>`[Source ${i+1}] ${r.content}`).join('\n\n'));
      setStatus(`Hybrid search complete · ${data.latency_ms} ms`);
    } catch(err) { setStatus(err.message); }
  }
  return <main className="shell">
    <header><div className="mark">C</div><div><p className="eyebrow">DEZINET · KNOWLEDGE PLATFORM</p><h1>CIKSHA <span>AI Knowledge Engine</span></h1></div><div className="status"><i/> {status}</div></header>
    <section className="intro"><p className="eyebrow">ENTERPRISE SEARCH / RAG</p><h2>Find answers across your knowledge.</h2><p>Upload internal documents, search semantically and lexically, and get grounded answers with source references.</p></section>
    <div className="grid">
      <section className="panel">
        <h3>01 / Workspace</h3><label>Tenant ID</label><input value={tenant} onChange={e=>setTenant(e.target.value)} placeholder="your-team-id"/>
        <h3 className="spaced">02 / Ingest knowledge</h3><form onSubmit={upload}><input type="file" accept=".pdf,.md,.markdown,.html,.htm,.txt" onChange={e=>setFile(e.target.files[0])}/><button>Upload & index</button></form>
        <p className="hint">PDF, Markdown, HTML, TXT · 15 MB max</p>
        <div className="security"><strong>Tenant scoped</strong><p>Search and session keys are scoped by tenant. The demo tenant header is not authentication.</p></div>
      </section>
      <section className="panel mainpanel">
        <h3>03 / Ask your knowledge base</h3><form onSubmit={ask}><textarea value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question grounded in your uploaded documents…" rows="4"/><div className="actions"><button type="button" className="secondary" onClick={search}>Hybrid search</button><button>Ask CIKSHA ↗</button></div></form>
        <div className="answer"><div className="answerhead"><span>RESPONSE</span><span>{answer ? 'GROUNDING ENABLED' : 'AWAITING QUERY'}</span></div><pre>{answer || 'Your answer will appear here, with source references.'}</pre></div>
        {!!sources.length && <div className="sources"><h4>Retrieved sources</h4>{sources.map((s,i)=><div className="source" key={i}><b>[Source {s.source || i+1}]</b><span>Document {s.document_id} · chunk {s.chunk_index}</span>{s.preview && <p>{s.preview}</p>}</div>)}</div>}
      </section>
    </div>
    <footer><span>CIKSHA CAPSTONE · LOCAL DEVELOPMENT</span><span>API <a href="http://localhost:8000/docs" target="_blank">OpenAPI docs ↗</a></span></footer>
  </main>
}
createRoot(document.getElementById('root')).render(<App/>);

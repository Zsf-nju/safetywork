// Treat imported backups as data, not markup or executable configuration.
export function validateSchema(b) {
  const fail = message => { throw new Error('Invalid backup: '+message); };
  const text = (v, label) => { if(typeof v!=='string')fail(label+' must be text'); };
  const list = (v, label) => { if(!Array.isArray(v))fail(label+' must be a list'); };
  const identifier = v => { if(typeof v!=='string'||!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(v))fail('invalid record identifier'); };
  const unique = values => { if(new Set(values).size!==values.length)fail('duplicate identifiers'); };
  const date = v => { text(v,'date');if(v&&!/^\d{4}-\d{2}-\d{2}$/.test(v))fail('invalid date'); };
  const record = (r,fields) => { if(!r||typeof r!=='object')fail('invalid record');identifier(r.id);for(const f of fields)text(r[f],f); };
  if(!b||b.format!=='safetywork-backup'||b.version!==1||!b.state||b.state.version!==1)fail('unsupported format');
  const s=b.state;
  for(const key of ['projects','papers','updates'])list(s[key],key);list(b.pdfs,'PDF files');
  unique(s.projects.map(p=>p.id));unique(s.papers.map(p=>p.id));unique(s.updates.map(u=>u.id));unique(b.pdfs.map(p=>p.id));
  const stages=new Set();
  for(const p of s.projects){
    record(p,['title','direction','goal','createdAt']);date(p.start);date(p.due);list(p.stages,'milestones');
    if(typeof p.archived!=='boolean')fail('invalid archive flag');
    for(const a of p.stages){
      record(a,['title','goal','notes','overleaf']);date(a.start);date(a.due);if(stages.has(a.id))fail('duplicate milestone');stages.add(a.id);
      if(!['papers','ideas','bench','algorithm','experiments','writing','custom'].includes(a.type))fail('unknown tool');
      if(!['planned','in progress','done','blocked'].includes(a.status))fail('unknown status');
      for(const key of ['nodes','edges','versions','checks']){list(a[key],key);unique(a[key].map(x=>x.id));}
      for(const n of a.nodes){record(n,['title','detail','kind']);if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||n.x<0||n.x>850||n.y<0||n.y>400)fail('board position is out of range');}
      for(const e of a.edges){identifier(e.id);if(!a.nodes.some(n=>n.id===e.from)||!a.nodes.some(n=>n.id===e.to))fail('a connection is missing a node');}
      for(const v of a.versions)record(v,['name','code','notes','at']);
      for(const c of a.checks){record(c,['text']);if(typeof c.done!=='boolean')fail('invalid checklist item');}
      if(!a.table)fail('missing table');list(a.table.columns,'columns');list(a.table.rows,'rows');unique(a.table.rows.map(r=>r.id));
      if(!a.table.columns.length)fail('table has no columns');a.table.columns.forEach(v=>text(v,'column'));
      for(const r of a.table.rows){identifier(r.id);list(r.cells,'cells');if(r.cells.length!==a.table.columns.length)fail('row size does not match columns');r.cells.forEach(v=>text(v,'cell'));}
    }
  }
  for(const p of s.papers){record(p,['projectId','stageId','title','authors','year','status','feelings','findings','filename','addedAt']);if(!['To read','Reading','Read'].includes(p.status)||typeof p.hasPdf!=='boolean')fail('invalid paper');}
  for(const u of s.updates){record(u,['projectId','title','body','at']);if(typeof u.manual!=='boolean')fail('invalid journal entry');}
}

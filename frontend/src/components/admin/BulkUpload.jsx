import {useState,useRef,useEffect} from 'react';
import {Link} from 'react-router-dom';
import {FolderUp,ImagePlus,Music2,X,Loader2,Check,CircleAlert,Upload,RotateCcw} from 'lucide-react';
import {toast} from 'sonner';
import {api,errorText} from '../../lib/api';
import {readTags,expandFiles,cleanName,toDate,MAX_AUDIO} from '../../lib/tags';
import {Button} from '../ui/button';
const initialDefaults={artist:'FLASHUBZ',album:'',genre:'',language:'',published:true,download_enabled:false};
const derive=(tags,file,d)=>({name:tags.title||cleanName(file.name),artist:d.artist||tags.artist||'',album:tags.album||d.album,genre:tags.genre||d.genre,language:d.language,release_date:toDate(tags.year)});
const size=bytes=>bytes>1024*1024?`${(bytes/1024/1024).toFixed(1)} MB`:`${Math.round(bytes/1024)} KB`;
let counter=0;

const Defaults=({d,onChange,cover,coverUrl,onCover,rights,setRights,disabled})=><section className="bulk-defaults" data-testid="bulk-defaults"><span className="form-section-title">01 / SHARED DETAILS · APPLIED TO EVERY SONG UNLESS YOU EDIT A ROW</span><div className="fields-grid">{[['artist','ARTIST','FLASHUBZ'],['album','ALBUM','Optional'],['genre','GENRE','Optional'],['language','LANGUAGE','Optional']].map(([key,label,ph])=><label key={key} htmlFor={`bulk-${key}`}>{label}<input id={`bulk-${key}`} data-testid={`bulk-default-${key}`} value={d[key]} placeholder={ph} maxLength={key==='artist'||key==='album'?160:80} disabled={disabled} onChange={e=>onChange({...d,[key]:e.target.value})}/></label>)}</div><div className="bulk-defaults-row"><div className="bulk-shared-cover"><label className={`file-drop ${cover?'file-selected':''}`} htmlFor="bulk-cover-file">{coverUrl?<img src={coverUrl} alt="Shared cover preview"/>:<ImagePlus size={18} strokeWidth={1}/>}<strong data-testid="bulk-cover-name">{cover?cover.name:'Shared cover for songs without embedded art'}</strong><input id="bulk-cover-file" data-testid="bulk-cover-file" type="file" accept="image/png,image/jpeg,image/webp" disabled={disabled} onChange={e=>onCover(e.target.files[0]||null)}/></label>{cover&&<button type="button" className="bulk-clear" data-testid="bulk-cover-clear" aria-label="Remove shared cover" onClick={()=>onCover(null)}><X size={14}/></button>}</div><label className="bulk-toggle"><input type="checkbox" data-testid="bulk-published" checked={d.published} disabled={disabled} onChange={e=>onChange({...d,published:e.target.checked})}/>Publish immediately</label><label className="bulk-toggle"><input type="checkbox" data-testid="bulk-download-enabled" checked={d.download_enabled} disabled={disabled} onChange={e=>onChange({...d,download_enabled:e.target.checked})}/>Enable downloads</label>{d.download_enabled&&<label className="bulk-toggle rights"><input type="checkbox" data-testid="bulk-rights-confirmation" checked={rights} disabled={disabled} onChange={e=>setRights(e.target.checked)}/>I own these recordings or have permission to distribute them.</label>}</div></section>;

const Row=({row,index,coverUrl,onEdit,onRemove,busy})=>{
 const thumb=row.tags.picture||coverUrl;
 const locked=busy||row.status==='done';
 return <div className={`bulk-row status-${row.status}`} data-testid={`bulk-row-${index}`}>{thumb?<img className="bulk-thumb" src={thumb} alt=""/>:<span className="bulk-thumb"><Music2 size={16} strokeWidth={1}/></span>}{['name','artist','album','genre'].map(key=><input key={key} data-testid={`bulk-row-${index}-${key}`} aria-label={`${key} for ${row.file.name}`} value={row.values[key]} placeholder={key==='name'||key==='artist'?`${key} *`:key} disabled={locked} onChange={e=>onEdit(row.key,key,e.target.value)}/>)}<span className="bulk-meta"><span>{row.file.name.split('.').pop().toUpperCase()}</span><span>{size(row.file.size)}</span></span><span className={`bulk-status ${row.status}`} data-testid={`bulk-row-${index}-status`}>{row.status==='reading'&&<><Loader2 size={12} className="spin"/>Reading tags</>}{row.status==='ready'&&<>Ready{row.tags.title?' · tagged':''}</>}{row.status==='uploading'&&<><span>Uploading {row.progress}%</span><span className="bulk-progress"><i style={{width:`${row.progress}%`}}/></span></>}{row.status==='done'&&<><Check size={12}/>{row.song?.published?'Published':'Saved as draft'}</>}{row.status==='error'&&<><CircleAlert size={12}/>{row.error}</>}</span><button type="button" className="bulk-clear" data-testid={`bulk-row-${index}-remove`} aria-label={`Remove ${row.file.name}`} disabled={busy} onClick={()=>onRemove(row.key)}><X size={14}/></button></div>;
};

export default function BulkUpload(){
 const [rows,setRows]=useState([]),[defaults,setDefaults]=useState(initialDefaults),[cover,setCover]=useState(null),[coverUrl,setCoverUrl]=useState(''),[rights,setRights]=useState(false),[busy,setBusy]=useState(false),[dragging,setDragging]=useState(false),[error,setError]=useState('');
 const coverRef=useRef({file:null,id:''}),rowsRef=useRef(rows);rowsRef.current=rows;
 useEffect(()=>()=>{rowsRef.current.forEach(r=>r.tags.picture&&URL.revokeObjectURL(r.tags.picture));},[]);
 const patch=(key,fn)=>setRows(rs=>rs.map(r=>r.key===key?fn(r):r));
 const addFiles=async list=>{
  setError('');
  let files;try{files=await expandFiles(Array.from(list));}catch{setError('That ZIP could not be read. Please check the archive and try again.');return;}
  if(!files.length){setError('No supported audio found. Add MP3, WAV, FLAC, OGG, M4A files or a ZIP containing them.');return;}
  const fresh=files.map(file=>({key:`r${++counter}`,file,tags:{},touched:new Set(),values:derive({},file,defaults),progress:0,error:'',song:null,status:file.size>MAX_AUDIO?'error':'reading'}));
  fresh.forEach(r=>{if(r.status==='error')r.error='Larger than 100 MB';});
  setRows(rs=>[...rs,...fresh]);
  for(const r of fresh){if(r.status==='error')continue;const tags=await readTags(r.file);patch(r.key,old=>({...old,tags,status:'ready',values:derive(tags,old.file,defaults)}));}
 };
 const changeDefaults=d=>{setDefaults(d);setRows(rs=>rs.map(r=>{const next=derive(r.tags,r.file,d);return {...r,values:{...r.values,...Object.fromEntries(Object.entries(next).filter(([k])=>!r.touched.has(k)))}};}));};
 const changeCover=file=>{if(file&&file.size>10*1024*1024){setError('Cover must be smaller than 10 MB');return;}if(coverUrl)URL.revokeObjectURL(coverUrl);setCover(file);setCoverUrl(file?URL.createObjectURL(file):'');};
 const edit=(key,field,value)=>patch(key,r=>{const touched=new Set(r.touched);touched.add(field);return {...r,touched,values:{...r.values,[field]:value}};});
 const remove=key=>setRows(rs=>rs.filter(r=>{if(r.key===key&&r.tags.picture)URL.revokeObjectURL(r.tags.picture);return r.key!==key;}));
 const start=async()=>{
  setError('');
  const pending=rows.filter(r=>r.status==='ready');
  if(!pending.length){setError('Add at least one audio file to upload.');return;}
  if(pending.some(r=>!r.values.name.trim()||!r.values.artist.trim())){setError('Every song needs a name and an artist before uploading.');return;}
  if(defaults.download_enabled&&!rights){setError('Confirm that you have permission to distribute these recordings.');return;}
  setBusy(true);
  let coverId='';
  if(cover){
   if(coverRef.current.file===cover)coverId=coverRef.current.id;
   else{try{const form=new FormData();form.append('cover',cover);coverId=(await api.post('/admin/covers',form)).data.id;coverRef.current={file:cover,id:coverId};}catch(e){setError(errorText(e));setBusy(false);return;}}
  }
  const queue=[...pending];let done=0,failed=0;
  const worker=async()=>{for(let row=queue.shift();row;row=queue.shift()){
   patch(row.key,r=>({...r,status:'uploading',progress:0}));
   const form=new FormData();
   form.append('metadata',JSON.stringify({...row.values,name:row.values.name.trim(),artist:row.values.artist.trim(),lyrics:'',description:'',published:defaults.published,download_enabled:defaults.download_enabled}));
   form.append('audio',row.file);if(coverId)form.append('cover_file_id',coverId);
   try{const r=await api.post('/admin/songs',form,{onUploadProgress:e=>patch(row.key,old=>({...old,progress:Math.min(99,Math.round(e.loaded/(e.total||e.loaded)*100))}))});patch(row.key,old=>({...old,status:'done',progress:100,song:r.data}));done++;}
   catch(e){patch(row.key,old=>({...old,status:'error',error:errorText(e)}));failed++;}
  }};
  await Promise.all([worker(),worker()]);
  setBusy(false);
  if(failed)toast.error(`${done} uploaded, ${failed} failed. Fix the rows marked in red and retry.`);else toast.success(defaults.published?`${done} songs published. Your new music folders are ready.`:`${done} songs saved as drafts.`);
 };
 const retry=()=>setRows(rs=>rs.map(r=>r.status==='error'&&r.file.size<=MAX_AUDIO?{...r,status:'ready',error:''}:r));
 const counts=rows.reduce((c,r)=>({...c,[r.status]:(c[r.status]||0)+1}),{});
 const onDrop=e=>{e.preventDefault();setDragging(false);if(!busy)addFiles(e.dataTransfer.files);};
 return <div data-testid="bulk-upload"><label className={`file-drop bulk-drop ${dragging?'is-dragging':''}`} htmlFor="bulk-audio-files" onDragOver={e=>{e.preventDefault();setDragging(true);}} onDragLeave={()=>setDragging(false)} onDrop={onDrop}><FolderUp size={32} strokeWidth={1}/><strong>Drop many songs here, or click to choose</strong><span>MP3, WAV, FLAC, OGG, M4A up to 100 MB each · or a ZIP full of songs · one 3D folder per song</span><input id="bulk-audio-files" data-testid="bulk-audio-files" type="file" multiple accept=".mp3,.wav,.flac,.ogg,.m4a,.zip" disabled={busy} onChange={e=>{addFiles(e.target.files);e.target.value='';}}/></label>
  <Defaults d={defaults} onChange={changeDefaults} cover={cover} coverUrl={coverUrl} onCover={changeCover} rights={rights} setRights={setRights} disabled={busy}/>
  {rows.length>0&&<section><span className="form-section-title">02 / {rows.length} SONG{rows.length===1?'':'S'} IN THIS BATCH · EDIT ANY ROW BEFORE UPLOADING</span><div className="bulk-table" data-testid="bulk-table"><div className="bulk-row bulk-head"><span/><span>SONG NAME</span><span>ARTIST</span><span>ALBUM</span><span>GENRE</span><span>FILE</span><span>STATUS</span><span/></div>{rows.map((row,i)=><Row key={row.key} row={row} index={i} coverUrl={coverUrl} onEdit={edit} onRemove={remove} busy={busy}/>)}</div></section>}
  {error&&<p role="alert" className="error" data-testid="bulk-error">{error}</p>}
  <div className="bulk-summary"><p data-testid="bulk-summary">{counts.ready||0} ready · {counts.done||0} uploaded{counts.error?` · ${counts.error} failed`:''}</p><div className="upload-actions">{counts.error>0&&!busy&&<Button variant="outline" type="button" data-testid="bulk-retry" onClick={retry}><RotateCcw size={15}/>Retry failed</Button>}{counts.done>0&&!busy&&<Link className="text-link" data-testid="bulk-view-songs" to="/admin/songs">View songs</Link>}<Button type="button" className="red-button" data-testid="bulk-submit" disabled={busy||!counts.ready} onClick={start}>{busy?<><Loader2 size={16} className="spin"/>Uploading {counts.done||0}/{(counts.done||0)+(counts.uploading||0)+(counts.ready||0)}</>:<><Upload size={16}/>{defaults.published?'PUBLISH':'SAVE'} {counts.ready||0} SONG{counts.ready===1?'':'S'}</>}</Button></div></div></div>;
}

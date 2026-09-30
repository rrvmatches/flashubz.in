import JSZip from 'jszip';
import jsmediatags from 'jsmediatags/dist/jsmediatags.min.js';
export const AUDIO_RE=/\.(mp3|wav|flac|ogg|m4a)$/i;
const TAGGED_RE=/\.(mp3|flac|m4a)$/i;
export const MAX_AUDIO=100*1024*1024;
export const cleanName=name=>name.replace(/\.[^.]+$/,'').replace(/^\s*\d{1,3}\s*[-._)]\s*/,'').replace(/_/g,' ').trim()||name;
export const toDate=year=>{const y=String(year||'').trim();if(/^\d{4}$/.test(y))return `${y}-01-01`;if(/^\d{4}-\d{2}-\d{2}/.test(y))return y.slice(0,10);return '';};
export const readTags=file=>new Promise(resolve=>{
 if(!TAGGED_RE.test(file.name))return resolve({});
 jsmediatags.read(file,{onSuccess:({tags})=>{
  let picture='';
  if(tags.picture?.data?.length){try{picture=URL.createObjectURL(new Blob([new Uint8Array(tags.picture.data)],{type:tags.picture.format||'image/jpeg'}));}catch{picture='';}}
  resolve({title:(tags.title||'').trim(),artist:(tags.artist||'').trim(),album:(tags.album||'').trim(),genre:(tags.genre||'').trim(),year:tags.year||'',picture});
 },onError:()=>resolve({})});
});
export async function expandFiles(list){
 const files=[];
 for(const file of list){
  if(/\.zip$/i.test(file.name)){
   const zip=await JSZip.loadAsync(file);
   for(const entry of Object.values(zip.files)){
    const base=entry.name.split('/').pop();
    if(entry.dir||!AUDIO_RE.test(base)||entry.name.includes('__MACOSX')||base.startsWith('.'))continue;
    const blob=await entry.async('blob');
    files.push(new File([blob],base,{type:blob.type}));
   }
  }else if(AUDIO_RE.test(file.name))files.push(file);
 }
 return files;
}

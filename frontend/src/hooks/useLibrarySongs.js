import {useEffect,useState} from 'react';
import {api,errorText} from '../lib/api';
export const useLibrarySongs=(ids=[])=>{
 const key=JSON.stringify(ids),[songs,setSongs]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{const abort=new AbortController();const ids=JSON.parse(key);setError('');setLoading(true);const chunks=[];for(let i=0;i<ids.length;i+=48)chunks.push(ids.slice(i,i+48));Promise.all(chunks.map(chunk=>api.get('/songs',{params:{ids:chunk.join(','),limit:48},signal:abort.signal}))).then(results=>setSongs(results.flatMap(r=>r.data.songs))).catch(e=>{if(e.code!=='ERR_CANCELED')setError(errorText(e));}).finally(()=>{if(!abort.signal.aborted)setLoading(false);});return()=>abort.abort();},[key]);
 return {songs,loading,error};
};
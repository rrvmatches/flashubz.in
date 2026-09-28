import {useState,useEffect} from 'react';
import {api,errorText} from '../lib/api';
export const useSongs=(params={})=>{
 const key=JSON.stringify(params);const [result,setResult]=useState({songs:[],total:0,pages:0}),[loading,setLoading]=useState(true),[error,setError]=useState(''),[revision,setRevision]=useState(0);
 useEffect(()=>{const controller=new AbortController();setLoading(true);setError('');api.get('/songs',{params:JSON.parse(key),signal:controller.signal}).then(r=>setResult(r.data)).catch(e=>{if(e.code!=='ERR_CANCELED')setError(errorText(e));}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});return()=>controller.abort();},[key,revision]);
 return {...result,loading,error,reload:()=>setRevision(r=>r+1)};
};
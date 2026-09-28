import axios from 'axios';
import { toast } from 'sonner';
export const BASE = process.env.REACT_APP_BACKEND_URL;
export const api = axios.create({baseURL: `${BASE}/api`, withCredentials:true});
let adminCsrf = '';
api.interceptors.response.use(response=>{
 if(response.data?.csrf_token) adminCsrf=response.data.csrf_token;
 if(response.config.url==='/admin/logout') adminCsrf='';
 return response;
});
api.interceptors.request.use(config=>{
 if(adminCsrf && config.url?.startsWith('/admin/') && !['get','head','options'].includes(config.method)) config.headers['X-CSRF-Token']=adminCsrf;
 return config;
});
export const mediaUrl = path => path ? (path.startsWith('/') ? `${BASE}${path}` : path) : '';
export const errorText = e => typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Something went wrong. Please try again.';
export const time = seconds => `${Math.floor((seconds||0)/60)}:${String(Math.floor((seconds||0)%60)).padStart(2,'0')}`;
export async function downloadSong(song) {
  try { const {data}=await api.post(`/songs/${song.id}/download`); const a=document.createElement('a'); a.href=mediaUrl(data.url); a.download=''; document.body.appendChild(a); a.click(); a.remove(); }
  catch(e){toast.error(errorText(e));}
}
export async function shareSong(song) {
  const url=`${BASE}/song/${song.slug}`;
  try { if(navigator.share) await navigator.share({title:`FLASHUBZ — ${song.name}`,url}); else {await navigator.clipboard.writeText(url); toast.success('Song link copied');} }
  catch(e){if(e.name!=='AbortError') toast.error('Could not share this song. Copy the address from your browser.');}
}
export function readSaved(key, fallback) {try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}}
export function saveLocal(key,value){try{localStorage.setItem(key,JSON.stringify(value));}catch{toast.error('Your browser could not save your library. Check available storage.');}}
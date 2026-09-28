import {createContext,useContext,useRef,useState,useEffect,useCallback} from 'react';
import {toast} from 'sonner';
import {api,mediaUrl,readSaved,saveLocal} from '../lib/api';
const MusicContext=createContext(null);
export const useMusic=()=>useContext(MusicContext);

export const MusicProvider=({children})=>{
 const audioRef=useRef(null), analyserRef=useRef(null), contextRef=useRef(null), frequencies=useRef(new Uint8Array(128));
 const [current,setCurrent]=useState(null),[playing,setPlaying]=useState(false),[progress,setProgress]=useState(0),[duration,setDuration]=useState(0);
 const [queue,setQueue]=useState([]),[volume,setVolumeState]=useState(()=>readSaved('flashubz-volume',.7)),[shuffle,setShuffle]=useState(false),[repeat,setRepeat]=useState(false);
 const [favorites,setFavorites]=useState(()=>readSaved('flashubz-favorites',[])),[playlists,setPlaylists]=useState(()=>readSaved('flashubz-playlists',[]));
 const [visitor]=useState(()=>{let id=readSaved('flashubz-visitor',null);if(!id){id=crypto.randomUUID();saveLocal('flashubz-visitor',id);}return id;});
 const initAudio=async()=>{
  if(!contextRef.current){const AC=window.AudioContext||window.webkitAudioContext;if(AC){const ctx=new AC();const analyser=ctx.createAnalyser();analyser.fftSize=256;analyser.smoothingTimeConstant=.82;ctx.createMediaElementSource(audioRef.current).connect(analyser);analyser.connect(ctx.destination);contextRef.current=ctx;analyserRef.current=analyser;}}
  if(contextRef.current?.state==='suspended') await contextRef.current.resume();
 };
 const playSong=async(song,list)=>{
  if(!song?.audio_url){toast.info('The first FLASHUBZ release is on its way.');return;}
  try{
   await initAudio();
   if(list?.length)setQueue(list);
   if(current?.id!==song.id){audioRef.current.src=mediaUrl(song.audio_url);setCurrent(song);setProgress(0);setDuration(song.duration);}
   await audioRef.current.play();
   if(current?.id!==song.id)api.post(`/songs/${song.id}/play`).catch(()=>{});
  }catch(e){if(e.name!=='AbortError')toast.error('Unable to play this audio. Please try again.');}
 };
 const toggle=async()=>{if(!current)return;try{if(audioRef.current.paused){await initAudio();await audioRef.current.play();}else audioRef.current.pause();}catch{toast.error('Playback is unavailable. Please try again.');}};
 const next=(direction=1)=>{if(!queue.length)return;let i=queue.findIndex(s=>s.id===current?.id);if(shuffle&&queue.length>1){let choices=queue.filter(s=>s.id!==current?.id);playSong(choices[Math.floor(Math.random()*choices.length)]);}else playSong(queue[(i+direction+queue.length)%queue.length]);};
 const seek=value=>{if(audioRef.current&&Number.isFinite(duration)){audioRef.current.currentTime=value;setProgress(value);}};
 const setVolume=value=>{setVolumeState(value);saveLocal('flashubz-volume',value);};
 useEffect(()=>{if(audioRef.current)audioRef.current.volume=volume;},[volume]);
 useEffect(()=>{let frame;const tick=()=>{if(analyserRef.current&&playing)analyserRef.current.getByteFrequencyData(frequencies.current);else frequencies.current.fill(0);frame=requestAnimationFrame(tick);};tick();return()=>cancelAnimationFrame(frame);},[playing]);
 const favorite=song=>{const active=!favorites.includes(song.id);const updated=active?[...favorites,song.id]:favorites.filter(id=>id!==song.id);setFavorites(updated);saveLocal('flashubz-favorites',updated);api.post('/favorites/activity',{visitor_id:visitor,song_id:song.id,active}).catch(()=>{});toast.success(active?'Added to your favorites':'Removed from your favorites');};
 const updatePlaylists=useCallback(updater=>setPlaylists(old=>{const next=typeof updater==='function'?updater(old):updater;saveLocal('flashubz-playlists',next);return next;}),[]);
 const createPlaylist=name=>{const p={id:crypto.randomUUID(),name:name.trim(),song_ids:[],created_at:new Date().toISOString()};updatePlaylists(old=>[...old,p]);return p;};
 const addToPlaylist=(id,song)=>{updatePlaylists(old=>old.map(p=>p.id===id?{...p,song_ids:[...new Set([...p.song_ids,song.id])]}:p));toast.success('Added to playlist');};
 return <MusicContext.Provider value={{audioRef,analyserRef,frequencies,current,playing,progress,duration,queue,volume,shuffle,repeat,favorites,playlists,playSong,toggle,next,seek,setVolume,setShuffle,setRepeat,favorite,createPlaylist,updatePlaylists,addToPlaylist}}>
  <audio data-testid="global-audio" ref={audioRef} crossOrigin="anonymous" preload="none" onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onTimeUpdate={()=>setProgress(audioRef.current.currentTime)} onLoadedMetadata={()=>setDuration(audioRef.current.duration)} onEnded={()=>{if(repeat){seek(0);audioRef.current.play().catch(()=>{});}else if(shuffle||queue.findIndex(s=>s.id===current?.id)<queue.length-1)next();else setPlaying(false);}} onError={()=>{setPlaying(false);if(current)toast.error('This audio is currently unavailable.');}} />
  {children}
 </MusicContext.Provider>;
};
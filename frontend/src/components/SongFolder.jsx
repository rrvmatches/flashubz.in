import {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Music2,Play,ArrowUpRight,Heart} from 'lucide-react';
import {useMusic} from '../context/MusicContext';
import {Waveform} from './Waveform';
import {mediaUrl} from '../lib/api';
export const SongFolder=({song,index=0,queue=[]})=>{
 const navigate=useNavigate(),m=useMusic();const [opening,setOpening]=useState(false);
 const open=()=>{setOpening(true);setTimeout(()=>navigate(`/song/${song.slug}`),matchMedia('(prefers-reduced-motion: reduce)').matches?0:420);};
 return <article className={`song-folder-wrap ${opening?'opening':''}`} style={{'--delay':`${index%12*.065}s`}} data-testid={`song-folder-${song.slug}`}><button className="song-folder" data-testid={`open-song-${song.slug}`} onClick={open} aria-label={`Open ${song.name}`}><div className="folder-back"/><div className="folder-art">{song.cover_url?<img src={mediaUrl(song.cover_url)} alt="" loading="lazy"/>:<Music2/>}</div><div className="folder-front"><span className="folder-topline"><Music2 size={16}/><span>FLASHUBZ · AUDIO ARCHIVE</span><ArrowUpRight size={15}/></span><Music2 className="folder-symbol" strokeWidth={1}/><div className="folder-bottom"><span className="folder-number">{String(index+1).padStart(2,'0')} / MUSIC FILE</span><h2 data-testid={`folder-title-${song.slug}`}>{song.name}</h2><Waveform bars={24}/></div></div></button><div className="folder-info"><span data-testid={`folder-artist-${song.slug}`}>{song.artist}</span><div><button data-testid={`folder-favorite-${song.slug}`} aria-label={`Favorite ${song.name}`} className={m.favorites.includes(song.id)?'is-active':''} onClick={()=>m.favorite(song)}><Heart size={15} fill={m.favorites.includes(song.id)?'currentColor':'none'}/></button><button data-testid={`folder-play-${song.slug}`} aria-label={`Play ${song.name}`} onClick={()=>m.playSong(song,queue.length?queue:[song])}><Play size={15}/></button></div></div></article>;
};
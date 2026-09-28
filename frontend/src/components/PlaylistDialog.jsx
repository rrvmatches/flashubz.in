import {useState} from 'react';
import {Plus,ListMusic,Check} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from './ui/dialog';
import {Button} from './ui/button';
import {useMusic} from '../context/MusicContext';
export const PlaylistDialog=({open,onOpenChange,song})=>{
 const m=useMusic();const [name,setName]=useState('');
 const create=e=>{e.preventDefault();if(!name.trim())return;const p=m.createPlaylist(name);if(song)m.addToPlaylist(p.id,song);setName('');onOpenChange(false);};
 return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent data-testid="playlist-dialog" className="app-dialog"><DialogTitle data-testid="playlist-dialog-title">{song?'ADD TO PLAYLIST':'CREATE A PLAYLIST'}</DialogTitle><DialogDescription>Your music. Your own order.</DialogDescription>{song&&<div className="playlist-options">{m.playlists.map(p=><button data-testid={`select-playlist-${p.id}`} key={p.id} onClick={()=>{m.addToPlaylist(p.id,song);onOpenChange(false);}}><ListMusic size={18}/><span>{p.name}</span>{p.song_ids.includes(song.id)?<Check size={16}/>:<Plus size={16}/>}</button>)}</div>}<form onSubmit={create} className="playlist-create"><label htmlFor="playlist-name">NEW PLAYLIST</label><input id="playlist-name" data-testid="playlist-name-input" placeholder="Give your playlist a name" required maxLength="100" value={name} onChange={e=>setName(e.target.value)}/><Button className="red-button" data-testid="create-playlist-submit" type="submit"><Plus size={16}/>{song?'Create & add song':'Create playlist'}</Button></form></DialogContent></Dialog>;
};
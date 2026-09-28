import {Link} from 'react-router-dom';
import {Play,Pause,SkipBack,SkipForward,Volume2,VolumeX,Shuffle,Repeat,Heart,Download,AudioLines} from 'lucide-react';
import {useMusic} from '../context/MusicContext';
import {IconButton,Cover} from './Common';
import {Waveform} from './Waveform';
import {time,downloadSong} from '../lib/api';
export const Player=()=>{
 const m=useMusic();
 if(!m.current)return null;
 return <aside className="global-player" aria-label="Music player" data-testid="global-player">
 <div className="player-song"><Cover song={m.current}/><Link to={`/song/${m.current.slug}`} data-testid="player-song-link"><strong data-testid="player-song-name">{m.current.name}</strong><span data-testid="player-song-artist">{m.current.artist}</span></Link><IconButton label="Favorite song" testId="player-favorite" active={m.favorites.includes(m.current.id)} onClick={()=>m.favorite(m.current)}><Heart fill={m.favorites.includes(m.current.id)?'currentColor':'none'}/></IconButton></div>
 <div className="player-center"><div className="transport"><IconButton label="Shuffle" testId="player-shuffle" active={m.shuffle} onClick={()=>m.setShuffle(!m.shuffle)}><Shuffle/></IconButton><IconButton label="Previous song" testId="player-previous" onClick={()=>m.next(-1)}><SkipBack/></IconButton><button data-testid="player-play-pause" className="play-main" aria-label={m.playing?'Pause':'Play'} onClick={m.toggle}>{m.playing?<Pause size={18} fill="currentColor"/>:<Play size={18} fill="currentColor"/>}</button><IconButton label="Next song" testId="player-next" onClick={()=>m.next()}><SkipForward/></IconButton><IconButton label="Repeat song" testId="player-repeat" active={m.repeat} onClick={()=>m.setRepeat(!m.repeat)}><Repeat/></IconButton></div><div className="progress-row"><span data-testid="player-current-time">{time(m.progress)}</span><input data-testid="player-progress" aria-label="Song progress" type="range" min="0" max={m.duration||1} step=".1" value={Math.min(m.progress,m.duration||1)} onChange={e=>m.seek(Number(e.target.value))} style={{'--progress':`${m.progress/(m.duration||1)*100}%`}}/><span data-testid="player-duration">{time(m.duration)}</span></div></div>
 <div className="player-options"><Waveform bars={20}/><IconButton label={m.volume?'Mute':'Unmute'} testId="player-mute" onClick={()=>m.setVolume(m.volume?0:.7)}>{m.volume?<Volume2/>:<VolumeX/>}</IconButton><input data-testid="player-volume" aria-label="Volume" type="range" min="0" max="1" step=".01" value={m.volume} onChange={e=>m.setVolume(Number(e.target.value))}/>{m.current.download_enabled&&<IconButton label="Download song" testId="player-download" onClick={()=>downloadSong(m.current)}><Download/></IconButton>}</div>
 </aside>;
};
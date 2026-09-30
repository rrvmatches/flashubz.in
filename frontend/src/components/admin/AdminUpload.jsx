import {lazy,Suspense} from 'react';
import {useSearchParams} from 'react-router-dom';
import {Music2,FolderUp} from 'lucide-react';
import {SongForm} from './AdminSongs';
import {Loading} from '../Common';
const BulkUpload=lazy(()=>import('./BulkUpload'));
export default function AdminUpload(){
 const [params,setParams]=useSearchParams();const bulk=params.get('mode')==='bulk';
 return <div><header className="admin-page-heading"><span className="eyebrow">THE MUSIC STARTS HERE</span><h1 data-testid="upload-title">{bulk?'BULK UPLOAD':'UPLOAD SONG'}</h1><p>{bulk?'Many tracks at once. Every file becomes its own 3D folder.':'A new track. A new world to discover.'}</p></header><div className="upload-mode-switch" role="tablist" aria-label="Upload mode"><button type="button" role="tab" aria-selected={!bulk} className={bulk?'':'active'} data-testid="upload-mode-single" onClick={()=>setParams({})}><Music2 size={14}/>SINGLE SONG</button><button type="button" role="tab" aria-selected={bulk} className={bulk?'active':''} data-testid="upload-mode-bulk" onClick={()=>setParams({mode:'bulk'})}><FolderUp size={14}/>BULK UPLOAD</button></div>{bulk?<Suspense fallback={<Loading/>}><BulkUpload/></Suspense>:<SongForm hideHeading/>}</div>;
}

import {useEffect,useState} from 'react';
import {NavLink,useLocation} from 'react-router-dom';
import {ShieldCheck,LayoutDashboard,Music2,Upload,ListMusic,Mic2,Users,Download,ChartNoAxesCombined,Settings,LogOut,LockKeyhole,ArrowRight} from 'lucide-react';
import {api,errorText} from '../lib/api';
import {Button} from '../components/ui/button';
import {Loading} from '../components/Common';
import {SEO} from '../components/SEO';
import AdminDashboard from '../components/admin/AdminDashboard';
import {AdminSongs} from '../components/admin/AdminSongs';
import AdminUpload from '../components/admin/AdminUpload';
import AdminManagement from '../components/admin/AdminManagement';
import '../admin.css';
const navigation=[['','Dashboard',LayoutDashboard],['songs','Songs',Music2],['upload','Upload music',Upload],['playlists','Playlists',ListMusic],['artists','Artists',Mic2],['users','Users',Users],['downloads','Downloads',Download],['analytics','Analytics',ChartNoAxesCombined],['settings','Settings',Settings]];
export default function Admin(){
 const [auth,setAuth]=useState(null),[checking,setChecking]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState(false);const location=useLocation();const section=location.pathname.split('/')[2]||'';
 useEffect(()=>{api.get('/admin/me').then(r=>setAuth(r.data)).catch(()=>setAuth(null)).finally(()=>setChecking(false));},[]);
 const login=async e=>{e.preventDefault();setBusy(true);setError('');try{const r=await api.post('/admin/login',Object.fromEntries(new FormData(e.currentTarget)));setAuth(r.data);}catch(e){setError(errorText(e));}finally{setBusy(false);}};
 const logout=async()=>{try{await api.post('/admin/logout');setAuth(null);}catch(e){setError(errorText(e));}};
 if(checking)return <Loading/>;
 if(!auth)return <div className="admin-login page content-width"><SEO title="Admin Studio"/><div className="login-emblem"><ShieldCheck size={32} strokeWidth={1}/></div><span className="eyebrow">BEHIND THE FREQUENCY</span><h1 data-testid="admin-login-title">THE ADMIN <em>STUDIO</em></h1><p>Private access. Unlimited possibility.</p><form onSubmit={login} data-testid="admin-login-form"><label htmlFor="admin-username">USERNAME</label><input data-testid="admin-username" id="admin-username" name="username" required autoComplete="username" placeholder="Your admin username"/><label htmlFor="admin-password">PASSWORD</label><input data-testid="admin-password" id="admin-password" name="password" type="password" required autoComplete="current-password" placeholder="Your password"/>{error&&<p role="alert" className="error" data-testid="admin-login-error">{error}</p>}<Button className="red-button" type="submit" disabled={busy} data-testid="admin-login-submit">{busy?'Signing in…':'ENTER THE STUDIO'}<ArrowRight size={16}/></Button><span className="login-security"><LockKeyhole size={12}/>AUTHORIZED ADMINISTRATORS ONLY</span></form></div>;
 return <div className="admin-layout"><SEO title="Admin Studio"/><aside className="admin-sidebar"><div className="studio-label"><ShieldCheck size={16}/><span>FLASHUBZ STUDIO</span></div><nav aria-label="Admin navigation">{navigation.map(([path,label,Icon])=><NavLink data-testid={`admin-nav-${path||'dashboard'}`} key={path} end to={`/admin${path?'/'+path:''}`}><Icon size={17}/><span>{label}</span>{path==='upload'&&<span className="nav-plus">+</span>}</NavLink>)}</nav><div className="admin-profile"><span className="admin-avatar">F</span><div><strong data-testid="admin-account-name">{auth.username}</strong><span>Administrator</span></div><button data-testid="admin-logout" title="Sign out" aria-label="Sign out" onClick={logout}><LogOut size={16}/></button></div></aside><div className="admin-content" key={section}>{error&&<p data-testid="admin-session-error" className="error">{error}</p>}{section==='upload'?<AdminUpload/>:section==='songs'?<AdminSongs/>:section===''||section==='analytics'?<AdminDashboard analytics={section==='analytics'}/>:<AdminManagement section={section}/>}</div></div>;
}
import {useRef,useEffect} from 'react';
import {useMusic} from '../context/MusicContext';
export const Waveform=({className='',bars=32})=>{
 const canvas=useRef(null);const {frequencies,playing}=useMusic();
 useEffect(()=>{let frame;const c=canvas.current,ctx=c.getContext('2d');let tick=0;const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const draw=()=>{const w=c.width,h=c.height;ctx.clearRect(0,0,w,h);tick+=.02;for(let i=0;i<bars;i++){const value=frequencies.current[Math.floor(i*80/bars)]/255;const idle=3+Math.sin(i*.7+(reduced?0:tick))*2;const height=playing?Math.max(3,value*h):idle*(.35+Math.sin(i/bars*Math.PI));ctx.fillStyle=i>bars*.7?'#ff5c64':'#ef233c';ctx.fillRect(i*w/bars,(h-height)/2,Math.max(1,w/bars-3),height);}frame=requestAnimationFrame(draw);};draw();return()=>cancelAnimationFrame(frame);},[frequencies,playing,bars]);
 return <canvas aria-hidden="true" ref={canvas} width="320" height="64" className={`waveform ${className}`} />;
};
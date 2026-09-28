import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {EffectComposer} from 'three/examples/jsm/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/examples/jsm/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/examples/jsm/postprocessing/OutputPass.js';
import {useMusic} from '../context/MusicContext';

export default function WorldScene({onOrbClick}){
 const mount=useRef(null),live=useRef({}),[failed,setFailed]=useState(false);const {frequencies,playing}=useMusic();live.current={playing,onOrbClick};
 useEffect(()=>{
  const host=mount.current;if(!host)return;let renderer,composer,frame,observer;const resources=[];
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  try{
   const mobile=host.clientWidth<768;renderer=new THREE.WebGLRenderer({antialias:!mobile,alpha:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,mobile?1.25:1.6));renderer.setClearColor(0x050506,0);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;host.appendChild(renderer.domElement);renderer.domElement.setAttribute('data-testid','world-webgl-canvas');renderer.domElement.setAttribute('aria-hidden','true');
   const scene=new THREE.Scene();const camera=new THREE.PerspectiveCamera(40,1,.1,100);camera.position.set(0,.4,10);
   const pmrem=new THREE.PMREMGenerator(renderer),env=pmrem.fromScene(new RoomEnvironment(),.04);scene.environment=env.texture;
   scene.add(new THREE.AmbientLight(0xffffff,.35));const redLight=new THREE.PointLight(0xff102a,8,20);redLight.position.set(2,0,3);scene.add(redLight);const white=new THREE.DirectionalLight(0xffffff,1.8);white.position.set(-3,5,6);scene.add(white);
   const root=new THREE.Group();scene.add(root);const orb=new THREE.Group();root.add(orb);
   const chrome=new THREE.MeshStandardMaterial({color:0xd7dce4,metalness:1,roughness:.16});const darkChrome=new THREE.MeshStandardMaterial({color:0x171217,metalness:1,roughness:.18});
   const red=new THREE.MeshPhysicalMaterial({color:0x90000c,metalness:.55,roughness:.16,clearcoat:.7,clearcoatRoughness:.12,emissive:0x4b0007,emissiveIntensity:.45,envMapIntensity:.5});
   const core=new THREE.Mesh(new THREE.SphereGeometry(1.3,64,48),red);core.scale.z=.7;orb.add(core);
   function torus(radius,tube,material,parent=orb){const mesh=new THREE.Mesh(new THREE.TorusGeometry(radius,tube,16,120),material);parent.add(mesh);return mesh;}
   const rim=torus(1.3,.115,chrome);rim.rotation.y=-.15;
   const blackRim=torus(1.14,.1,darkChrome);blackRim.position.z=.43;
   const neon=new THREE.MeshBasicMaterial({color:0xff2036});const innerRim=torus(1.04,.018,neon);innerRim.position.z=.62;
   const panel=new THREE.Mesh(new THREE.CircleGeometry(1.01,80),new THREE.MeshPhysicalMaterial({color:0x8c000a,metalness:.3,roughness:.24,clearcoat:.5,envMapIntensity:.18,emissive:0x67000b,emissiveIntensity:.5,transparent:true,opacity:.93}));panel.position.z=.97;orb.add(panel);
   const shape=new THREE.Shape();shape.moveTo(-.29,-.49);shape.lineTo(.55,0);shape.lineTo(-.29,.49);shape.quadraticCurveTo(-.37,.5,-.37,.4);shape.lineTo(-.37,-.4);shape.quadraticCurveTo(-.37,-.5,-.29,-.49);
   const icon=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:.1,bevelEnabled:true,bevelThickness:.035,bevelSize:.035,bevelSegments:4,steps:1}),new THREE.MeshStandardMaterial({color:0xffffff,metalness:.45,roughness:.3,emissive:0xffffff,emissiveIntensity:.05,envMapIntensity:.4}));icon.position.set(.04,0,1.03);orb.add(icon);
   const pause=new THREE.Group();[-.19,.19].forEach(x=>{const b=new THREE.Mesh(new THREE.BoxGeometry(.18,.72,.12),icon.material);b.position.set(x,0,1.1);pause.add(b);});orb.add(pause);pause.visible=false;
   const rings=new THREE.Group();root.add(rings);const r1=torus(1.95,.012,neon,rings);r1.rotation.set(1.17,.15,-.35);const r2=torus(2.15,.009,chrome,rings);r2.rotation.set(1.24,-.15,-.45);const r3=torus(2.4,.012,neon,rings);r3.rotation.set(1.32,.08,-.29);
   const floor=new THREE.Group();root.add(floor);floor.position.y=-1.75;for(let i=0;i<6;i++){const r=torus(1.65+i*.39,i%2?.008:.018,new THREE.MeshBasicMaterial({color:i%2?0x721018:0xc71a28,transparent:true,opacity:.55-i*.045}),floor);r.rotation.x=Math.PI/2;}
   const plane=new THREE.Mesh(new THREE.CircleGeometry(3,96),new THREE.MeshBasicMaterial({color:0x080405,transparent:true,opacity:.85}));plane.rotation.x=-Math.PI/2;plane.position.y=-1.79;root.add(plane);floor.scale.setScalar(.8);
   const glowCanvas=document.createElement('canvas');glowCanvas.width=128;glowCanvas.height=128;const gx=glowCanvas.getContext('2d'),gradient=gx.createRadialGradient(64,64,0,64,64,64);gradient.addColorStop(0,'rgba(255,34,42,0.85)');gradient.addColorStop(.15,'rgba(220,0,16,0.3)');gradient.addColorStop(1,'rgba(130,0,0,0)');gx.fillStyle=gradient;gx.fillRect(0,0,128,128);const glowTexture=new THREE.CanvasTexture(glowCanvas);resources.push(glowTexture);
   const glow=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTexture,blending:THREE.AdditiveBlending,depthWrite:false,opacity:.7}));glow.scale.set(5.7,5.7,1);glow.position.z=-.8;orb.add(glow);
   const notes=[];['♪','♫','♩','♪','♫','♩','♪'].slice(0,mobile?4:7).forEach((symbol,i)=>{const c=document.createElement('canvas');c.width=96;c.height=128;const ctx=c.getContext('2d');ctx.font='85px Georgia';ctx.shadowColor='#ff142c';ctx.shadowBlur=13;ctx.fillStyle=i%2?'#ffadb6':'#ff2136';ctx.fillText(symbol,8,100);const tex=new THREE.CanvasTexture(c);resources.push(tex);const note=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthWrite:false}));const a=i/7*Math.PI*2;note.userData={a,r:2.1+(i%3)*.15};note.position.set(Math.cos(a)*2.1,Math.sin(a)*1.9,.3);note.scale.set(.4,.54,1);root.add(note);notes.push(note);});
   const count=mobile?65:180,positions=new Float32Array(count*3);for(let i=0;i<count;i++){positions[i*3]=(Math.random()-.5)*13;positions[i*3+1]=(Math.random()-.5)*6;positions[i*3+2]=(Math.random()-.5)*6;}
   const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));const particles=new THREE.Points(geometry,new THREE.PointsMaterial({color:0xff3845,size:.035,transparent:true,opacity:.7,map:glowTexture,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(particles);
   composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));const bloom=new UnrealBloomPass(new THREE.Vector2(1,1),.3,.35,1.3);composer.addPass(bloom);composer.addPass(new OutputPass());
   let hover=false;const mouse=new THREE.Vector2(),raycaster=new THREE.Raycaster();const pointer=e=>{const rect=host.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-((e.clientY-rect.top)/rect.height)*2+1);raycaster.setFromCamera(mouse,camera);hover=raycaster.intersectObject(core).length>0;host.style.cursor=hover?'pointer':'default';};const click=()=>{if(hover)live.current.onOrbClick?.();};const leave=()=>{mouse.set(0,0);hover=false;};host.addEventListener('pointermove',pointer);host.addEventListener('pointerleave',leave);host.addEventListener('click',click);
   const resize=()=>{const w=host.clientWidth,h=host.clientHeight,isMobile=w<768;renderer.setSize(w,h);composer.setSize(w,h);camera.aspect=w/h;camera.fov=isMobile?45:40;camera.position.z=isMobile?10.3:10;camera.updateProjectionMatrix();root.position.set(isMobile?0:2.7,isMobile?-.95:.16,0);root.scale.setScalar(isMobile?.92:1.32);};observer=new ResizeObserver(resize);observer.observe(host);resize();
   const clock=new THREE.Clock();const render=()=>{const t=clock.getElapsedTime();const f=frequencies.current,bass=(f[1]+f[2]+f[3]+f[4])/1020,mid=(f[15]+f[25])/510;const scale=1+bass*.09+(hover?.025:0);orb.scale.lerp(new THREE.Vector3(scale,scale,scale),.07);icon.visible=!live.current.playing;pause.visible=live.current.playing;
    if(!reduced){orb.position.y=Math.sin(t*.7)*.065;orb.rotation.y=Math.sin(t*.24)*.12-.15;orb.rotation.z=Math.sin(t*.3)*.025;root.rotation.y+=(mouse.x*.035-root.rotation.y)*.025;rings.rotation.z=t*(hover?.13:.05);notes.forEach((n,i)=>{n.position.y=Math.sin(n.userData.a)*1.9+Math.sin(t*.7+i)*.09;});particles.rotation.y=t*.018;floor.scale.setScalar(.8+bass*.07);}
    redLight.intensity=8+bass*12;red.emissiveIntensity=.45+mid*.4;glow.material.opacity=.23+bass*.15;bloom.strength=.3+bass*.2;composer.render();frame=requestAnimationFrame(render);};render();
   return()=>{cancelAnimationFrame(frame);observer?.disconnect();host.removeEventListener('pointermove',pointer);host.removeEventListener('pointerleave',leave);host.removeEventListener('click',click);scene.traverse(o=>{o.geometry?.dispose();if(o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});resources.forEach(r=>r.dispose());env.dispose();pmrem.dispose();composer.dispose();renderer.dispose();renderer.domElement.remove();};
  }catch(e){console.warn('Using artwork fallback:',e.message);setFailed(true);renderer?.dispose();}
 },[frequencies]);
 return <div className={`world-scene ${failed?'world-fallback':''}`} ref={mount} data-testid="world-scene">{failed&&<img src="/assets/flashubz-artwork.webp" alt="FLASHUBZ red chrome play orb"/>}</div>;
}
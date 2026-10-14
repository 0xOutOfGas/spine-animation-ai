"""Offline geometry preview for the exact stationary turret subset we author."""
import base64
import html
import io
import json


def generate_preview(manifest, images):
    payload = dict(manifest)
    payload["images"] = {}
    for name, im in images.items():
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        payload["images"][name] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    page = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · Turret geometry preview</title>
<style>
body{margin:0;background:#eee9df;color:#243742;font:15px system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:28px}
h1{font-size:26px;margin:0 0 8px}p{max-width:850px;line-height:1.55}button,select,input{font:inherit}button,select{padding:8px 14px;border:1px solid #9eaaa9;border-radius:7px;background:#fff;cursor:pointer}
.controls{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:18px 0}#angle{width:240px}.stage{background:#faf9f4;border:1px solid #b6c0b9;border-radius:12px;overflow:hidden}
canvas{display:block;width:100%}#sheet{margin-top:18px;border:1px solid #b6c0b9;border-radius:12px;background:#faf9f4}.note{font-size:13px;color:#526767}output{font-variant-numeric:tabular-nums}.badge{display:inline-block;background:#d4e5dc;border-radius:5px;padding:5px 8px}
</style><main><h1>__TITLE__</h1><div class="badge">Fixed base · 360° aim · local recoil</div>
<p>Geometry preview from the measured rig. The socket stays at the crosshair; only the head turns.
The red points are visual muzzles. This preview implements the exported region subset and does not run the Spine runtime.</p>
<div class="controls"><label>Aim <input id="angle" type="range" min="-180" max="180" step="0.1" value="0"></label><output id="degrees">0°</output>
<button id="fire">Fire</button><label><input id="sweep" type="checkbox">360° sweep</label><label><input id="repeat" type="checkbox">Repeat fire</label>
<label>Display <select id="zoom"><option value="1">72px cell · 1×</option><option value="3" selected>72px cell · 3×</option><option value="6">72px cell · 6×</option></select></label>
<label><input id="dark" type="checkbox">Dark background</label></div>
<div class="stage"><canvas id="stage" width="1060" height="420" aria-label="Interactive turret preview"></canvas></div>
<p><output id="status"></output></p><canvas id="sheet" width="1060" height="380" aria-label="12 aim angles at rest and peak recoil"></canvas>
<p class="note">Top row: idle. Bottom row: peak recoil. Every head pixel with alpha greater than zero, including each texel corner, is included in the rotation budget.
No walk, run, jump or baked turning clip. Pointer movement aims the turret; click fires a presentation preview.</p></main>
<script>
const rig=__DATA__, stage=document.querySelector('#stage'), ctx=stage.getContext('2d'), sheet=document.querySelector('#sheet'), sc=sheet.getContext('2d');
const angle=document.querySelector('#angle'), sweep=document.querySelector('#sweep'), repeat=document.querySelector('#repeat'), zoom=document.querySelector('#zoom'), dark=document.querySelector('#dark');
const sprites={}; let fireTime=Infinity, previous=null, turn=0, sinceShot=0;
function depth(t){let f=rig.fire;if(t<0||t>=f.duration)return 0;if(t<=f.peak_time)return f.recoil_source_px*t/f.peak_time;if(t<f.recover_time)return f.recoil_source_px*(f.recover_time-t)/(f.recover_time-f.peak_time);return 0;}
function draw(c,cx,cy,theta,d,z){let s=rig.godot_display_scale*z; c.save();c.translate(cx,cy);c.scale(s,s);
 for(const p of rig.parts){c.save();if(p.role!=='base')c.rotate(theta);if(p.role==='recoil')c.translate(-rig.forward_px[0]*d,-rig.forward_px[1]*d);
 c.drawImage(sprites[p.name],p.position_px[0]-rig.pivot_px[0],p.position_px[1]-rig.pivot_px[1]);c.restore();}
 c.save();c.rotate(theta);c.translate(-rig.forward_px[0]*d,-rig.forward_px[1]*d);c.fillStyle='#d94739';for(const m of rig.muzzles){c.beginPath();c.arc(m.setup_px[0]-rig.pivot_px[0],m.setup_px[1]-rig.pivot_px[1],2.5/s,0,Math.PI*2);c.fill();}c.restore();c.restore();
 c.save();c.strokeStyle='#3b8b77';c.lineWidth=1;c.beginPath();c.moveTo(cx-7,cy);c.lineTo(cx+7,cy);c.moveTo(cx,cy-7);c.lineTo(cx,cy+7);c.stroke();c.restore();}
function backdrop(c,w,h,cell){c.fillStyle=dark.checked?'#23313b':'#faf9f4';c.fillRect(0,0,w,h);c.strokeStyle=dark.checked?'#40525c':'#e0e4dc';c.lineWidth=.6;c.beginPath();for(let x=w/2%cell;x<w;x+=cell){c.moveTo(x,0);c.lineTo(x,h);}for(let y=h/2%cell;y<h;y+=cell){c.moveTo(0,y);c.lineTo(w,y);}c.stroke();}
function contact(){backdrop(sc,sheet.width,sheet.height,100);sc.fillStyle=dark.checked?'#d9e9de':'#334c48';sc.font='13px system-ui';
 for(let row=0;row<2;row++){sc.fillText(row?'Peak fire':'Idle',10,30+row*180);for(let i=0;i<12;i++){let x=46+i*88,y=100+row*180;draw(sc,x,y,i*Math.PI/6,row?rig.fire.recoil_source_px:0,1);sc.fillText(i*30+'°',x-10,y+50);}}}
function shot(){fireTime=0;sinceShot=0;}
document.querySelector('#fire').onclick=shot;angle.oninput=()=>{turn=Number(angle.value)*Math.PI/180;sweep.checked=false;};dark.onchange=contact;
stage.onpointermove=e=>{if(sweep.checked)return;let r=stage.getBoundingClientRect(),x=(e.clientX-r.left)*stage.width/r.width-stage.width/2,y=(e.clientY-r.top)*stage.height/r.height-stage.height/2;if(Math.hypot(x,y)<3)return;turn=Math.atan2(y,x)-Math.atan2(rig.forward_px[1],rig.forward_px[0]);turn=Math.atan2(Math.sin(turn),Math.cos(turn));angle.value=turn*180/Math.PI;};stage.onpointerdown=shot;
function frame(now){let dt=previous===null?0:Math.min((now-previous)/1000,.1);previous=now;fireTime+=dt;sinceShot+=dt;if(repeat.checked&&sinceShot>=Math.max(rig.fire.duration,.35))shot();if(sweep.checked){turn=(turn+dt*1.2)%(Math.PI*2);angle.value=Math.atan2(Math.sin(turn),Math.cos(turn))*180/Math.PI;}
 let z=Number(zoom.value);backdrop(ctx,stage.width,stage.height,rig.cell_size_px*z);ctx.save();ctx.strokeStyle='#b8cdbc';ctx.setLineDash([5,5]);ctx.beginPath();ctx.arc(stage.width/2,stage.height/2,rig.head_max_radius_cell*rig.cell_size_px*z,0,Math.PI*2);ctx.stroke();ctx.restore();
 draw(ctx,stage.width/2,stage.height/2,turn,depth(fireTime),z);document.querySelector('#degrees').textContent=((turn*180/Math.PI%360+360)%360).toFixed(1)+'°';
 document.querySelector('#status').textContent='Head envelope '+rig.head_envelope_cell.toFixed(4)+' / '+rig.head_max_radius_cell+' cell · recoil '+rig.fire.recoil_cell+' cell · '+(fireTime<rig.fire.duration?'fire':'idle');requestAnimationFrame(frame);}
Promise.all(Object.entries(rig.images).map(([name,url])=>new Promise((resolve,reject)=>{let im=new Image();im.onload=()=>{sprites[name]=im;resolve();};im.onerror=reject;im.src=url;}))).then(()=>{contact();requestAnimationFrame(frame);}).catch(()=>{document.querySelector('#status').textContent='Texture failed to load';});
</script></html>'''
    return page.replace("__TITLE__", html.escape(manifest["name"])).replace("__DATA__", encoded)

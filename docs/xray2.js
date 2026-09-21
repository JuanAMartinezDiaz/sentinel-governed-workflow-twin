import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";

const canvas=document.getElementById("xrayCanvas");
const scene=new THREE.Scene();
scene.fog=new THREE.FogExp2(0x04101a,.055);
const camera=new THREE.PerspectiveCamera(42,1,.1,80);
camera.position.set(0,3.25,13.7);
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:"high-performance"});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setClearColor(0x04101a,0);
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.25;

scene.add(new THREE.HemisphereLight(0x78cfff,0x071018,1.25));
const key=new THREE.PointLight(0x49dfff,30,24);key.position.set(-2,4,6);scene.add(key);
const fill=new THREE.PointLight(0x44f0b0,22,18);fill.position.set(5,1,4);scene.add(fill);
const amberLight=new THREE.PointLight(0xffb83f,26,15);amberLight.position.set(-3,1,4);scene.add(amberLight);

const floor=new THREE.GridHelper(24,48,0x1c607d,0x123246);
floor.position.y=-1.8;
floor.material.transparent=true;floor.material.opacity=.22;
scene.add(floor);

const stageX=[-5.25,-3.1,-.72,1.65,3.85,5.55];
const stageGroups=[];
const color={cyan:0x59dcff,blue:0x5aa7ff,amber:0xffbd4a,green:0x55f0b0,red:0xff666f,navy:0x0a2536};

function mat(c,opts={}){
 return new THREE.MeshStandardMaterial({
  color:c,emissive:opts.emissive??c,emissiveIntensity:opts.emissiveIntensity??.12,
  metalness:opts.metalness??.65,roughness:opts.roughness??.24,
  transparent:opts.transparent??false,opacity:opts.opacity??1,
  side:THREE.DoubleSide
 });
}

function addGlow(group,c,size=1.8){
 const texCanvas=document.createElement("canvas");texCanvas.width=128;texCanvas.height=128;
 const ctx=texCanvas.getContext("2d");const g=ctx.createRadialGradient(64,64,0,64,64,64);
 g.addColorStop(0,"rgba(255,255,255,.95)");g.addColorStop(.15,"rgba(120,220,255,.65)");
 g.addColorStop(.5,"rgba(40,130,190,.14)");g.addColorStop(1,"rgba(0,0,0,0)");
 ctx.fillStyle=g;ctx.fillRect(0,0,128,128);
 const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(texCanvas),color:c,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:.6}));
 sprite.scale.set(size,size,size);group.add(sprite);return sprite;
}

const tube=new THREE.Mesh(
 new THREE.CylinderGeometry(.7,.7,11.9,48,1,true),
 mat(0x12384d,{transparent:true,opacity:.2,emissive:0x0c4f6c,emissiveIntensity:.18,roughness:.12})
);
tube.rotation.z=Math.PI/2;tube.position.y=-.18;scene.add(tube);

const spine=new THREE.Mesh(
 new THREE.CylinderGeometry(.075,.075,11.7,20),
 new THREE.MeshBasicMaterial({color:color.cyan,transparent:true,opacity:.38})
);
spine.rotation.z=Math.PI/2;spine.position.y=-.18;scene.add(spine);

function stageFrame(x,c){
 const g=new THREE.Group();g.position.set(x,-.18,0);
 const ring=new THREE.Mesh(new THREE.TorusGeometry(.86,.035,10,64),mat(c,{emissiveIntensity:.55,metalness:.4,roughness:.15}));
 ring.rotation.y=Math.PI/2;g.add(ring);
 const shell=new THREE.Mesh(new THREE.CylinderGeometry(.79,.79,1.55,32,1,true),mat(c,{transparent:true,opacity:.07,emissiveIntensity:.08}));
 shell.rotation.z=Math.PI/2;g.add(shell);
 scene.add(g);stageGroups.push(g);return g;
}

const proposal=stageFrame(stageX[0],color.cyan);
const pCore=new THREE.Mesh(new THREE.IcosahedronGeometry(.42,1),mat(color.blue,{emissiveIntensity:.8,roughness:.08}));
proposal.add(pCore);addGlow(proposal,color.cyan,2.4);

const gate=new THREE.Group();gate.position.set(stageX[1],-.18,0);scene.add(gate);stageGroups.push(gate);
const gateRings=[];
[1.12,.88,.62].forEach((r,i)=>{
 const m=mat(color.amber,{emissiveIntensity:.55+i*.12,metalness:.45,roughness:.12});
 const t=new THREE.Mesh(new THREE.TorusGeometry(r,.055-i*.009,12,72),m);t.rotation.y=Math.PI/2;gate.add(t);gateRings.push(t);
});
const shield=new THREE.Mesh(new THREE.OctahedronGeometry(.43,0),mat(color.amber,{transparent:true,opacity:.48,emissiveIntensity:.7}));
gate.add(shield);addGlow(gate,color.amber,3.1);

const human=stageFrame(stageX[2],color.blue);
const humanCore=new THREE.Mesh(new THREE.SphereGeometry(.43,28,20),mat(color.blue,{emissiveIntensity:.72,roughness:.1}));
human.add(humanCore);
const humanOrbit=new THREE.Mesh(new THREE.TorusGeometry(.62,.035,8,64),mat(color.blue,{emissiveIntensity:.65,metalness:.3}));
humanOrbit.rotation.x=Math.PI/2;human.add(humanOrbit);addGlow(human,color.blue,2.35);

const permit=stageFrame(stageX[3],color.green);
const permitCard=new THREE.Mesh(new THREE.BoxGeometry(1.12,.72,.12),mat(color.green,{transparent:true,opacity:.72,emissiveIntensity:.38,metalness:.28,roughness:.16}));
permitCard.rotation.y=-.06;permit.add(permitCard);
const permitEdges=new THREE.LineSegments(new THREE.EdgesGeometry(permitCard.geometry),new THREE.LineBasicMaterial({color:color.green,transparent:true,opacity:.95}));
permitCard.add(permitEdges);addGlow(permit,color.green,2.2);

const executor=stageFrame(stageX[4],color.blue);
const execBox=new THREE.Mesh(new THREE.BoxGeometry(1.1,1.1,1.1),mat(color.blue,{transparent:true,opacity:.2,emissiveIntensity:.25,roughness:.15}));
executor.add(execBox);
const execEdges=new THREE.LineSegments(new THREE.EdgesGeometry(execBox.geometry),new THREE.LineBasicMaterial({color:color.cyan,transparent:true,opacity:.82}));
execBox.add(execEdges);
for(let i=0;i<5;i++){
 const cube=new THREE.Mesh(new THREE.BoxGeometry(.19,.19,.19),mat(color.cyan,{emissiveIntensity:.8,metalness:.25,roughness:.1}));
 cube.position.set((i%2?1:-1)*.24,(i-2)*.13,(i%3-1)*.18);executor.add(cube);
}
addGlow(executor,color.blue,2.3);

const evidence=stageFrame(stageX[5],color.green);
const ledgers=[];
for(let i=0;i<5;i++){
 const slab=new THREE.Mesh(new THREE.BoxGeometry(.95,.72,.055),mat(color.green,{transparent:true,opacity:.22+i*.06,emissiveIntensity:.32,metalness:.18,roughness:.15}));
 slab.position.z=(i-2)*.16;slab.position.x=i*.035;slab.rotation.y=-.12;evidence.add(slab);ledgers.push(slab);
}
addGlow(evidence,color.green,2.35);

const starCount=340;
const starPos=new Float32Array(starCount*3);
for(let i=0;i<starCount;i++){
 starPos[i*3]=(Math.random()-.5)*25;starPos[i*3+1]=(Math.random()-.25)*10;starPos[i*3+2]=(Math.random()-.5)*12;
}
const starGeo=new THREE.BufferGeometry();starGeo.setAttribute("position",new THREE.BufferAttribute(starPos,3));
const stars=new THREE.Points(starGeo,new THREE.PointsMaterial({color:0x4eb9e7,size:.024,transparent:true,opacity:.38,depthWrite:false}));
scene.add(stars);

const packet=new THREE.Mesh(new THREE.OctahedronGeometry(.18,0),mat(color.cyan,{emissiveIntensity:2,metalness:.1,roughness:.08}));
packet.position.set(-6.1,-.18,0);scene.add(packet);
const packetLight=new THREE.PointLight(color.cyan,16,3);packet.add(packetLight);

const trailGeo=new THREE.BufferGeometry();
const trailCount=42;const trailPos=new Float32Array(trailCount*3);
trailGeo.setAttribute("position",new THREE.BufferAttribute(trailPos,3));
const trail=new THREE.Points(trailGeo,new THREE.PointsMaterial({color:color.cyan,size:.07,transparent:true,opacity:.65,blending:THREE.AdditiveBlending,depthWrite:false}));
scene.add(trail);
const trailHistory=Array.from({length:trailCount},()=>new THREE.Vector3(-6.1,-.18,0));

const scenarios={
 read:{title:"LOW RISK READ",tone:"cyan",disp:"ALLOW",sub:"Read-only action. Human approval is not required.",stop:"pass",
 summary:"The agent is registered, READ_CASE is delegated, case_api is approved, the action is within the risk ceiling, and confidence clears the LOW threshold.",
 trace:"PROPOSED ACTION\nREAD_CASE / case_api / LOW / confidence 0.95\n\n[PASS] agent_registry\n[PASS] delegated_action\n[PASS] tool_permission\n[PASS] risk_ceiling\n[PASS] confidence >= 0.60\n[SKIP] human_approval\n\nDISPOSITION: ALLOW\nEXECUTION PERMIT: ISSUED"},
 high:{title:"HIGH RISK ACTION",tone:"amber",disp:"REQUIRE_APPROVAL",sub:"The action reaches the gate and waits for accountable human authority.",stop:"gate",
 summary:"The agent may propose the state change, but capability does not supply authority. No execution permit exists until the required human approval is present.",
 trace:"PROPOSED ACTION\nCOMMIT_ACCOUNT_CHANGE / HIGH / confidence 0.97\n\n[PASS] agent_registry\n[PASS] delegated_action\n[PASS] tool_permission\n[PASS] risk_ceiling\n[PASS] confidence >= 0.90\n[WAIT] human_approval required\n\nDISPOSITION: REQUIRE_APPROVAL\nEXECUTION PERMIT: NOT ISSUED"},
 approved:{title:"APPROVED ACTION",tone:"green",disp:"ALLOW",sub:"Human authority is present. A permit is issued for this exact action.",stop:"pass",
 summary:"After approval, Sentinel binds authorization to the action fingerprint, issues a signed execution permit, and allows the protected executor to proceed.",
 trace:"PROPOSED ACTION\nCOMMIT_ACCOUNT_CHANGE / HIGH / confidence 0.97\nhuman_approved: true\n\n[PASS] agent_registry\n[PASS] delegated_action\n[PASS] tool_permission\n[PASS] risk_ceiling\n[PASS] confidence >= 0.90\n[PASS] human_approval\n\nDISPOSITION: ALLOW\nEXECUTION PERMIT: ISSUED\nPROTECTED EXECUTOR: ACTION MAY PROCEED"},
 bypass:{title:"BYPASS ATTEMPT",tone:"red",disp:"BLOCKED",sub:"A direct executor call cannot manufacture authority.",stop:"bypass",
 summary:"The attempted action appears at the protected executor without a valid permit. The boundary fails closed and the state change is not executed.",
 trace:"DIRECT CALL TO PROTECTED EXECUTOR\nexecution_permit: null\n\n[FAIL] permit validation\n[FAIL] authorization boundary\n\nRESULT: PermissionError\nSTATE CHANGE: NOT EXECUTED"},
 confidence:{title:"CONFIDENCE BELOW FLOOR",tone:"amber",disp:"FALLBACK",sub:"Governance chooses a bounded non-execution path.",stop:"fallback",
 summary:"The proposed action is otherwise delegated, but confidence is below the MODERATE threshold. Sentinel does not improvise; it selects the declared safe fallback.",
 trace:"PROPOSED ACTION\nDRAFT_RECOMMENDATION / MODERATE / confidence 0.50\n\n[PASS] agent_registry\n[PASS] delegated_action\n[PASS] tool_permission\n[PASS] risk_ceiling\n[FAIL] confidence < 0.75\n[PASS] bounded_fallback\n\nDISPOSITION: FALLBACK\nEXECUTION PERMIT: NOT ISSUED"}
};

let activeScenario="high";
let scenarioStarted=performance.now();
let hoverStage=-1;
const stateBox=document.getElementById("xrayState");
const stateValue=document.getElementById("xrayStateValue");
const stateSub=document.getElementById("xrayStateSub");
const disposition=document.getElementById("disposition");
const summary=document.getElementById("scenarioSummary");
const traceEl=document.getElementById("trace");
const stageLabels=[...document.querySelectorAll(".stage-label")];
const scenarioButtons=[...document.querySelectorAll(".scenario-btn")];

function setMaterialColor(material,c,emissive=c){
 material.color.setHex(c);
 if(material.emissive)material.emissive.setHex(emissive);
}

function applyScenario(name){
 activeScenario=name;scenarioStarted=performance.now();
 const s=scenarios[name];
 stateBox.dataset.tone=s.tone;stateValue.textContent=s.title;stateSub.textContent=s.sub;
 disposition.textContent=s.disp;summary.textContent=s.summary;traceEl.textContent=s.trace;
 const tone=s.tone==="green"?color.green:s.tone==="red"?color.red:s.tone==="amber"?color.amber:color.cyan;
 disposition.style.color="#"+tone.toString(16).padStart(6,"0");
 scenarioButtons.forEach(b=>b.classList.toggle("active",b.dataset.scenario===name));
 gateRings.forEach(r=>setMaterialColor(r.material,tone,tone));
 setMaterialColor(shield.material,tone,tone);
 const humanTone=name==="approved"?color.green:name==="high"?color.amber:color.blue;
 setMaterialColor(humanCore.material,humanTone,humanTone);setMaterialColor(humanOrbit.material,humanTone,humanTone);
 permit.visible=(name==="approved"||name==="read");
 const execTone=name==="bypass"?color.red:(name==="approved"||name==="read"?color.green:color.blue);
 setMaterialColor(execBox.material,execTone,execTone);execEdges.material.color.setHex(execTone);
 ledgers.forEach(l=>setMaterialColor(l.material,tone,tone));
 packet.material.color.setHex(tone);packet.material.emissive.setHex(tone);packetLight.color.setHex(tone);
 trail.material.color.setHex(tone);
}

scenarioButtons.forEach(b=>b.addEventListener("click",()=>applyScenario(b.dataset.scenario)));
stageLabels.forEach((b,i)=>{
 b.addEventListener("mouseenter",()=>hoverStage=i);
 b.addEventListener("mouseleave",()=>hoverStage=-1);
 b.addEventListener("focus",()=>hoverStage=i);
 b.addEventListener("blur",()=>hoverStage=-1);
});

const pointer={x:0,y:0};
window.addEventListener("pointermove",e=>{
 pointer.x=(e.clientX/window.innerWidth-.5)*2;
 pointer.y=(e.clientY/window.innerHeight-.5)*2;
},{passive:true});

function packetPosition(now){
 const s=scenarios[activeScenario];
 const cycle=((now-scenarioStarted)%6200)/6200;
 const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
 if(s.stop==="pass") return THREE.MathUtils.lerp(-6.25,6.2,ease(cycle));
 if(s.stop==="gate"){
  const t=Math.min(cycle/.42,1);return THREE.MathUtils.lerp(-6.25,stageX[1]-.18,ease(t));
 }
 if(s.stop==="fallback"){
  if(cycle<.42)return THREE.MathUtils.lerp(-6.25,stageX[1]-.18,ease(cycle/.42));
  return THREE.MathUtils.lerp(stageX[1]-.18,-5.45,ease(Math.min((cycle-.42)/.44,1)));
 }
 return stageX[4]-.55+Math.sin(cycle*Math.PI*2)*.08;
}

function resize(){
 const box=canvas.parentElement.getBoundingClientRect();
 const w=Math.max(1,box.width),h=Math.max(1,box.height);
 renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
}
window.addEventListener("resize",resize);resize();

let lastTrail=0;
function animate(now){
 requestAnimationFrame(animate);
 const t=now*.001;
 camera.position.x+=(pointer.x*.32-camera.position.x)*.025;
 camera.position.y+=(3.25-pointer.y*.18-camera.position.y)*.025;
 camera.lookAt(0,-.08,0);

 gate.rotation.x=Math.sin(t*.7)*.025;
 gateRings[0].rotation.x=t*.38;gateRings[1].rotation.x=-t*.55;gateRings[2].rotation.x=t*.82;
 shield.rotation.x=t*.55;shield.rotation.y=t*.9;
 humanOrbit.rotation.z=t*.55;
 pCore.rotation.x=t*.42;pCore.rotation.y=t*.68;
 execBox.rotation.x=Math.sin(t*.65)*.07;execBox.rotation.y=t*.16;
 ledgers.forEach((l,i)=>{l.position.y=Math.sin(t*1.4+i*.55)*.035});
 stars.rotation.y=t*.012;

 packet.position.x=packetPosition(now);
 packet.position.y=-.18+Math.sin(t*5.5)*.045;
 packet.rotation.x=t*2.2;packet.rotation.y=t*2.8;
 if(activeScenario==="high" && packet.position.x>stageX[1]-.3) packet.scale.setScalar(1+Math.sin(t*6)*.22);
 else if(activeScenario==="bypass") packet.scale.setScalar(1.2+Math.sin(t*9)*.18);
 else packet.scale.setScalar(1);

 if(now-lastTrail>34){
  lastTrail=now;trailHistory.pop();trailHistory.unshift(packet.position.clone());
  const a=trail.geometry.attributes.position.array;
  trailHistory.forEach((p,i)=>{a[i*3]=p.x;a[i*3+1]=p.y;a[i*3+2]=p.z});
  trail.geometry.attributes.position.needsUpdate=true;
 }

 let nearest=0,best=999;
 stageX.forEach((x,i)=>{const d=Math.abs(packet.position.x-x);if(d<best){best=d;nearest=i}});
 stageLabels.forEach((el,i)=>el.classList.toggle("active",i===(hoverStage>=0?hoverStage:nearest)));
 stageGroups.forEach((g,i)=>{
  const target=(i===(hoverStage>=0?hoverStage:nearest))?1.075:1;
  g.scale.lerp(new THREE.Vector3(target,target,target),.08);
 });
 renderer.render(scene,camera);
}
requestAnimationFrame(animate);

const workflowSteps=[
["S01","Receive exception request","ASSIST"],["S02","Validate request completeness","AGENT"],
["S03","Retrieve customer profile","AGENT"],["S04","Retrieve account state","AGENT"],
["S05","Check data provenance","AGENT"],["S06","Classify exception type","AGENT"],
["S07","Apply policy retrieval","AGENT"],["S08","Identify missing evidence","AGENT"],
["S09","Request additional evidence","ASSIST"],["S10","Assess exception risk","AGENT"],
["S11","Generate recommended disposition","AGENT"],["S12","Independent control check","AGENT"],
["S13","Human decision review","HUMAN"],["S14","Prepare customer communication","AGENT"],
["S15","Approval before state change","HUMAN"],["S16","Commit approved account change","AGENT"],
["S17","Write evidence and close case","AGENT"]
];
document.getElementById("baseline").innerHTML=workflowSteps.map(s=>'<div class="step human"><span class="n">'+s[0]+'</span><div>'+s[1]+'<br><small>HUMAN</small></div></div>').join("");
document.getElementById("redesign").innerHTML=workflowSteps.map(s=>{
 const cls=s[2]==="HUMAN"?"human":s[2]==="ASSIST"?"assist":"agent";
 return '<div class="step '+cls+'"><span class="n">'+s[0]+'</span><div>'+s[1]+'<br><small>'+s[2]+'</small></div></div>';
}).join("");

applyScenario("high");
window.__sentinelXRay2Ready=true;
document.documentElement.dataset.xray2Ready="true";

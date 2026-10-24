import assert from 'node:assert/strict';
import test from 'node:test';
import {createScenarioRunner} from '../docs/demo-client.mjs';
import {scenarios} from '../docs/scenarios.mjs';

function resultFor(name){
 return {
  mode:'synthetic-demo', scenario:scenarios[name].apiScenario,
  decision:scenarios[name].disp, reason:'synthetic test response',
  trace:[{check:'test',status:'PASS',detail:'test fixture'}],
  evidence:[{decision_id:'test-only'}, {execution_status:scenarios[name].disp==='ALLOW'?'SUCCEEDED':'BLOCKED'}]
 };
}
const responseFor=name=>({ok:true,json:async()=>resultFor(name)});
function harness(fetchImpl,timeoutMs=1000){
 const events=[];
 const run=createScenarioRunner({
  scenarios,fetchImpl,timeoutMs,
  onPending:name=>events.push(['pending',name]),
  onResult:(name,result)=>events.push(['result',name,result.decision]),
  onUnavailable:name=>events.push(['unavailable',name])
 });
 return {run,events};
}
function deferred(){
 let resolve,reject;
 const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});
 return {promise,resolve,reject};
}

for(const name of Object.keys(scenarios)){
 test(`visual selection ${name} sends only its fixed API scenario`,async()=>{
  const {run,events}=harness(async(url,options)=>{
   assert.equal(url,'/api/demo');
   assert.equal(options.method,'POST');
   assert.deepEqual(JSON.parse(options.body),{scenario:scenarios[name].apiScenario});
   return responseFor(name);
  });
  await run(name);
  assert.deepEqual(events,[['pending',name],['result',name,scenarios[name].disp]]);
 });
}

test('older success cannot overwrite the latest selection',async()=>{
 const first=deferred(),second=deferred();
 let count=0,firstSignal;
 const {run,events}=harness(async(url,options)=>{
  if(count++===0){firstSignal=options.signal;return first.promise;}
  return second.promise;
 });
 const a=run('approved'),b=run('tool');
 second.resolve(responseFor('tool'));await b;
 first.resolve(responseFor('approved'));await a;
 assert.equal(firstSignal.aborted,true);
 assert.deepEqual(events,[['pending','approved'],['pending','tool'],['result','tool','DENY']]);
});

test('older failure cannot replace the latest connected status',async()=>{
 const first=deferred();let count=0;
 const {run,events}=harness(()=>count++===0?first.promise:Promise.resolve(responseFor('read')));
 const a=run('high');await run('read');
 first.reject(new Error('old request failed'));await a;
 assert.deepEqual(events,[['pending','high'],['pending','read'],['result','read','ALLOW']]);
});

for(const [label,fetchImpl] of [
 ['offline',async()=>{throw new Error('offline');}],
 ['HTTP error',async()=>({ok:false,status:503})],
 ['invalid JSON',async()=>({ok:true,json:async()=>{throw new SyntaxError('bad JSON');}})],
 ['wrong scenario',async()=>responseFor('approved')],
 ['wrong mode',async()=>({ok:true,json:async()=>({...resultFor('tool'),mode:'production'})})],
 ['unexpected decision',async()=>({ok:true,json:async()=>({...resultFor('tool'),decision:'ALLOW'})})],
 ['missing evidence',async()=>({ok:true,json:async()=>({...resultFor('tool'),evidence:[]})})],
 ['malformed trace',async()=>({ok:true,json:async()=>({...resultFor('tool'),trace:[null]})})],
]){
 test(`${label} retains the illustrative fallback`,async()=>{
  const {run,events}=harness(fetchImpl);
  await run('tool');
  assert.deepEqual(events,[['pending','tool'],['unavailable','tool']]);
 });
}

test('a stalled request times out and releases the pending status',async()=>{
 const {run,events}=harness(()=>new Promise(()=>{}),5);
 await run('read');
 assert.deepEqual(events,[['pending','read'],['unavailable','read']]);
});

test('unknown visual selections never submit an arbitrary scenario',async()=>{
 const {run,events}=harness(()=>assert.fail('unexpected API request'));
 await run('customer-input');
 assert.deepEqual(events,[['pending','customer-input'],['unavailable','customer-input']]);
});

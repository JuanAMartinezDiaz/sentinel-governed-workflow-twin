// Keep asynchronous API results associated with the currently selected scenario.
export function createScenarioRunner({
 scenarios, onPending, onResult, onUnavailable,
 fetchImpl=globalThis.fetch, timeoutMs=5000
}){
 let latest=0;
 let previousController;
 return async function runScenario(name){
  const requestId=++latest;
  previousController?.abort();
  const controller=new AbortController();
  previousController=controller;
  let timer;
  onPending(name);
  try{
   const scenario=scenarios[name];
   if(!scenario)throw new Error("Unknown visual scenario");
   const request=(async()=>{
    const response=await fetchImpl("/api/demo",{
     method:"POST", headers:{"Content-Type":"application/json"},
     body:JSON.stringify({scenario:scenario.apiScenario}), signal:controller.signal
    });
    if(!response.ok)throw new Error("Engine API returned "+response.status);
    return response.json();
   })();
   const timeout=new Promise((_,reject)=>{
    timer=setTimeout(()=>{
     controller.abort();
     reject(new Error("Engine API timed out"));
    },timeoutMs);
   });
   const result=await Promise.race([request,timeout]);
   if(requestId!==latest)return;
   if(result?.mode!=="synthetic-demo" || result.scenario!==scenario.apiScenario ||
      result.decision!==scenario.disp || typeof result.reason!=="string" ||
      !Array.isArray(result.trace) || !result.trace.length ||
      !result.trace.every(s=>typeof s?.check==="string" && typeof s.status==="string" && typeof s.detail==="string") ||
      !Array.isArray(result.evidence) || typeof result.evidence[0]?.decision_id!=="string" ||
      !["SUCCEEDED","BLOCKED","FAILED"].includes(result.evidence[1]?.execution_status)){
    throw new Error("Unexpected engine response");
   }
   onResult(name,result);
  }catch(error){
   if(requestId===latest)onUnavailable(name,error);
  }finally{
   clearTimeout(timer);
  }
 };
}

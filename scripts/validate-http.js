#!/usr/bin/env node
"use strict";
process.env.WATCHDOG="off"; process.env.TELEGRAM_ENABLED="0";
const {server}=require("../server/server.js");
const failures=[];
function ok(x,m){if(!x)failures.push(m)}
server.listen(0,"127.0.0.1",async()=>{
 const base=`http://127.0.0.1:${server.address().port}`;
 try{
  for(const p of ["/","/sports/","/movies/","/series/","/anime/","/articles/","/movie/the-invite/","/entertainment/","/watch-next/","/watch-next/shows-like-alice-in-borderland/","/sports/explainers/","/sports/explainers/what-does-offside-mean/","/movie/1917/","/assets/media-v3.css"]){const r=await fetch(base+p,{redirect:"manual"});ok(r.status===200,`${p}: ${r.status}`);await r.arrayBuffer()}
  for(const p of ["/package.json","/scripts/apply-media-brand.py","/content/catalogue.json","/missing"]){const r=await fetch(base+p,{redirect:"manual"});ok(r.status===404,`${p} should be 404, got ${r.status}`);await r.arrayBuffer()}
  const r=await fetch(base+"/"); for(const h of ["content-security-policy","x-content-type-options","referrer-policy"])ok(r.headers.has(h),`missing ${h}`);
 }catch(e){failures.push(e.stack||String(e))}finally{server.close(()=>{if(failures.length){console.error(failures.join("\n"));process.exitCode=1}else console.log(JSON.stringify({ok:true,http:"media routes and containment"},null,2))})}
});

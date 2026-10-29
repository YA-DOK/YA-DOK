"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { DashboardIcon } from "./dashboard-icon";
import { translated, useDashboardUI } from "./dashboard-ui";

type Version = {version_number:number;created_at:string|null;is_published:boolean;has_clinical_approval:boolean;publication_blocker_count:number;review_status:string};
type CaseItem = {case_id:string;title:string|null;short_brief:string|null;specialty:string|null;difficulty:string|null;status:"draft"|"published"|"archived";latest_version_number:number|null;published_version_number:number|null;versions:Version[]};
type Page = {items:CaseItem[];limit:number;offset:number;has_more:boolean};
type Notice = {text:string;error:boolean}|null;
const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function adminRequest(path:string, method="GET", body?:unknown):Promise<unknown> {
  const { data: { session } } = await createClient().auth.getSession();
  if (!session?.access_token) throw new Error("Your session has expired. Sign in again.");
  const res = await fetch(new URL(`/api/v1/admin/cases${path}`, baseUrl), {
    method, cache:"no-store", headers:{Authorization:`Bearer ${session.access_token}`,
      ...(body!==undefined?{"Content-Type":"application/json"}:{})},
    body: body===undefined?undefined:JSON.stringify(body),
  });
  if (!res.ok) {
    const result:unknown = await res.json().catch(()=>null);
    let msg = `Request failed (HTTP ${res.status})`;
    if (result && typeof result === "object" && "detail" in result) {
      const detail = (result as {detail:unknown}).detail;
      if (typeof detail === "string") msg = detail;
      else if (detail && typeof detail === "object" && "message" in detail) msg = String((detail as {message:unknown}).message);
    }
    throw new Error(msg);
  }
  return res.json();
}

export function AdminCasesManager(){
  const {locale} = useDashboardUI();
  const [page,setPage] = useState<Page|null>(null);
  const [offset,setOffset] = useState(0);
  const [busy,setBusy] = useState(false);
  const [loading,setLoading] = useState(true);
  const [notice,setNotice] = useState<Notice>(null);
  const [selected,setSelected] = useState<string|null>(null);
  const [file,setFile] = useState<File|null>(null);
  const [approvalFile,setApprovalFile] = useState<File|null>(null);
  const [evidence,setEvidence] = useState("");
  const [confirmation,setConfirmation] = useState(false);
  const [filter,setFilter] = useState("");
  const mounted = useRef(true);
  const refresh = useCallback(async (nextOffset=offset)=>{
    setLoading(true);
    try {
      const result=await adminRequest(`?limit=20&offset=${nextOffset}`) as Page;
      if(mounted.current){setPage(result);setOffset(nextOffset);}
    } catch(error){if(mounted.current)setNotice({text:error instanceof Error?error.message:"Could not load cases",error:true});}
    finally{if(mounted.current)setLoading(false);}
  },[offset]);
  useEffect(()=>{mounted.current=true;const frame=requestAnimationFrame(()=>{void refresh();});return()=>{mounted.current=false;cancelAnimationFrame(frame);};},[refresh]);

  async function runAction(path:string, body?:unknown){
    setBusy(true);setNotice(null);
    try {
      const result=await adminRequest(path,"POST",body);
      setNotice({text:typeof result==="object"&&result&&"status" in result?`Success: ${String((result as {status:unknown}).status)}`:"Saved successfully",error:false});
      await refresh(offset);
    } catch(error){setNotice({text:error instanceof Error?error.message:"Request failed",error:true});}
    finally{setBusy(false);}
  }
  async function readJSON(input:File|null){
    if(!input)throw new Error("Choose a JSON file first");
    if(input.size>2*1024*1024)throw new Error("JSON file exceeds 2 MB");
    if(!input.name.toLowerCase().endsWith(".json"))throw new Error("Only .json files are accepted");
    try {return JSON.parse(await input.text()) as unknown;}
    catch {throw new Error("Invalid JSON file");}
  }
  async function importDraft(){
    try {const obj=await readJSON(file);await runAction("/import",obj);setFile(null);}
    catch(error){setNotice({text:error instanceof Error?error.message:"Invalid upload",error:true});}
  }
  async function approve(){
    if(!selected)return;
    if(!confirmation){setNotice({text:"A verified clinician must confirm all three review checks",error:true});return;}
    try {const obj=await readJSON(approvalFile);
      await runAction(`/${encodeURIComponent(selected)}/approve`,{
        blueprint:obj,evidence_reference:evidence,medical_accuracy_confirmed:true,
        privacy_review_confirmed:true,source_review_confirmed:true,
      });setApprovalFile(null);setConfirmation(false);
    } catch(error){setNotice({text:error instanceof Error?error.message:"Invalid upload",error:true});}
  }
  const shown=(page?.items||[]).filter(c=>`${c.case_id} ${c.title||""} ${c.specialty||""}`.toLowerCase().includes(filter.toLowerCase()));
  const active=page?.items.find(item=>item.case_id===selected)||null;
  return <div className="yd-admin-root">
    <div className="yd-admin-head"><div><span className="ydash-kicker">CASE MANAGEMENT / ADMIN</span><h1>{translated(locale,"إدارة الحالات الطبية","Medical case management")}</h1><p>{translated(locale,"إدارة الإصدارات بدون كشف بيانات المريض أو الإجابات للطلاب.","Manage draft versions, reviews and publication safely.")}</p></div><Link href="/dashboard/cases" className="ydash-outline-action">View student library</Link></div>
    <div className="yd-admin-notice" role="note">Drafts are not available to students. Publishing requires a verified clinical reviewer, complete v3.2 validation and a matching immutable approval audit record.</div>
    {notice&&<div role={notice.error?"alert":"status"} className={`yd-admin-notice ${notice.error?"yd-admin-error":"yd-admin-ok"}`}>{notice.text}</div>}
    <section className="yd-admin-import ydash-glass"><div><h2>Import a draft JSON</h2><p>Accepts v3.2 blueprints only. Import never publishes.</p></div><input type="file" accept=".json,application/json" aria-label="Choose draft blueprint JSON" onChange={e=>setFile(e.target.files?.[0]||null)}/><button disabled={busy||!file} onClick={()=>void importDraft()}>Import draft</button></section>
    <div className="yd-admin-toolbar"><label>Search loaded cases <input placeholder="Code, title or specialty" value={filter} onChange={e=>setFilter(e.target.value)} /></label><button disabled={loading} onClick={()=>void refresh()}>Refresh</button></div>
    <section className="yd-admin-grid" aria-busy={loading}>{loading?<div className="yd-admin-empty">Loading cases…</div>:shown.length?shown.map(item=><button key={item.case_id} type="button" className={`yd-admin-card ydash-glass ${selected===item.case_id?"is-selected":""}`} onClick={()=>setSelected(item.case_id)}>
      <span className="yd-admin-card-top"><small>{item.specialty||"Uncategorized"}</small><strong className={`yd-admin-pill yd-admin-${item.status}`}>{item.status}</strong></span>
      <h3>{item.title||item.case_id}</h3><p>{item.short_brief||"No preview provided"}</p><span className="yd-admin-foot">{item.case_id} · v{item.latest_version_number??"—"}<DashboardIcon name="arrow" size={16}/></span>
    </button>):<div className="yd-admin-empty">No cases found. Import a draft to get started.</div>}</section>
    <div className="yd-admin-pages"><button disabled={offset===0||loading} onClick={()=>void refresh(Math.max(0,offset-20))}>Previous</button><span>Page {Math.floor(offset/20)+1}</span><button disabled={!page?.has_more||loading} onClick={()=>void refresh(offset+20)}>Next</button></div>
    {active&&<section className="yd-admin-detail ydash-glass"><div className="yd-admin-detail-head"><div><span className="ydash-kicker">SELECTED CASE</span><h2>{active.title||active.case_id}</h2><p>{active.case_id} · {active.status}</p></div><button aria-label="Close case details" onClick={()=>setSelected(null)}>Close</button></div>
      <div className="yd-admin-versions">{active.versions.map(v=><div key={v.version_number} className="yd-admin-version"><div><strong>Version {v.version_number}</strong><small>{v.review_status} · {v.has_clinical_approval?"Clinician audit verified":"No verified review"} · {v.publication_blocker_count} blocker(s)</small></div><button disabled={busy||active.status==="archived"||!v.has_clinical_approval||v.publication_blocker_count>0} title={!v.has_clinical_approval?"Requires clinician approval first":""} onClick={()=>void runAction(`/${encodeURIComponent(active.case_id)}/versions/${v.version_number}/publish`)}>Publish</button></div>)}</div>
      <div className="yd-admin-actions"><button disabled={busy||active.status==="archived"} onClick={()=>void runAction(`/${encodeURIComponent(active.case_id)}/archive`)}>Archive case</button><button disabled={busy||active.status!=="archived"} onClick={()=>void runAction(`/${encodeURIComponent(active.case_id)}/restore`)}>Restore case</button></div>
      <details className="yd-admin-approval"><summary>Verified clinician approval — controlled workflow</summary><p>Only a pre-authorized clinician/admin account can submit a separately reviewed, fully approved v3.2 JSON. Keep the signed source/review evidence in your private clinical review records; enter only an opaque reference here.</p><input type="file" accept=".json,application/json" aria-label="Clinician-reviewed JSON" onChange={e=>setApprovalFile(e.target.files?.[0]||null)}/><label>Review evidence reference<input value={evidence} maxLength={500} placeholder="internal-review-record-id" onChange={e=>setEvidence(e.target.value)}/></label><label className="yd-admin-check"><input type="checkbox" checked={confirmation} onChange={e=>setConfirmation(e.target.checked)}/> I personally confirm verified medical accuracy, privacy/anonymization and source review of this exact JSON.</label><button disabled={busy||!approvalFile||evidence.trim().length<8||!confirmation} onClick={()=>void approve()}>Submit clinical review</button></details>
    </section>}
  </div>;
}

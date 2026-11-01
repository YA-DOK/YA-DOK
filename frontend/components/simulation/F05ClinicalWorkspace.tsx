"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle, Check, ChevronRight, ClipboardCheck,
  FileText, FlaskConical, Search, ShieldCheck, Stethoscope,
} from "lucide-react";
import { SecureImagingPreview } from "./SecureImagingPreview";
import {
  f03Live, type F03Session,
  type F05ClinicalOptions, type F05ClinicalOption,
} from "@/lib/simulation/f03-live";

type Section = "examination" | "investigations" | "imaging" | "vitals" | "notes";
type ActionType = "examinations" | "investigations";
type Event = F03Session["events"][number];

type Props = {
  session: F03Session;
  section: Section;
  busy: boolean;
  runAction: (action: ActionType, body: Record<string, unknown>) => Promise<boolean>;
};

function prettyName(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

// Render only data returned by the protected F03 request endpoint.
// Never render a raw image storage path or internal answer-key metadata.
const hiddenKeys = new Set([
  "image_asset", "storage_path", "relevance", "teaching_point",
  "leak_terms", "answer_key", "ground_truth", "file_path",
]);
type CaseLabRow = {
  label: string;
  value: string | number;
  unit?: string | null;
  ref_range?: string | null;
  flag?: string | null;
};

// A lab panel is a collection of measurements from the *case-defined* result.
// We deliberately render only these patient-facing fields, not internal metadata.
function isCaseLabRow(value: unknown): value is CaseLabRow {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const row = value as Record<string, unknown>;
  return typeof row.label === "string" &&
    (typeof row.value === "string" || typeof row.value === "number");
}

function LabResultTable({ rows }: { rows: CaseLabRow[] }) {
  return <div className="f05ui_labScroll" role="region" aria-label="Laboratory result measurements" tabIndex={0}>
    <table className="f05ui_labTable">
      <thead><tr>
        <th scope="col">Parameter</th>
        <th scope="col">Result</th>
        <th scope="col">Reference</th>
        <th scope="col">Flag</th>
      </tr></thead>
      <tbody>
        {rows.map((row, index) => {
          const flag = typeof row.flag === "string" ? row.flag.trim() : "";
          const kind = flag.toLowerCase();
          const flagClass = kind === "high" || kind === "low" || kind === "critical"
            ? "f05ui_labFlagAlert" : kind === "normal" ? "f05ui_labFlagNormal" : "f05ui_labFlagNeutral";
          return <tr key={`${row.label}-${index}`}>
            <th scope="row">{row.label}</th>
            <td><strong>{row.value}</strong>{row.unit && <small>{row.unit}</small>}</td>
            <td>{row.ref_range || <span className="f05ui_labMuted">Not specified</span>}</td>
            <td><span className={`f05ui_labFlag ${flagClass}`}>{flag || "—"}</span></td>
          </tr>;
        })}
      </tbody>
    </table>
  </div>;
}

function ClinicalResult({ value, sessionId, imageId }: { value: unknown; sessionId?: string; imageId?: string }) {
  if (value === null || value === undefined || value === "") {
    return <p className="f05ui_missing">No case-defined result is available.</p>;
  }
  if (typeof value !== "object") {
    return <span className="f05ui_resultValue">{String(value)}</span>;
  }
  if (Array.isArray(value)) {
    if (!value.length) return <p className="f05ui_missing">No case-defined result is available.</p>;
    if (value.every(isCaseLabRow)) return <LabResultTable rows={value}/>;
    return <div className="f05ui_resultRows">
      {value.map((item, index) => <div className="f05ui_resultRow" key={index}>
        <ClinicalResult value={item} sessionId={sessionId} imageId={imageId}/>
      </div>)}
    </div>;
  }
  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([key]) => !hiddenKeys.has(key))
    .filter(([key, val]) => key !== "image_available" || val === true)
    .filter(([key]) => key !== "image_status");
  return <dl className="f05ui_resultList">
    {entries.map(([key, val]) => {
      if (key === "image_available") {
        return <div className="f05ui_resultEntry" key={key}>
          <dt>Image</dt><dd>{sessionId && imageId ? <SecureImagingPreview sessionId={sessionId} imageId={imageId}/> : "Unavailable"}</dd>
        </div>;
      }
      return <div className="f05ui_resultEntry" key={key}>
        <dt>{prettyName(key)}</dt>
        <dd><ClinicalResult value={val} sessionId={sessionId} imageId={imageId}/></dd>
      </div>;
    })}
  </dl>;
}


// A physical finding is descriptive clinical data, not a numeric observation.
// The F02 converter may emit placeholder value/unit strings even when `finding`
// contains the actual recorded examination result. Do not show placeholders.
function PhysicalExamResult({ value }: { value: unknown }) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return <ClinicalResult value={value}/>;
  }
  const result = value as Record<string, unknown>;
  const finding = typeof result.finding === "string" ? result.finding.trim() : "";
  if (!finding) return <ClinicalResult value={value}/>;

  const raw = result.value;
  const hasMeasurement = (typeof raw === "string" || typeof raw === "number") &&
    String(raw).trim().length > 0 &&
    !/^no case-defined result is available\.?$/i.test(String(raw).trim());
  const unit = typeof result.unit === "string" &&
    !/^no case-defined result is available\.?$/i.test(result.unit.trim())
      ? result.unit.trim() : "";

  return <div className="f05ui_findingBlock">
    <span className="f05ui_findingEyebrow">EXAMINATION FINDING</span>
    <p className="f05ui_findingText">{finding}</p>
    {hasMeasurement && <p className="f05ui_findingMeasure">
      Recorded measurement: <strong>{String(raw)}{unit ? ` ${unit}` : ""}</strong>
    </p>}
  </div>;
}

// This is an illustrative, third-party recording of pneumonia crackles,
// NOT a recording of the simulated patient. It is deliberately mapped to
// the exact authored case version and only shown AFTER the saved examination.
// A clinician must review the case/audio pairing before clinical assessment use.
function eventFor(events: Event[], id: string): Event | undefined {
  const normalized = id.trim().toLowerCase();
  return [...events].reverse().find((event) =>
    String(event.details.name ?? "").trim().toLowerCase() === normalized
  );
}

function statusFor(event: Event | undefined): "done" | "unavailable" | "new" {
  if (!event) return "new";
  const status = String(event.details.status ?? "").toLowerCase();
  return event.details.available === false || status === "unavailable" ? "unavailable" : "done";
}

export default function F05ClinicalWorkspace({ session, section, busy, runAction }: Props) {
  const [options, setOptions] = useState<F05ClinicalOptions | null>(null);
  const [loadError, setLoadError] = useState("");
  const [search, setSearch] = useState("");
  const [selection, setSelection] = useState("");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setOptions(null);
    setLoadError("");
    void f03Live.clinicalOptions(session.session_id)
      .then((result) => { if (!cancelled) setOptions(result); })
      .catch((error: unknown) => {
        if (!cancelled) setLoadError(error instanceof Error ? error.message : "Could not load clinical tools.");
      });
    return () => { cancelled = true; };
  }, [session.session_id]);

  useEffect(() => {
    setSelection("");
    setSearch("");
    setShowAll(false);
  }, [section]);

  const isExam = section === "examination" || section === "vitals";
  // Clinical actions are phase-independent in the F03/F04 stabilized workflow.
  const canOrder = !busy && !session.is_paused && !session.is_completed;
  const source = useMemo(() => {
    if (!options) return [];
    if (section === "imaging") return options.imaging;
    if (section === "investigations") return options.investigations;
    if (section === "vitals") return options.examinations.filter((item) => item.category.toLowerCase() === "vitals");
    return options.examinations;
  }, [options, section]);

  const matching = useMemo(() => {
    const query = search.trim().toLowerCase();
    return source.filter((item) => !query || `${item.label} ${item.id} ${item.category}`.toLowerCase().includes(query));
  }, [source, search]);

  const relevantEvents = useMemo(() => session.events.filter((event) => {
    if (isExam) return event.event_type === "examination_requested";
    return event.event_type === "investigation_requested";
  }), [session.events, isExam]);

  const sectionEvents = useMemo(() => {
    const known = new Set(source.map((item) => item.id.toLowerCase()));
    if (section === "imaging" || section === "vitals") {
      return relevantEvents.filter((event) => known.has(String(event.details.name ?? "").toLowerCase()));
    }
    if (section === "investigations" && options) {
      const imageIds = new Set(options.imaging.map((item) => item.id.toLowerCase()));
      return relevantEvents.filter((event) => !imageIds.has(String(event.details.name ?? "").toLowerCase()));
    }
    return relevantEvents;
  }, [relevantEvents, source, section, options]);

  const saved = useMemo(() => {
    const map = new Map<string, Event>();
    for (const event of sectionEvents) {
      const key = String(event.details.name ?? "").toLowerCase();
      if (!key) continue;
      // Preserve the original recorded result if a repeated request has no new result.
      if (!event.details.repeated || !map.has(key)) map.set(key, event);
    }
    return map;
  }, [sectionEvents]);

  const recent = selection ? eventFor(sectionEvents, selection) : undefined;
  const previous = selection ? saved.get(selection.toLowerCase()) : undefined;
  const shown = recent?.details.repeated ? previous ?? recent : recent;
  const selectedOption = source.find((item) => item.id === selection);
  const visible = search.trim() || showAll ? matching : matching.slice(0, 12);
  const countCompleted = [...saved.values()].filter((event) => statusFor(event) === "done").length;

  if (section === "notes") {
    const clinicalEvents = session.events.filter((event) =>
      event.event_type === "examination_requested" || event.event_type === "investigation_requested"
    );
    return <div className="f05ui_body f05ui_notes">
      <div className="f05ui_summary">
        <ClipboardCheck size={17}/>
        <span>{clinicalEvents.length} saved clinical action{clinicalEvents.length === 1 ? "" : "s"} in this session</span>
      </div>
      <div className="f05ui_notesList">
        {!clinicalEvents.length && <div className="f05ui_empty">No examinations or investigations have been requested yet.</div>}
        {[...clinicalEvents].reverse().map((event) => <article key={event.event_id} className="f05ui_note">
          <FileText size={17}/>
          <div><strong>{prettyName(String(event.details.name ?? "Clinical request"))}</strong>
            <span>{event.event_type === "examination_requested" ? "Examination" : "Investigation"} · {statusFor(event) === "unavailable" ? "Unavailable" : "Saved"}</span>
          </div>
        </article>)}
      </div>
    </div>;
  }

  return <div className="f05ui_body">
    <div className="f05ui_ready" role="status">
      <ShieldCheck size={17}/>
      <span>{canOrder ? "Clinical tools are available throughout your active session." : "View saved results. Ordering is unavailable for this session."}</span>
    </div>

    {section === "imaging" && <div className="f05ui_info">
      <AlertCircle size={16}/>
      <span>Reports are case-defined. Images can be opened securely after ordering, if the case asset is stored in the configured private bucket.</span>
    </div>}

    <label className="f05ui_search">
      <Search size={19} aria-hidden="true"/>
      <input
        type="search"
        aria-label={`Search ${section} tools`}
        placeholder={section === "vitals" ? "Search vital signs..." : section === "examination" ? "Search examinations..." : "Search available tests..."}
        value={search}
        onChange={(event) => { setSearch(event.target.value); setShowAll(false); }}
      />
      {options && <span className="f05ui_searchCount">{matching.length} tools</span>}
    </label>

    <div className="f05ui_catalogueHeader">
      <strong>{section === "vitals" ? "Measurements" : section === "examination" ? "Physical examinations" : section === "imaging" ? "Imaging studies" : "Laboratory investigations"}</strong>
      <span>{countCompleted} completed</span>
    </div>

    <div className="f05ui_listScroll">
      {loadError && <div className="f05ui_error" role="alert">{loadError}</div>}
      {!options && !loadError && <div className="f05ui_empty">Loading clinical tools…</div>}
      {options && !matching.length && <div className="f05ui_empty">{search ? "No results match your search." : "No tools are defined for this category in this case."}</div>}
      <div className="f05ui_cardGrid">
        {visible.map((item: F05ClinicalOption) => {
          const past = saved.get(item.id.toLowerCase());
          const outcome = statusFor(past);
          const isCurrent = selection === item.id;
          const already = outcome !== "new";
          const disabled = !already && !canOrder;
          return <button
            key={item.id}
            type="button"
            className={`f05ui_testCard ${isCurrent ? "f05ui_testCardActive" : ""}`}
            aria-pressed={isCurrent}
            disabled={disabled}
            onClick={() => {
              setSelection(item.id);
              if (already) return;
              const action: ActionType = isExam ? "examinations" : "investigations";
              const body = isExam ? { examination_name: item.id } : { investigation_name: item.id };
              void runAction(action, body);
            }}
          >
            <span className="f05ui_testIcon">{isExam ? <Stethoscope size={20}/> : <FlaskConical size={20}/>}</span>
            <span className="f05ui_testText"><strong>{item.label}</strong><small>{prettyName(item.category)}</small>
              <span className={`f05ui_status f05ui_status_${outcome}`}>
                {outcome === "done" ? <Check size={13}/> : outcome === "unavailable" ? <AlertCircle size={13}/> : <ChevronRight size={13}/>}
                {outcome === "done" ? "Result saved" : outcome === "unavailable" ? "Unavailable" : canOrder ? "Request" : "Not requested"}
              </span>
            </span>
          </button>;
        })}
      </div>
      {!search.trim() && !showAll && matching.length > visible.length && <button
        type="button" className="f05ui_showMore" onClick={() => setShowAll(true)}
      >Browse all {matching.length} tools <ChevronRight size={15}/></button>}
      {selection && <div className="f05ui_resultPanel" aria-live="polite">
        <div className="f05ui_resultPanelHeader">
          <div><span>CLINICAL RESULT</span><h4>{selectedOption?.label ?? prettyName(selection)}</h4></div>
          <span className={`f05ui_status f05ui_status_${statusFor(shown)}`}>{statusFor(shown) === "done" ? "Saved" : statusFor(shown) === "unavailable" ? "Unavailable" : "Pending"}</span>
        </div>
        {shown ? <>
          {isExam ? <PhysicalExamResult value={shown.details.result}/> : <ClinicalResult value={shown.details.result} sessionId={session.session_id} imageId={section === "imaging" ? selection : undefined}/>}
        </> : <p className="f05ui_missing">{busy ? "Saving your request…" : "Select a tool to request and view its result."}</p>}
      </div>}
    </div>
    <div className="f05ui_footer"><ClipboardCheck size={16}/> {sectionEvents.length} recorded request{sectionEvents.length === 1 ? "" : "s"} · saved with your simulation session</div>
  </div>;
}

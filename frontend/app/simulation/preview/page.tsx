"use client";
import Link from "next/link";
import { useF03Session } from "@/lib/simulation/use-f03-session";
import { createClient } from "@/lib/supabase/client";

import { useEffect, useState, type FormEvent } from "react";
import {
  Activity, ClipboardList, FlaskConical, HeartPulse,
  Image as ImageIcon, Lightbulb, Menu, MessageCircle,
  Mic, Pause, Play, Send, Stethoscope, Thermometer,
  UserRound, X, Clock3, Keyboard, ChevronRight,
  Volume2, CheckCircle2, GraduationCap, ClipboardCheck, LayoutDashboard,
} from "lucide-react";
const styles = {
  "activeTool": "ydokpreview_activeTool",
  "assistantArea": "ydokpreview_assistantArea",
  "avatarIcon": "ydokpreview_avatarIcon",
  "body": "ydokpreview_body",
  "brand": "ydokpreview_brand",
  "brandSub": "ydokpreview_brandSub",
  "cardHeading": "ydokpreview_cardHeading",
  "chatDrawer": "ydokpreview_chatDrawer",
  "chatForm": "ydokpreview_chatForm",
  "child": "ydokpreview_child",
  "clinicWindow": "ydokpreview_clinicWindow",
  "clipboard": "ydokpreview_clipboard",
  "closeMini": "ydokpreview_closeMini",
  "demoLabel": "ydokpreview_demoLabel",
  "desk": "ydokpreview_desk",
  "dock": "ydokpreview_dock",
  "dockButton": "ydokpreview_dockButton",
  "drawer": "ydokpreview_drawer",
  "drawerDetail": "ydokpreview_drawerDetail",
  "drawerHeader": "ydokpreview_drawerHeader",
  "encounterCard": "ydokpreview_encounterCard",
  "endButton": "ydokpreview_endButton",
  "environment": "ydokpreview_environment",
  "examBed": "ydokpreview_examBed",
  "face": "ydokpreview_face",
  "fallback": "ydokpreview_fallback",
  "figure": "ydokpreview_figure",
  "figures": "ydokpreview_figures",
  "glass": "ydokpreview_glass",
  "greenDot": "ydokpreview_greenDot",
  "hair": "ydokpreview_hair",
  "hintBubble": "ydokpreview_hintBubble",
  "hintOrb": "ydokpreview_hintOrb",
  "iconButton": "ydokpreview_iconButton",
  "initials": "ydokpreview_initials",
  "keyboardIcon": "ydokpreview_keyboardIcon",
  "logTime": "ydokpreview_logTime",
  "message": "ydokpreview_message",
  "micCircle": "ydokpreview_micCircle",
  "modal": "ydokpreview_modal",
  "modalActions": "ydokpreview_modalActions",
  "modalOverlay": "ydokpreview_modalOverlay",
  "modeButton": "ydokpreview_modeButton",
  "mother": "ydokpreview_mother",
  "overlay": "ydokpreview_overlay",
  "patientCard": "ydokpreview_patientCard",
  "patientLine": "ydokpreview_patientLine",
  "photoReady": "ydokpreview_photoReady",
  "poster": "ydokpreview_poster",
  "previewTag": "ydokpreview_previewTag",
  "profile": "ydokpreview_profile",
  "railButton": "ydokpreview_railButton",
  "railSeparator": "ydokpreview_railSeparator",
  "root": "ydokpreview_root",
  "scenePhoto": "ydokpreview_scenePhoto",
  "sceneShade": "ydokpreview_sceneShade",
  "shelf": "ydokpreview_shelf",
  "status": "ydokpreview_status",
  "studentMessage": "ydokpreview_studentMessage",
  "subtle": "ydokpreview_subtle",
  "successIcon": "ydokpreview_successIcon",
  "timer": "ydokpreview_timer",
  "toast": "ydokpreview_toast",
  "toolChoice": "ydokpreview_toolChoice",
  "toolList": "ydokpreview_toolList",
  "toolRail": "ydokpreview_toolRail",
  "toolSelected": "ydokpreview_toolSelected",
  "topBar": "ydokpreview_topBar",
  "topCenter": "ydokpreview_topCenter",
  "transcript": "ydokpreview_transcript",
  "vitalGrid": "ydokpreview_vitalGrid",
  "vitalItem": "ydokpreview_vitalItem",
  "vitalName": "ydokpreview_vitalName",
  "vitalsDisclaimer": "ydokpreview_vitalsDisclaimer",
  "vitalsHeading": "ydokpreview_vitalsHeading",
  "vitalsPanel": "ydokpreview_vitalsPanel",
  "voiceButton": "ydokpreview_voiceButton",
  "voiceText": "ydokpreview_voiceText",
  "waveform": "ydokpreview_waveform",
} as const;

type ToolId = "investigations" | "imaging" | "examination" | "vitals" | "notes";
type ChatMessage = {
  id: number;
  role: "student" | "system";
  text: string;
  time: string;
};

const tools = [
  { id: "investigations", label: "Investigations", Icon: FlaskConical },
  { id: "imaging", label: "Imaging", Icon: ImageIcon },
  { id: "examination", label: "Physical Examination", Icon: Stethoscope },
  { id: "vitals", label: "Vital Signs", Icon: HeartPulse },
  { id: "notes", label: "Encounter Notes", Icon: ClipboardList },
] as const;

const vitals = [
  { name: "Heart Rate", short: "HR", value: "92", unit: "bpm", Icon: HeartPulse },
  { name: "Respiratory Rate", short: "RR", value: "20", unit: "/min", Icon: Activity },
  { name: "Temperature", short: "Temp", value: "36.8", unit: "°C", Icon: Thermometer },
  { name: "Blood Pressure", short: "BP", value: "102/68", unit: "mmHg", Icon: HeartPulse },
  { name: "Oxygen Saturation", short: "SpO₂", value: "98", unit: "%", Icon: Activity },
];

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

export default function SimulationPreview() {
  const {
    session: liveSession,
    mode,
    elapsed,
    paused,
    ended,
    busy,
    error: liveError,
    currentPhase,
    nextPhase,
    runAction,
    finish,
    restart,
  } = useF03Session();
  const [toolsOpen, setToolsOpen] = useState(false);
  const [toolPanelOpen, setToolPanelOpen] = useState(false);
  const [studentName, setStudentName] = useState("Student");
  const [selectedTool, setSelectedTool] = useState<ToolId>("examination");
  const [chatOpen, setChatOpen] = useState(false);
  const [hintOpen, setHintOpen] = useState(false);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [sceneLoaded, setSceneLoaded] = useState(false);
  const [draft, setDraft] = useState("");
  const [notice, setNotice] = useState("");
  const [diagnosisText, setDiagnosisText] = useState("");
  const [planText, setPlanText] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "system",
      text: "UI preview. Session transcript will load from the backend after integration.",
      time: "00:00",
    },
  ]);


  const studentInitials = studentName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => Array.from(part)[0]?.toUpperCase() ?? "")
    .join("") || "ST";

  useEffect(() => {
    let cancelled = false;
    const supabase = createClient();

    void supabase.auth.getUser().then(({ data, error }) => {
      if (cancelled) return;
      const user = data.user;
      if (error || !user) {
        setStudentName("Guest Preview");
        return;
      }
      const meta = user.user_metadata ?? {};
      const name = [meta.full_name, meta.name, meta.display_name]
        .find((value) => typeof value === "string" && value.trim());

      setStudentName(
        typeof name === "string"
          ? name.trim()
          : user.email?.split("@")[0] || "Student"
      );
    }).catch(() => {
      if (!cancelled) setStudentName("Guest Preview");
    });

    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setToolsOpen(false);
      setToolPanelOpen(false);
      setChatOpen(false);
      setHintOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);





  const testSeconds = Math.max(0, 15 * 60 - elapsed);
  const time = formatTime(mode === "test" ? testSeconds : elapsed);
  const activeTool = tools.find((tool) => tool.id === selectedTool) ?? tools[0];

  function sendDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.trim() || paused || ended) return;

    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        role: "student",
        text: draft.trim(),
        time: formatTime(elapsed),
      },
    ]);
    setDraft("");
    setNotice("Preview only: question not sent to the Patient AI.");
  }

  function resetPreview() {
    restart();
  }


  const displayMessages: ChatMessage[] = [
    ...(liveSession?.messages ?? [])
      .filter(
        (message) =>
          message.role !== "system" ||
          ["examination_result", "investigation_result"].includes(
            message.action
          )
      )
      .map((message, index) => ({
        id: -(index + 1),
        role: message.role === "user" ? "student" as const : "system" as const,
        text: message.content,
        time: "Saved",
      })),
    ...messages,
  ];

  return (
    <main className={styles.root}>
      <link rel="stylesheet" href="/simulation/preview-ui.css" />
      <div className={styles.environment} aria-hidden="true">
        <div className={styles.fallback}>
          <div className={styles.poster}>YA-DOK<br /><span>CARE · LEARN · GROW</span></div>
          <div className={styles.clinicWindow} />
          <div className={styles.shelf} />
          <div className={styles.examBed} />
          <div className={styles.figures}>
            <div className={`${styles.figure} ${styles.child}`}>
              <div className={styles.hair} />
              <div className={styles.face} />
              <div className={styles.body} />
            </div>
            <div className={`${styles.figure} ${styles.mother}`}>
              <div className={styles.hair} />
              <div className={styles.face} />
              <div className={styles.body} />
            </div>
          </div>
          <div className={styles.desk} />
          <div className={styles.clipboard} />
        </div>
        <img
          className={`${styles.scenePhoto} ${sceneLoaded ? styles.photoReady : ""}`}
          src="/simulation/clinic-scene.webp"
          alt=""
          onLoad={() => setSceneLoaded(true)}
          onError={() => setSceneLoaded(false)}
        />
      </div>

      <div className={styles.sceneShade} />

      <header className={styles.topBar}>
        <div className={`${styles.glass} ${styles.brand}`}>
          <HeartPulse size={26} />
          <strong>YA-DOK</strong>
          <span className={styles.brandSub}>Clinical Simulation</span>
        </div>

        <div className={styles.topCenter}>
          <span className={`${styles.glass} ${styles.status}`}>
            <i className={styles.greenDot} />
            {!liveSession
              ? "Connecting"
              : ended ? "Completed" : paused ? "Paused" : "In Session"}
          </span>

          <div
            className={`${styles.glass} ${styles.modeButton}`}
            title="Session mode is selected before starting"
          >
            {mode === "training" ? (
              <>
                <GraduationCap size={18} strokeWidth={2} />
                <span>TRAIN MODE</span>
              </>
            ) : (
              <>
                <ClipboardCheck size={18} strokeWidth={2} />
                <span>TEST MODE</span>
              </>
            )}
          </div>

          <div className={`${styles.glass} ${styles.timer}`}>
            <Clock3 size={17} />
            <strong>{time}</strong>
            <small>{mode === "test" ? "Remaining" : "Elapsed"}</small>
          </div>
        </div>

        <div className={`${styles.glass} ${styles.profile}`}>
          <div className={styles.initials}>{studentInitials}</div>
          <div className="ydokpreview_profileText">
            <strong title={studentName}>{studentName}</strong>
            <small>Medical Student</small>
          </div>
        </div>
      </header>

      
      <aside
        className={`${styles.glass} ${styles.toolRail} ${
          toolsOpen ? "ydokpreview_railExpanded" : ""
        }`}
        aria-label="Clinical tools"
      >
        <button
          type="button"
          className={`${styles.railButton} ydokpreview_railToggle`}
          aria-label={toolsOpen ? "Collapse sidebar" : "Expand sidebar"}
          aria-expanded={toolsOpen}
          onClick={() => setToolsOpen((value) => !value)}
          title="Clinical Tools"
        >
          {toolsOpen ? <X size={21}/> : <Menu size={21}/>}
          {toolsOpen && <span className="ydokpreview_railLabel">Clinical Tools</span>}
        </button>

        <div className={styles.railSeparator}/>

        {tools.map(({ id, label, Icon }) => (
          <button
            type="button"
            key={id}
            title={label}
            aria-label={label}
            aria-pressed={selectedTool === id}
            className={`${styles.railButton} ${
              selectedTool === id ? styles.activeTool : ""
            }`}
            onClick={() => {
              setSelectedTool(id);
              setToolPanelOpen(true);
            }}
          >
            <Icon size={21} strokeWidth={1.9}/>
            {toolsOpen && <span className="ydokpreview_railLabel">{label}</span>}
          </button>
        ))}

        <div className="ydokpreview_railSpacer"/>

        <Link
          href={`/dashboard/cases?specialty=Pediatrics&mode=${mode}`}
          className="ydokpreview_railLink"
          title="Back to Case Library"
          aria-label="Back to Case Library"
        >
          <LayoutDashboard size={20}/>
          {toolsOpen && <span className="ydokpreview_railLabel">Case Library</span>}
        </Link>
      </aside>

      <section className={`${styles.glass} ${styles.patientCard}`}>
        <div className={styles.cardHeading}><UserRound size={18} /> Patient Information</div>
        <div className={styles.patientLine}>
          <span className={styles.avatarIcon}>OK</span>
          <div><strong>Omar K. <small>(6 yrs)</small></strong><p>Male · 6 years · 18 kg</p></div>
        </div>
        <div className={styles.patientLine}>
          <span className={styles.avatarIcon}>M</span>
          <div><strong>Guardian</strong><p>Mother (Mariam)</p></div>
        </div>
        <span className={styles.previewTag}>Synthetic UI data</span>
      </section>

      <section className={`${styles.glass} ${styles.encounterCard}`}>
        <div className={styles.cardHeading}><ClipboardList size={18} /> Encounter Log</div>
        <p>Phase: {currentPhase.replaceAll("_", " ")}</p>
        <p className={styles.subtle}>
          {liveSession
            ? `${liveSession.events.length} saved events`
            : "Connecting to backend..."}
        </p>
        {nextPhase && nextPhase !== "completed" && (
          <button
            type="button"
            className={styles.dockButton}
            style={{ minHeight: 36, width: "100%", marginTop: 12 }}
            disabled={!liveSession || busy || paused || ended}
            onClick={() => void runAction("phase", { phase: nextPhase })}
          >
            Next: {nextPhase.replaceAll("_", " ")}
          </button>
        )}
        <div className={styles.logTime}><Clock3 size={14} /> {formatTime(elapsed)}</div>
      </section>

      <section className={`${styles.glass} ${styles.vitalsPanel}`}>
        <div className={styles.vitalsHeading}>
          <span><Activity size={19} /> Vital Signs</span>
          <small>Sample readings</small>
        </div>
        <div className={styles.vitalGrid}>
          {vitals.map(({ name, short, value, unit, Icon }) => (
            <div className={styles.vitalItem} key={name} title={name}>
              <span className={styles.vitalName}><Icon size={16} />{short}</span>
              <strong>{value}</strong>
              <small>{unit}</small>
            </div>
          ))}
        </div>
        <p className={styles.vitalsDisclaimer}>Preview only · Real readings will follow F05 access rules.</p>
      </section>

      {mode === "training" && !ended && (
        <div className={styles.assistantArea}>
          {hintOpen && (
            <div className={`${styles.glass} ${styles.hintBubble}`}>
              <button
                className={styles.closeMini}
                aria-label="Close assistant"
                onClick={() => setHintOpen(false)}
              ><X size={15} /></button>
              <strong><Lightbulb size={15} /> YA-DOK Assistant</strong>
              <p>Try asking the guardian when the symptoms started and what happened next.</p>
              <small>Example hint · F06 integration pending</small>
            </div>
          )}
          <button
            className={styles.hintOrb}
            onClick={() => setHintOpen((value) => !value)}
            aria-label="Toggle training assistant"
            title="Training assistant"
          >
            <Lightbulb size={28} />
          </button>
        </div>
      )}

      <footer className={`${styles.glass} ${styles.dock}`}>
        <button className={styles.dockButton} onClick={() => void runAction(paused ? "resume" : "pause")}
          disabled={!liveSession || busy || ended}>
          {paused ? <Play size={18} /> : <Pause size={18} />}
          <span>{paused ? "Resume" : "Pause"}</span>
        </button>

        <button className={styles.dockButton} onClick={() => setChatOpen(true)}>
          <MessageCircle size={18} />
          <span>Chat History</span>
        </button>

        <button
          className={styles.voiceButton}
          onClick={() => {
            setChatOpen(true);
            setNotice("Voice STT/TTS will be connected in Feature 11. Use text fallback for now.");
          }}
        >
          <span className={styles.micCircle}><Mic size={22} /></span>
          <span className={styles.waveform}>▂▆█▃▇▅▂</span>
          <span className={styles.voiceText}>Start speaking to your patient...</span>
          <Keyboard size={17} className={styles.keyboardIcon} />
        </button>

        <button className={styles.endButton} onClick={() => setConfirmEnd(true)} disabled={ended}>
          <span>End Session</span>
          <ChevronRight size={18} />
        </button>
      </footer>

      <div className={styles.demoLabel}>SYNTHETIC CASE - LOCAL PG SESSION</div>
      {(notice || liveError) && (
        <div
          className={styles.toast}
          role={liveError ? "alert" : "status"}
          onClick={() => setNotice("")}
        >
          {liveError || notice}
          <X size={14} />
        </div>
      )}

      {toolPanelOpen && (
        <div className={styles.overlay} onClick={() => setToolPanelOpen(false)}>
          <aside className={styles.drawer} onClick={(event) => event.stopPropagation()}>
            <div className={styles.drawerHeader}>
              <div><small>CLINICAL WORKSPACE</small><h2>Diagnostic Tools</h2></div>
              <button className={styles.iconButton} onClick={() => setToolPanelOpen(false)} aria-label="Close tools"><X /></button>
            </div>
            <div className={styles.toolList}>
              {tools.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  className={`${styles.toolChoice} ${selectedTool === id ? styles.toolSelected : ""}`}
                  onClick={() => setSelectedTool(id)}
                >
                  <Icon size={19} /> {label} <ChevronRight size={15} />
                </button>
              ))}
            </div>
            <div className={styles.drawerDetail}>
              <activeTool.Icon size={27} />
              <h3>{activeTool.label}</h3>
              <p>This clinical workspace is ready for its Feature 05 data and actions. No examination or investigation result is invented in this preview.</p>
              <span>Awaiting clinical module integration</span>
            </div>
          </aside>
        </div>
      )}

      {chatOpen && (
        <div className={styles.overlay} onClick={() => setChatOpen(false)}>
          <aside className={`${styles.drawer} ${styles.chatDrawer}`} onClick={(event) => event.stopPropagation()}>
            <div className={styles.drawerHeader}>
              <div><small>TEXT FALLBACK</small><h2>Session Transcript</h2></div>
              <button className={styles.iconButton} aria-label="Close chat" onClick={() => setChatOpen(false)}><X /></button>
            </div>
            <div className={styles.transcript}>
              {displayMessages.map((message) => (
                <div key={message.id} className={`${styles.message} ${message.role === "student" ? styles.studentMessage : ""}`}>
                  <small>{message.role === "student" ? "You · Draft" : "System"} · {message.time}</small>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>
            <form className={styles.chatForm} onSubmit={sendDraft}>
              <input
                aria-label="Type a message"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Type a question (preview only)..."
                disabled={paused || ended}
              />
              <button type="submit" aria-label="Add preview message" disabled={!draft.trim() || paused || ended}><Send size={18} /></button>
            </form>
          </aside>
        </div>
      )}

      {confirmEnd && (
        <div className={styles.modalOverlay}>
          <div className={`${styles.glass} ${styles.modal}`} role="dialog" aria-modal="true" aria-labelledby="end-title">
            <h2 id="end-title">End this session preview?</h2>
            <p>
              Finish the previous phases, then submit your diagnosis and
              treatment plan to complete this saved session.
            </p>
            {currentPhase === "diagnosis_and_plan" && !liveSession?.diagnosis && (
              <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
                <textarea
                  aria-label="Diagnosis"
                  placeholder="Your diagnosis"
                  value={diagnosisText}
                  onChange={(e) => setDiagnosisText(e.target.value)}
                  style={{ padding: 12, background: "#18342d", color: "white", borderRadius: 10 }}
                />
                <textarea
                  aria-label="Treatment plan"
                  placeholder="Your treatment plan"
                  value={planText}
                  onChange={(e) => setPlanText(e.target.value)}
                  style={{ padding: 12, background: "#18342d", color: "white", borderRadius: 10 }}
                />
              </div>
            )}
            <div className={styles.modalActions}>
              <button className={styles.dockButton} onClick={() => setConfirmEnd(false)}>Cancel</button>
              <button
              className={styles.endButton}
              disabled={!liveSession || busy || currentPhase !== "diagnosis_and_plan"}
              onClick={() => {
                void finish(diagnosisText, planText).then((done) => {
                  if (done) setConfirmEnd(false);
                });
              }}
            >
              {busy ? "Saving..." : "Submit & Complete"}
            </button>
            </div>
          </div>
        </div>
      )}

      {ended && (
        <div className={styles.modalOverlay}>
          <div className={`${styles.glass} ${styles.modal}`} role="status">
            <CheckCircle2 size={36} className={styles.successIcon} />
            <h2>Preview finished</h2>
            <p>This synthetic session was completed and saved in local PostgreSQL.</p>
            <div className={styles.modalActions}>
              <a className={styles.dockButton} href="/dashboard">Dashboard</a>
              <button className={styles.endButton} onClick={resetPreview}>Try Again</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

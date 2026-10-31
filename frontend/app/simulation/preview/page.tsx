"use client";
import Link from "next/link";
import { useF03Session } from "@/lib/simulation/use-f03-session";
import { createClient } from "@/lib/supabase/client";
import { useF04PatientChat } from "@/lib/simulation/use-f04-patient-chat";

import { useEffect, useRef, useState } from "react";
import {
  Activity, ClipboardList, FlaskConical, HeartPulse,
  Image as ImageIcon, Lightbulb, Menu, MessageCircle,
  Mic, Pause, Play, Send, Stethoscope, Thermometer,
  UserRound, X, Clock3, ChevronRight,
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
  role: "student" | "patient";
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
  { name: "Heart Rate", short: "HR", value: "--", unit: "bpm", Icon: HeartPulse },
  { name: "Respiratory Rate", short: "RR", value: "--", unit: "/min", Icon: Activity },
  { name: "Temperature", short: "Temp", value: "--", unit: "°C", Icon: Thermometer },
  { name: "Blood Pressure", short: "BP", value: "--", unit: "mmHg", Icon: HeartPulse },
  { name: "Oxygen Saturation", short: "SpO₂", value: "--", unit: "%", Icon: Activity },
];

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

export default function SimulationPreview() {
  const {
    session: liveSession,
    caseCode,
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
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [sceneLoaded, setSceneLoaded] = useState(false);
  const [diagnosisText, setDiagnosisText] = useState("");
  const [planText, setPlanText] = useState("");

  // F04_PREVIEW_CHAT_V07: patient chat belongs to the current F03 session.
  const sessionId = liveSession?.session_id;
  const patientChat = useF04PatientChat(sessionId);
  const chatTailRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (chatOpen) chatTailRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [chatOpen, patientChat.messages.length]);
  const canChat = Boolean(liveSession) && currentPhase === "history_taking" && !paused && !ended && !busy;
  // F04_SCENE_CHAT_V08: the drawer is history-only; compose in the clinic dock.
  const latestPatientReply = [...patientChat.messages].reverse().find((item) => item.role === "patient")?.content;


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
        setStudentName("Student");
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
      if (!cancelled) setStudentName("Student");
    });

    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setToolsOpen(false);
      setToolPanelOpen(false);
      setChatOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);





  const hasTestDeadline = mode === "test" && typeof liveSession?.duration_minutes === "number" && liveSession.duration_minutes > 0;
  const remainingSeconds = hasTestDeadline ? Math.max(0, liveSession!.duration_minutes! * 60 - elapsed) : elapsed;
  const time = formatTime(remainingSeconds);
  const activeTool = tools.find((tool) => tool.id === selectedTool) ?? tools[0];

  function resetPreview() {
    restart();
  }


  const displayMessages: ChatMessage[] = patientChat.messages.map((message, index) => ({
    id: index,
    role: message.role,
    text: message.content,
    time: "Saved",
  }));

  function openPatientChat() {
    setChatOpen(true);
    if (sessionId) void patientChat.retryRefresh();
  }

  return (
    <main className={styles.root}>
      <link rel="stylesheet" href="/simulation/preview-ui.css" />
      <link rel="stylesheet" href="/simulation/f04-inline-chat-v08.css" />
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
            <small>{hasTestDeadline ? "Remaining" : "Elapsed"}</small>
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
            title={`${label} - F05 pending`}
            aria-label={`${label} - F05 pending`}
            disabled
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
          href={`/dashboard/cases?mode=${mode}`}
          className="ydokpreview_railLink"
          title="Back to Case Library"
          aria-label="Back to Case Library"
        >
          <LayoutDashboard size={20}/>
          {toolsOpen && <span className="ydokpreview_railLabel">Case Library</span>}
        </Link>
      </aside>

      <section className={`${styles.glass} ${styles.patientCard}`}>
      <div className={styles.cardHeading}>
        <UserRound size={18} /> Patient Information
      </div>
      <div className={styles.patientLine}>
        <span className={styles.avatarIcon}>ID</span>
        <div>
          <strong>{caseCode || "Loading case..."}</strong>
          <p>Case details follow clinical access rules.</p>
        </div>
      </div>
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
          <small>Not measured</small>
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
        <p className={styles.vitalsDisclaimer}>Readings are unavailable until clinical examination is connected.</p>
      </section>

      {!chatOpen && currentPhase === "history_taking" && (patientChat.sending || latestPatientReply) && (
        <div className="f04v08-scene-reply" aria-live="polite" aria-atomic="true">
          <div className="f04v08-reply-heading">
            <MessageCircle size={15} /> {patientChat.sending ? "Patient is responding..." : "Patient"}
          </div>
          <p dir="auto">{patientChat.sending ? "بيفكر في الرد..." : latestPatientReply}</p>
        </div>
      )}
      {!chatOpen && patientChat.error && (
        <div className="f04v08-scene-error" role="alert">
          {patientChat.error}
          <button type="button" onClick={() => void patientChat.retryRefresh()} aria-label="Reload chat history">Retry</button>
        </div>
      )}

      <footer className={`${styles.glass} ${styles.dock} f04v08-dock`}>
        <button className={styles.dockButton} onClick={() => void runAction(paused ? "resume" : "pause")}
          title={mode === "test" ? "The assessment clock cannot be paused" : undefined}
          disabled={!liveSession || busy || ended || mode === "test"}>
          {paused ? <Play size={18} /> : <Pause size={18} />}
          <span>{paused ? "Resume" : "Pause"}</span>
        </button>

        <button type="button" className={`${styles.dockButton} f04v08-history-button`} onClick={openPatientChat}>
          <MessageCircle size={18} />
          <span>Chat History</span>
        </button>

        <form
          className={`${styles.voiceButton} f04v08-dock-form`}
          aria-label="Message the virtual patient"
          onSubmit={(event) => {
            event.preventDefault();
            void patientChat.send(canChat);
          }}
        >
          <span className={styles.micCircle} title="Voice interaction is not available yet"><Mic size={22} /></span>
          <input
            className="f04v08-dock-input"
            aria-label="Type your question to the patient"
            dir="auto"
            placeholder={canChat ? "اكتب سؤالك للمريض هنا..." : "المحادثة متاحة أثناء أخذ التاريخ المرضي"}
            value={patientChat.draft}
            onChange={(event) => patientChat.setDraft(event.target.value)}
            autoComplete="off"
            maxLength={1000}
            disabled={!canChat || patientChat.sending}
          />
          <button
            type="submit"
            className="f04v08-send-button"
            aria-label="Send to patient"
            title="Send message"
            disabled={!canChat || patientChat.sending || !patientChat.draft.trim()}
          >
            {patientChat.sending ? <span className="f04v08-spinner" aria-label="Sending" /> : <Send size={19} />}
          </button>
        </form>

        <button className={styles.endButton} onClick={() => setConfirmEnd(true)} disabled={!liveSession || busy || paused || ended}>
          <span>End Session</span>
          <ChevronRight size={18} />
        </button>
      </footer>

      <div className={styles.demoLabel}>CASE {caseCode || "LOADING"}</div>
      {liveError && (
        <div className={styles.toast} role="alert">{liveError}</div>
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
              <div><small>F04 · SAVED CONVERSATION</small><h2>Chat History</h2></div>
              <button className={styles.iconButton} aria-label="Close chat" onClick={() => setChatOpen(false)}><X /></button>
            </div>
            <div className={styles.transcript} aria-live="polite" aria-label="Saved patient conversation">
              {patientChat.loading && <p role="status">Loading saved messages...</p>}
              {!patientChat.loading && displayMessages.length === 0 && (
                <p>No messages yet. Introduce yourself to the patient.</p>
              )}
              {displayMessages.map((message) => (
                <div key={message.id} className={`${styles.message} ${message.role === "student" ? styles.studentMessage : ""}`}>
                  <small>{message.role === "student" ? "You · Student" : "Patient"} · {message.time}</small>
                  <p dir="auto" style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{message.text}</p>
                </div>
              ))}
              <div ref={chatTailRef} />
            </div>
            {patientChat.error && (
              <div role="alert" style={{ color: "#ffd6c6", background: "#642c29", padding: 10, borderRadius: 10, marginBottom: 9, fontSize: 12 }}>
                {patientChat.error}
                <button type="button" onClick={() => void patientChat.retryRefresh()}
                  style={{ display: "block", marginTop: 7, color: "white", textDecoration: "underline" }}>
                  Refresh history
                </button>
              </div>
            )}
            {!canChat && (
              <p style={{ color: "#edd0aa", fontSize: 12, marginBottom: 8 }}>
                {!liveSession ? "Connecting to your simulation..." : ended ? "Session completed · chat is read-only." : paused ? "Resume the session to chat." : currentPhase !== "history_taking" ? "Patient chat is available during History Taking." : "Finish the current action first."}
              </p>
            )}
            <p className="f04v08-history-note">المحادثة محفوظة تلقائيًا. اكتب سؤالك من الشريط السفلي في العيادة.</p>
          </aside>
        </div>
      )}

      {confirmEnd && (
        <div className={styles.modalOverlay}>
          <div className={`${styles.glass} ${styles.modal}`} role="dialog" aria-modal="true" aria-labelledby="end-title">
            <h2 id="end-title">Complete this session?</h2>
            <p>
              You can finish at any point. Submit your diagnosis; skipped clinical
              steps will remain recorded as not performed. Treatment is optional.
            </p>
            {!liveSession?.diagnosis && (
              <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
                <textarea
                  aria-label="Diagnosis"
                  placeholder="Your diagnosis"
                  value={diagnosisText}
                  onChange={(e) => setDiagnosisText(e.target.value)}
                  style={{ padding: 12, background: "#18342d", color: "white", borderRadius: 10 }}
                />
                <textarea
                  aria-label="Treatment plan (optional)"
                  placeholder="Treatment plan (optional)"
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
              disabled={!liveSession || busy || paused || ended}
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
            <h2>Session completed</h2>
            <p>This simulation session was completed and saved.</p>
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

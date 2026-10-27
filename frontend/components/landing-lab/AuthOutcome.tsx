"use client";

/** A presentation-only overlay. The caller owns the real Auth result. */
export function AuthOutcome({ kind, message }: { kind: "success" | "error"; message: string }) {
  const isSuccess = kind === "success";
  return (
    <div className="yd-result-layer" data-state={kind} role={isSuccess ? "status" : "alert"} aria-live={isSuccess ? "polite" : "assertive"}>
      <style>{styles}</style>
      <div className="yd-result-halo" data-state={kind} aria-hidden="true" />
      <div className="yd-result-card" data-state={kind}>
        <div className="yd-result-medallion" aria-hidden="true">
          <span className="yd-result-shine" />
          <svg viewBox="0 0 120 120" className="yd-result-icon" focusable="false">
            <circle className="yd-result-circle" cx="60" cy="60" r="47" fill="none" strokeWidth="3" />
            {isSuccess ? (
              <path className="yd-result-path" d="M37 61 L53 76 L84 44" fill="none" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
            ) : (
              <path className="yd-result-path" d="M45 45 L75 75 M75 45 L45 75" fill="none" strokeWidth="7" strokeLinecap="round" />
            )}
          </svg>
        </div>
        <span className="yd-result-title">{isSuccess ? "YA-DOK ✓" : "YA-DOK"}</span>
        <p className="yd-result-message">{message}</p>
      </div>
    </div>
  );
}

const styles = `
.yd-result-layer{position:fixed;inset:0;z-index:1000;isolation:isolate;display:grid;place-items:center;pointer-events:none;background:rgba(2,19,28,.49);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);animation:yd-result-back 1.65s cubic-bezier(.16,1,.25,1) both}
.yd-result-halo{position:absolute;width:min(460px,90vw);aspect-ratio:1;border-radius:50%;background:radial-gradient(circle,rgba(108,238,200,.28) 0%,rgba(75,211,200,.09) 32%,transparent 69%);animation:yd-result-halo 1.55s ease-out both}
.yd-result-halo[data-state=error]{background:radial-gradient(circle,rgba(253,123,142,.25),rgba(251,100,116,.08) 32%,transparent 69%)}
.yd-result-card{position:relative;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:11px;padding:25px 30px 29px;width:min(370px,86vw);min-height:225px;text-align:center;color:#f1fff9;border:1px solid rgba(169,255,230,.37);border-radius:31px;box-shadow:0 30px 105px rgba(0,15,22,.36),inset 0 1px 0 rgba(255,255,255,.19);background:linear-gradient(125deg,rgba(8,53,60,.92),rgba(7,26,36,.95));animation:yd-result-card 1.65s cubic-bezier(.2,1,.25,1) both}
.yd-result-card[data-state=error]{border-color:rgba(255,173,177,.48);background:linear-gradient(125deg,rgba(67,30,44,.94),rgba(22,28,40,.96))}
.yd-result-card[data-state=error]{animation:yd-result-card 1.65s cubic-bezier(.2,1,.25,1) both,yd-result-shake .46s .26s ease-in-out both}
@keyframes yd-result-shake{0%,100%{translate:0 0}12%,42%{translate:-9px 0}26%,57%{translate:9px 0}70%{translate:-5px 0}82%{translate:4px 0}92%{translate:-2px 0}}
.yd-result-layer[data-state=error]{background:rgba(49,9,19,.55)}
.yd-result-medallion{position:relative;width:118px;height:118px;display:grid;place-items:center;color:#8ffce2;filter:drop-shadow(0 0 19px rgba(107,255,218,.22))}
.yd-result-card[data-state=error] .yd-result-medallion{color:#ffafb8;filter:drop-shadow(0 0 19px rgba(255,126,144,.27))}
.yd-result-shine{position:absolute;inset:12px;opacity:.46;border-radius:50%;border:1px solid currentColor;animation:yd-result-pulse .85s .12s ease-out both}
.yd-result-icon{width:118px;height:118px;overflow:visible;transform:rotate(-15deg);animation:yd-result-icon .65s cubic-bezier(.17,1.7,.35,1) both}
.yd-result-circle{stroke:currentColor;stroke-dasharray:300;stroke-dashoffset:300;animation:yd-result-circle .75s .12s ease-out forwards}
.yd-result-path{stroke:currentColor;stroke-dasharray:100;stroke-dashoffset:100;animation:yd-result-draw .48s .52s ease-out forwards}
.yd-result-title{font-size:16px;font-weight:900;letter-spacing:.08em}
.yd-result-message{font-size:14px;line-height:1.5;max-width:305px;margin:0;color:#d9f1ec;text-wrap:balance;overflow-wrap:anywhere}
@keyframes yd-result-back{0%{opacity:0}15%,79%{opacity:1}100%{opacity:0}}
@keyframes yd-result-halo{0%{opacity:0;transform:scale(.58)}23%{opacity:1;transform:scale(1.05)}100%{opacity:0;transform:scale(1.35)}}
@keyframes yd-result-card{0%{opacity:0;transform:translateY(26px) scale(.83)}25%{opacity:1;transform:translateY(0) scale(1)}80%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(1.07)}}
@keyframes yd-result-icon{from{transform:scale(.7) rotate(-42deg)}to{transform:scale(1) rotate(0)}}
@keyframes yd-result-circle{to{stroke-dashoffset:0}}
@keyframes yd-result-draw{to{stroke-dashoffset:0}}
@keyframes yd-result-pulse{from{opacity:.8;transform:scale(.65)}to{opacity:.35;transform:scale(1.16)}}
@media(prefers-reduced-motion:reduce){.yd-result-layer,.yd-result-halo,.yd-result-card,.yd-result-icon,.yd-result-circle,.yd-result-path,.yd-result-shine{animation:none!important} .yd-result-card{translate:0 0!important}.yd-result-circle,.yd-result-path{stroke-dashoffset:0}}
`;

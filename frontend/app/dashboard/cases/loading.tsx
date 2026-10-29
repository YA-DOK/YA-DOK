export default function CasesLoading() {
  return <div className="ydash-library-loading" role="status" aria-label="Loading clinical cases" aria-live="polite">
    <div className="ydash-skeleton-title ydash-skeleton"/>
    <div className="ydash-skeleton-toolbar ydash-skeleton"/>
    <div className="ydash-cases-grid">{[1,2,3,4,5,6].map(i => <div key={i} className="ydash-case-card ydash-glass ydash-skeleton-card"><div className="ydash-skeleton-cover ydash-skeleton"/><div className="ydash-skeleton-lines"><div className="ydash-skeleton"/><div className="ydash-skeleton"/><div className="ydash-skeleton"/></div></div>)}</div>
  </div>;
}

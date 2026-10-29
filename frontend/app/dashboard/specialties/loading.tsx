export default function SpecialtiesLoading() {
  return <div className="ydash-library-loading" role="status" aria-label="Loading specialties" aria-live="polite">
    <div className="ydash-skeleton-title ydash-skeleton"/>
    <div className="ydash-specialties-tiles">{[1,2,3,4,5,6].map(i => <div key={i} className="ydash-specialty-tile ydash-skeleton"/>)}</div>
  </div>;
}

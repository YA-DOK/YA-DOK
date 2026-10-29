/** Editorial stock photographs, NOT photographs of the simulated patients.
 * The original images are openly licensed on Unsplash; see docs/PHOTO_SOURCES.md.
 * Served from remote Unsplash CDN; MedicalPhoto supplies local SVG fallback offline.
 */
const root = 'https://images.unsplash.com/';
const params = '?auto=format&fit=crop&w=1000&q=78';
export const medicalImages = {
  all: root + 'photo-1758691462878-6edc3d3da1be' + params,
  pediatrics: root + 'photo-1758691462119-792279713969' + params,
  internal: root + 'photo-1758691462878-6edc3d3da1be' + params,
  surgery: root + 'photo-1579684453423-f84349ef60b0' + params,
  cardiology: root + 'photo-1513224502586-d1e602410265' + params,
  neurology: root + 'photo-1758691463110-697a814b2033' + params,
  respiratory: root + 'photo-1758691462268-fbe66c4f3e28' + params,
  urinary: root + 'photo-1614935151651-0bea6508db6b' + params,
  abdominal: root + 'photo-1579684453423-f84349ef60b0' + params,
} as const;

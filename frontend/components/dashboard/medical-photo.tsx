"use client";

import Image from "next/image";
import { useState } from "react";

/** An actual editorial medical photo with local fallback for offline development. */
export function MedicalPhoto({ src, fallback, alt, priority=false, sizes="(max-width: 720px) 100vw, (max-width: 1150px) 50vw, 33vw" }: {
  src: string; fallback: string; alt: string; priority?: boolean; sizes?: string;
}) {
  const [offline, setOffline] = useState(false);
  return <Image
    key={src}
    src={offline ? fallback : src}
    fill
    unoptimized
    priority={priority}
    sizes={sizes}
    alt={alt}
    className="ydash-medical-photo"
    onError={() => setOffline(true)}
  />;
}

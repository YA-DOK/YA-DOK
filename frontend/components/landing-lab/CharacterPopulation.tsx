"use client";

import { Clone, useAnimations, useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import type { ReactNode } from "react";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { clone as cloneSkinned } from "three/examples/jsm/utils/SkeletonUtils.js";

type Position = [number, number, number];
type StaticStaffProps = { url: string; position: Position; rotation?: number; scale?: number };

// Third-party human assets are NOT embedded in the ZIP. See README for CC0 source links.
// Optional models are gated by a HEAD request, so missing files cannot block the clinic.
export const PEOPLE_FILES = {
  nurse: "/models/people/nurse.glb",
  doctor: "/models/people/doctor.glb",
  visitor: "/models/people/visitor.glb",
} as const;

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

function OptionalAsset({ url, children }: { url: string; children: ReactNode }) {
  const [available, setAvailable] = useState(false);
  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();
    void fetch(url, { method: "HEAD", cache: "no-store", signal: controller.signal })
      .then((res) => { if (mounted) setAvailable(res.ok); })
      .catch(() => { if (mounted) setAvailable(false); });
    return () => { mounted = false; controller.abort(); };
  }, [url]);
  return available ? <Suspense fallback={null}>{children}</Suspense> : null;
}

function useFloorAlignment(scene: THREE.Object3D) {
  return useMemo(() => {
    const bounds = new THREE.Box3().setFromObject(scene);
    const center = bounds.getCenter(new THREE.Vector3());
    return new THREE.Vector3(-center.x, -bounds.min.y, -center.z);
  }, [scene]);
}

function StaticStaff({ url, position, rotation = 0, scale = 1 }: StaticStaffProps) {
  const { scene } = useGLTF(url);
  const offset = useFloorAlignment(scene);
  return (
    <group position={position} rotation={[0, rotation, 0]} scale={scale}>
      <group position={[offset.x, offset.y, offset.z]}>
        <Clone object={scene} castShadow receiveShadow />
      </group>
    </group>
  );
}

/**
 * A genuine skinned GLB with embedded locomotion clips (not a sliding static figure).
 * The visitor walks a compact oval around the reception waiting area.
 */
function AnimatedVisitor() {
  const { scene, animations } = useGLTF(PEOPLE_FILES.visitor);
  const instance = useMemo(() => cloneSkinned(scene), [scene]);
  const offset = useFloorAlignment(scene);
  const root = useRef<THREE.Group>(null);
  const reduced = useReducedMotion();
  const { actions, names } = useAnimations(animations, root);

  useEffect(() => {
    const preferred = reduced
      ? names.find((name) => /idle/i.test(name))
      : names.find((name) => /relaxed.*walk|walk.*relaxed/i.test(name)) ?? names.find((name) => /walk/i.test(name));
    const fallback = names.find((name) => /idle/i.test(name)) ?? names[0];
    const chosen = preferred ?? fallback;
    const action = chosen ? actions[chosen] : undefined;
    if (!action) return;
    action.reset().setLoop(THREE.LoopRepeat, Infinity).fadeIn(0.35).play();
    return () => { action.fadeOut(0.25); };
  }, [actions, names, reduced]);

  useFrame(({ clock }) => {
    if (!root.current) return;
    if (reduced) {
      root.current.position.set(-3.85, 0, 5.5);
      root.current.rotation.y = 0;
      return;
    }
    // Stay outside the width of the reception counter (desk spans x ~= +/-2.85).
    const phase = clock.elapsedTime * 0.38;
    const x = -3.85 + 0.35 * Math.sin(phase);
    const z = 7.45 + 2.25 * Math.cos(phase);
    const dx = 0.35 * Math.cos(phase);
    const dz = -2.25 * Math.sin(phase);
    root.current.position.set(x, 0, z);
    root.current.rotation.y = Math.atan2(dx, dz);
  });

  return (
    <group ref={root} position={[-3.85, 0, 9.7]}>
      <group position={[offset.x, offset.y, offset.z]}>
        <primitive object={instance} />
      </group>
    </group>
  );
}

export default function CharacterPopulation({ enabled = true }: { enabled?: boolean }) {
  if (!enabled) return null;
  return (
    <group name="YA-DOK optional medical staff">
      {/* Behind the reception counter. These two staff meshes are static poses. */}
      <OptionalAsset url={PEOPLE_FILES.nurse}>
        <StaticStaff url={PEOPLE_FILES.nurse} position={[2.0, 0, 6.72]} rotation={Math.PI} />
      </OptionalAsset>
      {/* In the clinical room: optional medical doctor wearing a coat. */}
      <OptionalAsset url={PEOPLE_FILES.doctor}>
        <StaticStaff url={PEOPLE_FILES.doctor} position={[-10.9, 0, -2.65]} rotation={-0.45} />
      </OptionalAsset>
      {/* Real rigged + animated visitor; additional walk through reception. */}
      <OptionalAsset url={PEOPLE_FILES.visitor}>
        <AnimatedVisitor />
      </OptionalAsset>
    </group>
  );
}

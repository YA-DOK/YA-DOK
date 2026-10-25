"use client";

import { OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import type { ComponentRef, ErrorInfo, ReactNode, RefObject } from "react";
import { Component, Suspense, useEffect, useRef } from "react";
import * as THREE from "three";

// Public, CC0 medical asset pack. No manual Sketchfab download or account required.
// Source: https://3dassets.dev/packs/hospital-wards-and-clinic-operations
// This is a *kit showcase*, NOT the final custom-built YA-DOK clinic layout.
const ASSET_URL = "https://cdn.3dassets.dev/assets/23663/v1/model.glb";
type OrbitInstance = ComponentRef<typeof OrbitControls>;

class SceneErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("YA-DOK 3D scene error:", error, info.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-[#071C22] p-6 text-center text-white">
          <div className="max-w-md space-y-3">
            <p className="text-lg font-semibold">The 3D asset could not be loaded.</p>
            <p className="text-sm text-slate-300">
              Check your connection and the browser console. The existing
              authentication is unaffected. If the CDN is blocked, download the
              GLB from the source page and change ASSET_URL to a local
              /models/clinic.glb file.
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function CameraIntro({
  model,
  orbitRef,
  interrupted,
}: {
  model: THREE.Object3D;
  orbitRef: RefObject<OrbitInstance | null>;
  interrupted: RefObject<boolean>;
}) {
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const begin = useRef(new THREE.Vector3());
  const goal = useRef(new THREE.Vector3());
  const pivot = useRef(new THREE.Vector3());
  const elapsed = useRef(0);
  const ready = useRef(false);

  useEffect(() => {
    const bounds = new THREE.Box3().setFromObject(model);
    if (bounds.isEmpty()) return;
    const center = bounds.getCenter(new THREE.Vector3());
    const dimensions = bounds.getSize(new THREE.Vector3());
    const radius = Math.max(dimensions.length() * 0.5, 1);
    const perspective = camera as THREE.PerspectiveCamera;
    const verticalFov = THREE.MathUtils.degToRad(perspective.fov);
    const aspect = Math.max(size.width / Math.max(size.height, 1), 0.1);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * aspect);
    const fitFov = Math.min(verticalFov, horizontalFov);
    const distance = (radius / Math.sin(fitFov / 2)) * 1.2;
    const direction = new THREE.Vector3(1.0, 0.75, 1.25).normalize();

    pivot.current.copy(center);
    goal.current.copy(center).addScaledVector(direction, distance);
    begin.current.copy(center).addScaledVector(direction, distance * 0.48);
    camera.position.copy(begin.current);
    camera.lookAt(center);
    perspective.near = Math.max(distance / 1000, 0.01);
    perspective.far = Math.max(distance * 10, 1000);
    perspective.updateProjectionMatrix();

    if (orbitRef.current) {
      orbitRef.current.target.copy(center);
      orbitRef.current.minDistance = Math.max(radius * 0.35, 0.1);
      orbitRef.current.maxDistance = distance * 2.2;
      orbitRef.current.update();
    }
    interrupted.current = false;
    elapsed.current = 0;
    ready.current = true;
  }, [camera, model, size.width, size.height, orbitRef, interrupted]);

  useFrame((_, delta) => {
    if (!ready.current || interrupted.current || elapsed.current >= 2.6) return;
    elapsed.current = Math.min(elapsed.current + delta, 2.6);
    const t = elapsed.current / 2.6;
    const eased = 1 - Math.pow(1 - t, 3);
    camera.position.lerpVectors(begin.current, goal.current, eased);
    camera.lookAt(pivot.current);
    orbitRef.current?.update();
  });

  return null;
}

function MedicalKit() {
  const { scene } = useGLTF(ASSET_URL);
  const orbit = useRef<OrbitInstance | null>(null);
  const interrupted = useRef(false);

  useEffect(() => {
    // Inspect node names in DevTools for the next step: composing 4 rooms.
    console.info("YA-DOK medical kit loaded:", scene.children.length, "top-level nodes");
  }, [scene]);

  return (
    <>
      <primitive object={scene} />
      <CameraIntro model={scene} orbitRef={orbit} interrupted={interrupted} />
      <OrbitControls
        ref={orbit}
        makeDefault
        enableDamping
        dampingFactor={0.075}
        enablePan={false}
        onStart={() => { interrupted.current = true; }}
      />
    </>
  );
}

export default function ClinicalWorld() {
  return (
    <SceneErrorBoundary>
      <div className="absolute inset-0">
        <Canvas
          camera={{ position: [16, 12, 18], fov: 42, near: 0.01, far: 3000 }}
          dpr={[1, 1.75]}
          gl={{ antialias: true, powerPreference: "high-performance" }}
          fallback={
            <div className="flex h-full items-center justify-center p-6 text-center text-white">
              WebGL is not available in this browser or device.
            </div>
          }
        >
          <color attach="background" args={["#071C22"]} />
          <hemisphereLight args={["#D9F9F1", "#567277", 2.2]} />
          <ambientLight intensity={0.65} />
          <directionalLight position={[20, 32, 18]} intensity={2.4} />
          <directionalLight position={[-18, 14, -18]} intensity={1.1} color="#87D8D2" />
          <Suspense fallback={null}>
            <MedicalKit />
          </Suspense>
        </Canvas>
      </div>
    </SceneErrorBoundary>
  );
}

"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, RoundedBox } from "@react-three/drei";
import * as THREE from "three";

/**
 * YA-DOK / CLINIC ISOMETRIC 02
 * Scope: the 3D scene AND the opening zoom only.
 * No network requests, no GLB downloads, no auth, no navigation, no CSS imports.
 * Designed for @react-three/fiber 9 + @react-three/drei 10 + Three.js.
 */

type V3 = [number, number, number];
export type SceneFocus = "overview" | "doctor" | "paper" | "reception";


type BoxProps = {
  position: V3;
  size: V3;
  color: string;
  radius?: number;
  metalness?: number;
  roughness?: number;
  opacity?: number;
  rotation?: V3;
};

function Block({ position, size, color, radius = 0.07, metalness = 0, roughness = 0.76, opacity = 1, rotation = [0, 0, 0] }: BoxProps) {
  return (
    <RoundedBox
      args={size}
      radius={Math.min(radius, Math.min(...size) / 2 - 0.001)}
      smoothness={3}
      position={position}
      rotation={rotation}
      castShadow={opacity === 1}
      receiveShadow
    >
      <meshStandardMaterial
        color={color}
        roughness={roughness}
        metalness={metalness}
        transparent={opacity < 1}
        opacity={opacity}
        depthWrite={opacity === 1}
      />
    </RoundedBox>
  );
}

function Sphere({ position, scale, color, roughness = 0.8 }: { position: V3; scale: V3; color: string; roughness?: number }) {
  return (
    <mesh position={position} scale={scale} castShadow>
      <sphereGeometry args={[1, 20, 14]} />
      <meshStandardMaterial color={color} roughness={roughness} />
    </mesh>
  );
}

function Cylinder({ position, top, bottom, height, color, rotation = [0, 0, 0], segments = 18 }: {
  position: V3;
  top: number;
  bottom: number;
  height: number;
  color: string;
  rotation?: V3;
  segments?: number;
}) {
  return (
    <mesh position={position} rotation={rotation} castShadow receiveShadow>
      <cylinderGeometry args={[top, bottom, height, segments]} />
      <meshStandardMaterial color={color} roughness={0.72} />
    </mesh>
  );
}

function Plant({ position, size = 1 }: { position: V3; size?: number }) {
  return (
    <group position={position} scale={size}>
      <Cylinder position={[0, 0.27, 0]} top={0.29} bottom={0.22} height={0.54} color="#ddd3bd" />
      <Cylinder position={[0, 0.57, 0]} top={0.025} bottom={0.027} height={0.4} color="#70856c" />
      <Sphere position={[0, 0.88, 0]} scale={[0.44, 0.44, 0.42]} color="#477b58" />
      <Sphere position={[-0.22, 0.76, 0.05]} scale={[0.30, 0.34, 0.28]} color="#6b976e" />
      <Sphere position={[0.24, 0.80, -0.05]} scale={[0.30, 0.37, 0.31]} color="#548c63" />
      <Sphere position={[0.06, 1.15, -0.10]} scale={[0.26, 0.29, 0.25]} color="#639a70" />
    </group>
  );
}

function Person({
  position, outfit, skin = "#e9b78f", hair = "#392d2c", seated = false,
  coat = false, facing = 0, ponytail = false, working = false,
}: {
  position: V3;
  outfit: string;
  skin?: string;
  hair?: string;
  seated?: boolean;
  coat?: boolean;
  facing?: number;
  ponytail?: boolean;
  working?: boolean;
}) {
  // Everyone faces local +Z; facing rotates their entire posture, face and shoes.
  // When seated, hips align to the chair, shins are vertical and feet remain on the floor.
  const bodyY = seated ? 1.02 : 1.36;
  const headY = seated ? 1.80 : 2.20;
  const armY = seated ? 0.98 : 1.30;
  const clothing = coat ? "#f7f9f6" : outfit;
  return (
    <group position={position} rotation={[0, facing, 0]}>
      {seated ? (
        <>
          {/* Thighs and knees turn forward from the edge of the chair. */}
          {[-0.18, 0.18].map((x) => (
            <group key={x}>
              <Block position={[x, 0.57, 0.21]} size={[0.28, 0.22, 0.56]} color="#3c5360" radius={0.09} />
              <Block position={[x, 0.30, 0.46]} size={[0.23, 0.47, 0.22]} color="#3c5360" radius={0.08} />
              <Block position={[x, 0.10, 0.60]} size={[0.27, 0.15, 0.39]} color="#f4f1eb" radius={0.065} />
            </group>
          ))}
        </>
      ) : (
        <>
          {[-0.17, 0.17].map((x) => (
            <group key={x}>
              <Block position={[x, 0.47, 0]} size={[0.25, 0.86, 0.28]} color="#3c5360" radius={0.10} />
              <Block position={[x, 0.09, 0.13]} size={[0.30, 0.16, 0.43]} color="#f4f1eb" radius={0.07} />
            </group>
          ))}
        </>
      )}
      <Block position={[0, bodyY, 0]} size={[0.70, seated ? 0.75 : 0.89, 0.43]} color={clothing} radius={0.19} />
      {coat && <Block position={[0, bodyY, 0.23]} size={[0.17, 0.66, 0.035]} color="#8bcdbb" radius={0.014} />}
      {[-1, 1].map((side) => (
        <group key={side}>
          {/* Relaxed shoulders and forearms, not disconnected cylinders. */}
          <Sphere position={[side * 0.39, armY + 0.12, 0]} scale={[0.18, 0.25, 0.21]} color={clothing} />
          <Block
            position={[side * 0.45, armY - 0.12, working ? 0.16 : 0.055]}
            size={[0.20, 0.39, 0.21]}
            color={clothing}
            radius={0.09}
            rotation={working ? [0.45, 0, -side * 0.18] : [0, 0, side * 0.07]}
          />
          <Sphere
            position={[side * (working ? 0.38 : 0.46), working ? armY - 0.36 : armY - 0.37, working ? 0.36 : 0.06]}
            scale={[0.115, 0.13, 0.12]}
            color={skin}
          />
        </group>
      ))}
      <Cylinder position={[0, headY - 0.43, 0]} top={0.12} bottom={0.12} height={0.19} color={skin} />
      <Sphere position={[0, headY, 0]} scale={[0.34, 0.39, 0.32]} color={skin} />
      {/* Hair volume + a fringe; eyes and nose all face the same direction. */}
      <Sphere position={[0, headY + 0.28, -0.07]} scale={[0.35, 0.17, 0.33]} color={hair} />
      <Sphere position={[-0.29, headY + 0.09, -0.04]} scale={[0.11, 0.21, 0.27]} color={hair} />
      <Sphere position={[0.29, headY + 0.09, -0.04]} scale={[0.11, 0.21, 0.27]} color={hair} />
      {ponytail && <Sphere position={[0.1, headY + 0.06, -0.35]} scale={[0.19, 0.24, 0.17]} color={hair} />}
      <Sphere position={[-0.12, headY + 0.025, 0.30]} scale={[0.028, 0.036, 0.014]} color="#2d3135" />
      <Sphere position={[0.12, headY + 0.025, 0.30]} scale={[0.028, 0.036, 0.014]} color="#2d3135" />
      <Sphere position={[0, headY - 0.11, 0.323]} scale={[0.055, 0.045, 0.027]} color={skin} />
      <Sphere position={[0, headY - 0.19, 0.314]} scale={[0.064, 0.014, 0.009]} color="#985e56" />
    </group>
  );
}

function WaitingSeat({ x, z }: { x: number; z: number }) {
  return (
    <group position={[x, 0, z]}>
      <Block position={[0, 0.50, 0]} size={[1.23, 0.20, 0.91]} color="#d5e6de" radius={0.14} />
      <Block position={[0, 0.99, -0.38]} size={[1.21, 0.90, 0.18]} color="#a6d4c4" radius={0.11} />
      <Block position={[-0.57, 0.71, 0]} size={[0.10, 0.41, 0.98]} color="#dbe8df" radius={0.045} />
      <Block position={[0.57, 0.71, 0]} size={[0.10, 0.41, 0.98]} color="#dbe8df" radius={0.045} />
      {[-0.42, 0.42].map((dx) => [-0.29, 0.29].map((dz) => (
        <Cylinder key={`${dx}:${dz}`} position={[dx, 0.22, dz]} top={0.045} bottom={0.045} height={0.42} color="#6b7d7d" />
      )))}
    </group>
  );
}

function Reception() {
  // The registration island stands ALONE in the front centre, ahead of waiting.
  return (
    <group position={[-0.50, 0, 2.95]}>
      <Block position={[0, 0.68, 0.06]} size={[4.90, 1.20, 1.04]} color="#b79174" radius={0.14} />
      <Block position={[0, 1.32, 0.05]} size={[5.12, 0.17, 1.27]} color="#fffefa" radius={0.095} />
      <Block position={[0, 0.72, 0.615]} size={[4.55, 0.86, 0.055]} color="#cfac91" radius={0.02} />
      {[-1.68, -0.56, 0.56, 1.68].map((x) => (
        <Block key={x} position={[x, 0.70, 0.65]} size={[0.045, 0.82, 0.027]} color="#f0d7bd" radius={0.01} />
      ))}
      {/* A matching screen and keyboard at each registrar station. */}
      {[-1.23, 1.16].map((x) => (
        <group key={x} position={[x, 0, -0.18]}>
          <Cylinder position={[0, 1.49, 0]} top={0.038} bottom={0.052} height={0.23} color="#54656a" />
          <Block position={[0, 1.77, 0]} size={[0.84, 0.54, 0.075]} color="#274d55" radius={0.045} />
          <Block position={[0, 1.78, 0.045]} size={[0.73, 0.43, 0.014]} color="#97d6c8" radius={0.01} />
          <Block position={[0, 1.43, 0.24]} size={[0.64, 0.028, 0.22]} color="#e6e9e5" radius={0.015} />
        </group>
      ))}
      {/* Staff look toward the visitor in front of the counter. */}
      <Person position={[-1.23, 0, -1.04]} outfit="#69b7a6" skin="#e6b38c" hair="#3b2e2d" seated ponytail working />
      <Person position={[1.16, 0, -1.04]} outfit="#79bdb1" skin="#bb876c" hair="#282a2b" seated working />
      <Plant position={[3.05, 0, 0.05]} size={0.72} />
      {/* Appointment book, positioned on the desk rather than floating. */}
      <Block position={[0.08, 1.43, 0.29]} size={[0.47, 0.045, 0.34]} color="#e6d7b9" radius={0.02} />
    </group>
  );
}

function ExamBed({ position }: { position: V3 }) {
  return (
    <group position={position} rotation={[0, -0.45, 0]}>
      <Block position={[0, 0.70, 0]} size={[1.38, 0.18, 2.74]} color="#e5f1ee" radius={0.14} />
      <Block position={[0, 0.81, -0.76]} size={[1.19, 0.15, 0.61]} color="#d6e9e5" radius={0.12} />
      <Block position={[0, 0.91, -1.08]} size={[0.95, 0.18, 0.46]} color="#ffffff" radius={0.12} />
      {[-0.5, 0.5].map((x) => [-1.10, 1.1].map((z) => (
        <Cylinder key={`${x}:${z}`} position={[x, 0.37, z]} top={0.058} bottom={0.07} height={0.73} color="#728c90" />
      )))}
      <Block position={[0, 0.42, 0]} size={[1.08, 0.10, 1.9]} color="#aebfc0" radius={0.03} />
    </group>
  );
}

function FloatingInvestigationSheet({ active }: { active: boolean }) {
  const ref = useRef<THREE.Group>(null);
  useFrame((_, dt) => {
    if (!ref.current) return;
    const amount = Math.min(dt, 0.05);
    ref.current.position.y = THREE.MathUtils.damp(ref.current.position.y, active ? 2.32 : 1.01, 4.6, amount);
    ref.current.rotation.z = THREE.MathUtils.damp(ref.current.rotation.z, active ? -0.23 : 0, 4.5, amount);
    ref.current.rotation.x = THREE.MathUtils.damp(ref.current.rotation.x, active ? -0.32 : 0, 4.5, amount);
  });
  return <group ref={ref} position={[4.35, 1.01, -3.07]}>
    <Block position={[0, 0, 0]} size={[0.54, 0.045, 0.75]} color="#fffdf5" radius={0.012} />
    {[-0.24, -0.08, 0.08, 0.24].map((z) => (
      <Block key={z} position={[-0.03, 0.026, z]} size={[0.32, 0.006, 0.014]} color="#74a9a2" radius={0.001} />
    ))}
    <Block position={[0.11, 0.027, -0.30]} size={[0.11, 0.009, 0.045]} color="#83d7c8" radius={0.001} />
  </group>;
}

function DoctorsRoom({ raisePaper }: { raisePaper: boolean }) {
  return (
    <group>
      {/* Right-back PRIVATE consultation room: enclosed by walls and see-through front/side glazing. */}
      <Block position={[5.01, 0.042, -2.62]} size={[6.83, 0.075, 5.50]} color="#edf4f1" radius={0.02} />
      <Block position={[5.00, 1.60, -5.33]} size={[6.82, 3.20, 0.16]} color="#f8faf7" radius={0.025} />
      {/* Right structural wall, partly opaque like a real room. */}
      <Block position={[8.41, 1.36, -4.37]} size={[0.16, 2.72, 1.90]} color="#f1f5f2" radius={0.02} />
      {/* Solid partition on the waiting-room side. */}
      <Block position={[1.59, 1.56, -3.96]} size={[0.17, 3.10, 2.66]} color="#eef3ef" radius={0.025} />
      {/* Glazed wall sections towards the camera: room CLOSED without hiding its doctor. */}
      {[-0.99, -2.56, -4.10].map((z) => (
        <group key={z}>
          <Block position={[8.42, 1.47, z]} size={[0.035, 2.70, 1.49]} color="#aacfc8" opacity={0.13} radius={0.009} />
          <Block position={[8.43, 2.84, z]} size={[0.068, 0.09, 1.50]} color="#829f9c" radius={0.018} />
          <Block position={[8.43, 0.13, z]} size={[0.075, 0.23, 1.50]} color="#9bbfba" radius={0.018} />
        </group>
      ))}
      {[-0.18, -1.65, -3.15].map((z) => (
        <Block key={z} position={[8.43, 1.5, z]} size={[0.085, 2.90, 0.067]} color="#8aa7a3" radius={0.014} />
      ))}
      {/* Front elevation: framed glazing and a visible hinged glass door. */}
      {[4.08, 5.82, 7.56].map((x) => (
        <group key={x}>
          <Block position={[x, 1.45, 0.12]} size={[1.62, 2.67, 0.04]} color="#acd8d1" opacity={0.15} radius={0.01} />
          <Block position={[x, 2.81, 0.12]} size={[1.64, 0.085, 0.085]} color="#799995" radius={0.018} />
          <Block position={[x, 0.16, 0.12]} size={[1.64, 0.22, 0.09]} color="#a8c8c2" radius={0.018} />
        </group>
      ))}
      {[3.23, 4.93, 6.68, 8.40].map((x) => (
        <Block key={x} position={[x, 1.5, 0.13]} size={[0.082, 2.74, 0.09]} color="#819f9a" radius={0.016} />
      ))}
      {/* Entry door near reception, distinct border and handle. */}
      <Block position={[2.38, 1.45, 0.13]} size={[1.45, 2.62, 0.048]} color="#a9d7cc" opacity={0.18} radius={0.012} />
      <Block position={[1.66, 1.49, 0.14]} size={[0.10, 2.76, 0.10]} color="#729c93" radius={0.02} />
      <Block position={[3.12, 1.49, 0.14]} size={[0.10, 2.76, 0.10]} color="#729c93" radius={0.02} />
      <Block position={[2.39, 2.82, 0.14]} size={[1.56, 0.10, 0.10]} color="#729c93" radius={0.02} />
      <Sphere position={[2.96, 1.12, 0.26]} scale={[0.057, 0.057, 0.057]} color="#bb9565" />
      {/* Posters and a clinical bed in the back-right, desk and two facing occupants on the left. */}
      <Block position={[6.75, 1.83, -5.20]} size={[1.65, 1.20, 0.07]} color="#b6d5d0" radius={0.045} />
      <Block position={[6.75, 1.83, -5.15]} size={[1.45, 1.0, 0.016]} color="#e6f1ee" radius={0.016} />
      <Block position={[3.16, 2.0, -5.18]} size={[1.02, 1.18, 0.06]} color="#c7dad4" radius={0.025} />
      <Block position={[3.16, 2.0, -5.13]} size={[0.81, 0.95, 0.016]} color="#fcfdfb" radius={0.015} />
      <Sphere position={[3.16, 2.13, -5.11]} scale={[0.24, 0.26, 0.012]} color="#87c4b7" />
      <ExamBed position={[6.68, 0, -3.22]} />
      <Block position={[3.63, 0.89, -3.35]} size={[2.24, 0.15, 1.04]} color="#cfa989" radius={0.055} />
      {[-0.89, 0.89].map((dx) => [-0.33, 0.33].map((dz) => (
        <Cylinder key={`${dx}:${dz}`} position={[3.63 + dx, 0.43, -3.35 + dz]} top={0.048} bottom={0.051} height={0.81} color="#c4cecd" />
      )))}
      <Block position={[3.22, 1.33, -3.63]} size={[0.82, 0.62, 0.08]} color="#3e6468" radius={0.035} />
      <Block position={[3.22, 1.33, -3.58]} size={[0.69, 0.50, 0.016]} color="#a2d3c9" radius={0.01} />
      <Cylinder position={[3.22, 1.01, -3.65]} top={0.046} bottom={0.055} height={0.21} color="#6c7f80" />
      <FloatingInvestigationSheet active={raisePaper} />
      <Person position={[4.47, 0, -4.46]} outfit="#9bd0c4" skin="#e7b48e" hair="#483730" coat facing={-0.24} />
      {/* The visitor's chair faces INTO the doctor's desk, not into the glass. */}
      <group rotation={[0, Math.PI, 0]} position={[4.06, 0, -1.65]}>
        <WaitingSeat x={0} z={0} />
        <Person position={[0, 0, 0]} outfit="#d7a68b" hair="#514035" skin="#bd8b71" seated />
      </group>
      <Block position={[6.04, 0.53, -4.86]} size={[0.78, 1.02, 0.72]} color="#dce8e2" radius={0.055} />
      <Plant position={[7.90, 0, -4.85]} size={0.56} />
    </group>
  );
}

function WallsAndDécor() {
  return (
    <group>
      {/* Rear and left side cutaway walls preserve the same isometric view. */}
      <Block position={[-3.43, 1.57, -5.44]} size={[10.2, 3.14, 0.18]} color="#f7f8f5" radius={0.02} />
      <Block position={[-8.48, 1.57, -2.32]} size={[0.18, 3.14, 6.28]} color="#f6f8f5" radius={0.02} />
      {/* Minimal wall art on the LEFT waiting wall. */}
      <Block position={[-6.69, 1.90, -5.31]} size={[1.56, 1.23, 0.056]} color="#dac8b0" radius={0.035} />
      <Block position={[-6.69, 1.90, -5.275]} size={[1.39, 1.06, 0.013]} color="#fafcf9" radius={0.02} />
      <Sphere position={[-6.69, 2.00, -5.26]} scale={[0.30, 0.32, 0.013]} color="#abd5c5" />
      <Block position={[-6.69, 1.51, -5.255]} size={[0.69, 0.07, 0.015]} color="#8fb7ac" radius={0.01} />
      <Block position={[-4.50, 2.19, -5.31]} size={[2.66, 0.49, 0.062]} color="#d6e9df" radius={0.07} />
      <Block position={[-4.50, 2.19, -5.265]} size={[1.84, 0.075, 0.014]} color="#73b3a4" radius={0.018} />
    </group>
  );
}

function WaitingArea() {
  // Waiting moved to the EMPTY REAR-LEFT area, behind the separate reception island.
  return (
    <group>
      <Block position={[-5.42, 0.04, -2.35]} size={[5.70, 0.055, 4.60]} color="#eee8dc" radius={0.09} />
      {[-7.12, -5.38, -3.64].map((x) => <WaitingSeat key={x} x={x} z={-2.58} />)}
      <Person position={[-7.12, 0, -2.58]} outfit="#d99984" skin="#c88a6c" hair="#342a2e" seated ponytail />
      <Person position={[-5.38, 0, -2.58]} outfit="#85a6cb" skin="#e8b78f" hair="#372c2b" seated />
      <Person position={[-3.64, 0, -2.58]} outfit="#b6a0c9" skin="#b98570" hair="#302527" seated ponytail />
      <Block position={[-5.35, 0.42, -0.56]} size={[1.46, 0.17, 0.76]} color="#cda987" radius={0.12} />
      <Cylinder position={[-5.35, 0.22, -0.56]} top={0.09} bottom={0.11} height={0.38} color="#e8dfce" />
      <Block position={[-5.35, 0.55, -0.56]} size={[0.41, 0.045, 0.32]} color="#faf8f4" radius={0.018} />
      <Plant position={[-7.84, 0, -0.36]} size={0.71} />
      <Plant position={[-2.53, 0, -4.75]} size={0.60} />
    </group>
  );
}

function ClinicDiorama({ raisePaper }: { raisePaper: boolean }) {
  return (
    <group>
      <Block position={[0, -0.38, 0]} size={[17.85, 0.68, 11.75]} color="#c5ad8f" radius={0.21} />
      <Block position={[0, -0.105, 0]} size={[17.60, 0.19, 11.50]} color="#e4c8a3" radius={0.10} />
      {Array.from({ length: 33 }, (_, i) => (
        <Block
          key={i}
          position={[-8.47 + i * 0.53, 0.008, 0]}
          size={[0.515, 0.025, 11.34]}
          color={["#dfbc92", "#e4c49d", "#e0bd95", "#e8c9a3", "#e2c199"][i % 5]}
          radius={0.008}
        />
      ))}
      <WallsAndDécor />
      <WaitingArea />
      <Reception />
      <DoctorsRoom raisePaper={raisePaper} />
      {/* A single visitor faces the two registrars, waiting to check in. */}
      <Person position={[-0.3, 0, 4.95]} outfit="#d5b2a1" skin="#d8a17f" hair="#473839" facing={Math.PI} />
      <Plant position={[8.08, 0, 4.94]} size={0.64} />
      <Plant position={[-8.1, 0, 4.82]} size={0.65} />
    </group>
  );
}

function CinematicCamera({ focus }: { focus: SceneFocus }) {
  const elapsed = useRef(0);
  const lookAt = useRef(new THREE.Vector3(0, 0.9, 0));
  const cameraOffset = useRef(new THREE.Vector3(21, 18, 24));
  const lastViewport = useRef({ width: 0, height: 0 });

  // Three.js camera objects must be updated in the R3F frame loop,
  // not by mutating an object obtained from a React hook during render.
  useFrame((state, dt) => {
    const orthographic = state.camera as THREE.OrthographicCamera;
    const { width, height } = state.size;
    if (width !== lastViewport.current.width || height !== lastViewport.current.height) {
      const aspect = Math.max(0.35, width / Math.max(1, height));
      const viewHeight = Math.max(15.2, 23.0 / aspect);
      orthographic.left = -viewHeight * aspect / 2;
      orthographic.right = viewHeight * aspect / 2;
      orthographic.top = viewHeight / 2;
      orthographic.bottom = -viewHeight / 2;
      lastViewport.current = { width, height };
    }

    const delta = Math.min(dt, 0.05);
    elapsed.current = Math.min(2.5, elapsed.current + delta);
    const p = elapsed.current / 2.5;
    const intro = 0.46 + 0.64 * (1 - Math.pow(1 - p, 3));
    const targets: Record<SceneFocus, [V3, number]> = {
      overview: [[0, 0.9, 0], 1.10],
      doctor: [[4.6, 1.25, -3.4], 2.35],
      paper: [[4.35, 1.9, -3.05], 3.05],
      reception: [[1.55, 1.35, 2.95], 2.3],
    };
    const [target, zoom] = targets[focus];
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const smoothing = reduced ? 1 : (1 - Math.exp(-3.8 * delta));
    lookAt.current.lerp(new THREE.Vector3(...target), smoothing);
    const targetZoom = focus === 'overview' && !reduced ? intro : zoom;
    orthographic.zoom = THREE.MathUtils.lerp(orthographic.zoom, targetZoom, smoothing);
    const offset = focus === "reception" ? new THREE.Vector3(9, 8, 29) : new THREE.Vector3(21, 18, 24);
    cameraOffset.current.lerp(offset, smoothing);
    orthographic.position.copy(lookAt.current).add(cameraOffset.current);
    orthographic.lookAt(lookAt.current);
    orthographic.updateProjectionMatrix();
  });
  return null;
}

export default function ClinicalWorld({
  focus = 'overview', onSceneClick,
}: { focus?: SceneFocus; onSceneClick?: () => void }) {
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: 'radial-gradient(ellipse at 50% 43%, #fcfdfb 0%, #f0f5f2 55%, #dae8e4 100%)' }}>
      <Canvas orthographic shadows dpr={[1, 1.7]}
        camera={{ position: [21, 18, 24], zoom: .46, near: .1, far: 110 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        style={{ cursor: focus === 'overview' && onSceneClick ? 'pointer' : 'default' }}
        onPointerMissed={() => { if (focus === 'overview') onSceneClick?.(); }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.03;
          gl.shadowMap.type = THREE.PCFShadowMap;
        }}
        fallback={<div style={{ padding: 20 }}>WebGL is required to view the clinic.</div>}
      >
        <ambientLight intensity={.42} />
        <hemisphereLight args={['#ffffff', '#9ca69e', .95]} />
        <directionalLight position={[-9, 22, 19]} intensity={2.65} castShadow shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-22} shadow-camera-right={22} shadow-camera-top={22} shadow-camera-bottom={-22} shadow-bias={-.00015}/>
        <directionalLight position={[13, 12, -12]} intensity={.48} color="#e4fff4"/>
        <ContactShadows position={[0, -.78, 0]} scale={[24, 19]} opacity={.30} blur={2.8}
          far={6} color="#6c6a60" resolution={512} frames={1} />
        <group onClick={(e) => { if (focus === 'overview' && onSceneClick) { e.stopPropagation(); onSceneClick(); } }}>
          <ClinicDiorama raisePaper={focus === 'paper'} />
        </group>
        <CinematicCamera focus={focus}/>
      </Canvas>
    </div>
  );
}

import type { ReactNode } from "react";
import { DashboardAuthArrival } from "../../components/landing-lab/DashboardAuthArrival";

// Preserve the existing protected Dashboard page, user queries and layout.
// Only add an animation after Google OAuth has completed and the user is verified.
export default function DashboardTemplate({ children }: { children: ReactNode }) {
  return <><DashboardAuthArrival />{children}</>;
}

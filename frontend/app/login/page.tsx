import { redirect } from "next/navigation";

// Keep the legacy URL working while the visual authentication experience
// lives in the 3D Landing. All server-side auth callbacks stay unchanged.
export default function Login() {
  redirect("/?auth=login");
}

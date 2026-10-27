/** Public YA-DOK contact email endpoint. Independent from Supabase/Auth. */
const TO = "yaadok.2027@gmail.com";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: Request) {
  const origin = request.headers.get("origin");
  // A browser contact form is same-origin only. Non-browser tools may omit Origin.
  if (origin && new URL(origin).host !== new URL(request.url).host) {
    return Response.json({ error: "Request origin is not allowed." }, { status: 403 });
  }
  if (Number(request.headers.get("content-length") || 0) > 16000) {
    return Response.json({ error: "Message is too long." }, { status: 413 });
  }
  let payload: unknown;
  try { payload = await request.json(); }
  catch { return Response.json({ error: "Invalid request." }, { status: 400 }); }
  if (!payload || typeof payload !== "object") {
    return Response.json({ error: "Invalid request." }, { status: 400 });
  }
  const fields = payload as Record<string, unknown>;
  // Honeypot: ignored bots receive an error; do not pretend mail was delivered.
  if (typeof fields.website === "string" && fields.website.trim()) {
    return Response.json({ error: "Invalid request." }, { status: 400 });
  }
  const name = typeof fields.name === "string" ? fields.name.trim() : "";
  const email = typeof fields.email === "string" ? fields.email.trim() : "";
  const message = typeof fields.message === "string" ? fields.message.trim() : "";
  if (name.length < 2 || name.length > 120 || !EMAIL_RE.test(email) || email.length > 254 || message.length < 10 || message.length > 3000) {
    return Response.json({ error: "Please provide a valid name, email and message (10–3000 characters)." }, { status: 400 });
  }
  const key = process.env.RESEND_API_KEY;
  const sender = process.env.CONTACT_FROM_EMAIL;
  if (!key || !sender) {
    return Response.json({ error: "Email delivery is not configured yet. Please use the email link instead.", code: "NOT_CONFIGURED" }, { status: 503 });
  }
  try {
    const result = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: sender,
        to: [TO],
        reply_to: email,
        subject: `YA-DOK contact from ${name.replace(/[\r\n]/g, " ")}`,
        text: `New YA-DOK website message\n\nName: ${name}\nEmail: ${email}\n\n${message}`,
      }),
      cache: "no-store",
    });
    if (!result.ok) {
      // Don't leak upstream response details or keys to browser.
      console.error("YA-DOK contact mail service failed with status", result.status);
      return Response.json({ error: "Email could not be sent. Please try the email link." }, { status: 502 });
    }
    return Response.json({ ok: true }, { status: 200 });
  } catch (error) {
    console.error("YA-DOK contact delivery network error", error);
    return Response.json({ error: "Email service is temporarily unavailable." }, { status: 502 });
  }
}

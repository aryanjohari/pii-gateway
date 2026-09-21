import { NextRequest, NextResponse } from "next/server";

type SanitizeBody = {
  text?: string;
  structured?: unknown;
};

const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 30;
const hits = new Map<string, number[]>();

function allow(ip: string): boolean {
  const now = Date.now();
  const cutoff = now - WINDOW_MS;
  const recent = (hits.get(ip) ?? []).filter((t) => t > cutoff);
  if (recent.length >= MAX_PER_WINDOW) {
    hits.set(ip, recent);
    return false;
  }
  recent.push(now);
  hits.set(ip, recent);
  return true;
}

function clientIp(request: NextRequest): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0]?.trim() || "unknown";
  }
  return request.headers.get("x-real-ip") || "unknown";
}

export async function POST(request: NextRequest) {
  const ip = clientIp(request);
  if (!allow(ip)) {
    return NextResponse.json(
      {
        ok: false,
        error: { code: "rate_limited", message: "Too many demo requests; try again later" },
      },
      { status: 429 },
    );
  }

  const apiUrl = process.env.PII_GATEWAY_API_URL?.replace(/\/$/, "");
  const apiKey = process.env.PII_GATEWAY_API_KEY;

  if (!apiUrl || !apiKey) {
    return NextResponse.json(
      {
        ok: false,
        offline: true,
        error: {
          code: "demo_offline",
          message:
            "Demo API is not configured. Run Docker Compose locally and set PII_GATEWAY_API_URL / PII_GATEWAY_API_KEY, or connect a Pi tunnel later.",
        },
      },
      { status: 503 },
    );
  }

  let body: SanitizeBody;
  try {
    body = (await request.json()) as SanitizeBody;
  } catch {
    return NextResponse.json(
      {
        ok: false,
        error: { code: "validation_error", message: "Invalid JSON body" },
      },
      { status: 422 },
    );
  }

  if (body.text == null && body.structured == null) {
    return NextResponse.json(
      {
        ok: false,
        error: {
          code: "validation_error",
          message: "Provide at least one of text or structured",
        },
      },
      { status: 422 },
    );
  }

  try {
    const upstream = await fetch(`${apiUrl}/v1/sanitize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const payload: unknown = await upstream.json().catch(() => null);
    if (payload == null) {
      return NextResponse.json(
        {
          ok: false,
          offline: true,
          error: {
            code: "demo_offline",
            message: "Demo gateway returned an empty response.",
          },
        },
        { status: 503 },
      );
    }

    return NextResponse.json(payload, { status: upstream.status });
  } catch {
    return NextResponse.json(
      {
        ok: false,
        offline: true,
        error: {
          code: "demo_offline",
          message:
            "Could not reach the demo gateway. Start Compose locally or check the Pi tunnel.",
        },
      },
      { status: 503 },
    );
  }
}

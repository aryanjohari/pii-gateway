export type SanitizeSuccess = {
  text?: string;
  structured?: unknown;
  entitySummary: Record<string, number> | null;
  durationMs: number | null;
};

export type ParsedResponse =
  | { kind: "ok"; value: SanitizeSuccess }
  | { kind: "error"; code: string | null }
  | { kind: "unknown" };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toSummary(value: unknown): Record<string, number> | null {
  if (!isRecord(value)) return null;
  const entries = Object.entries(value).filter(
    (entry): entry is [string, number] => typeof entry[1] === "number",
  );
  return Object.fromEntries(entries);
}

/** Check the shape at the boundary; everything after this can trust the types. */
export function parseSanitizeResponse(data: unknown): ParsedResponse {
  if (!isRecord(data)) return { kind: "unknown" };

  if (data.ok === true && isRecord(data.result)) {
    const meta = isRecord(data.meta) ? data.meta : {};
    return {
      kind: "ok",
      value: {
        text: typeof data.result.text === "string" ? data.result.text : undefined,
        structured: data.result.structured,
        entitySummary: toSummary(meta.entity_summary),
        durationMs: typeof meta.duration_ms === "number" ? meta.duration_ms : null,
      },
    };
  }

  if (data.ok === false) {
    const error = isRecord(data.error) ? data.error : {};
    return { kind: "error", code: typeof error.code === "string" ? error.code : null };
  }

  return { kind: "unknown" };
}

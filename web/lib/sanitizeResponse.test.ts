import { describe, expect, it } from "vitest";

import { parseSanitizeResponse } from "./sanitizeResponse";

describe("parseSanitizeResponse", () => {
  it("accepts a success body and keeps only numeric entity counts", () => {
    const parsed = parseSanitizeResponse({
      ok: true,
      result: { text: "hi <PERSON>" },
      meta: { entity_summary: { PERSON: 1, BAD: "x" }, duration_ms: 7 },
    });
    expect(parsed).toEqual({
      kind: "ok",
      value: {
        text: "hi <PERSON>",
        structured: undefined,
        entitySummary: { PERSON: 1 },
        durationMs: 7,
      },
    });
  });

  it("reads the error code from a failure body", () => {
    expect(parseSanitizeResponse({ ok: false, error: { code: "rate_limited" } })).toEqual({
      kind: "error",
      code: "rate_limited",
    });
  });

  it("ignores a result text of the wrong type", () => {
    const parsed = parseSanitizeResponse({ ok: true, result: { text: 5 } });
    expect(parsed).toMatchObject({ kind: "ok", value: { text: undefined } });
  });

  it.each([null, "text", { detail: { code: "x" } }, { ok: true }])(
    "treats %j as unknown",
    (body) => {
      expect(parseSanitizeResponse(body)).toEqual({ kind: "unknown" });
    },
  );
});

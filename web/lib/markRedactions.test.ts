import { describe, expect, it } from "vitest";

import { markRedactions } from "./markRedactions";

const removed = (segments: ReturnType<typeof markRedactions>) =>
  segments?.flatMap((segment) =>
    segment.kind === "removed" ? [`${segment.label}=${segment.text}`] : [],
  );

describe("markRedactions", () => {
  it("recovers each removed item and its label", () => {
    const segments = markRedactions(
      "Email Aroha Smith at aroha@example.com about NHI ZAC5361.",
      "Email <PERSON> at <EMAIL_ADDRESS> about NHI <NZ_NHI>.",
    );
    expect(removed(segments)).toEqual([
      "PERSON=Aroha Smith",
      "EMAIL_ADDRESS=aroha@example.com",
      "NZ_NHI=ZAC5361",
    ]);
  });

  it("handles adjacent placeholders and a removal at the very end", () => {
    expect(removed(markRedactions("Aroha Smith, Bob Lee", "<PERSON>, <PERSON>"))).toEqual([
      "PERSON=Aroha Smith",
      "PERSON=Bob Lee",
    ]);
  });

  it("returns the text unmarked when nothing was removed, even if it contains a literal placeholder", () => {
    expect(markRedactions("a <PERSON> b", "a <PERSON> b")).toEqual([
      { kind: "text", text: "a <PERSON> b" },
    ]);
  });

  it("returns null when the texts do not line up", () => {
    expect(markRedactions("something", "completely different")).toBeNull();
  });
});

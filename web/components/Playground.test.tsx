import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Playground } from "./Playground";

// The network is the only thing mocked; the component and its hook run for real.
function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// Assertions on text use textContent, so no extra matcher library is needed.
async function expectStatus(text: string) {
  await waitFor(() => expect(screen.getByRole("status").textContent).toContain(text));
}

const input = () => screen.getByRole("textbox", { name: /input/i });
const submitButton = () => screen.getByRole("button", { name: "Sanitize" });

describe("Playground", () => {
  it("fills the box from a preset without submitting", async () => {
    const fetchMock = mockFetch(200, {});
    render(<Playground />);

    await userEvent.click(screen.getByRole("button", { name: /invoice/i }));

    expect((input() as HTMLTextAreaElement).value).toContain("IRD number");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows both panels and announces what was removed on success", async () => {
    mockFetch(200, {
      ok: true,
      result: { text: "Clinic note, 12 March: <PERSON> attended." },
      meta: { entity_summary: { PERSON: 1 }, duration_ms: 5 },
    });
    render(<Playground />);

    await userEvent.clear(input());
    await userEvent.type(input(), "Clinic note, 12 March: Sarah Thompson attended.");
    await userEvent.click(submitButton());

    await expectStatus("Removed PERSON: 1");
    expect(screen.getByRole("heading", { name: "Your text" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "What the AI would see" })).toBeTruthy();
    expect(screen.getByText("Sarah Thompson").tagName).toBe("MARK");
  });

  it("asks for text when the box is empty and sends nothing", async () => {
    const fetchMock = mockFetch(200, {});
    render(<Playground />);

    await userEvent.clear(input());
    await userEvent.click(submitButton());

    await expectStatus("Add some text first");
    expect(fetchMock).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(input());
  });

  it("links invalid JSON to the field", async () => {
    mockFetch(200, {});
    render(<Playground />);

    await userEvent.click(screen.getByRole("button", { name: "JSON" }));
    await userEvent.clear(input());
    await userEvent.type(input(), "not json");
    await userEvent.click(submitButton());

    await waitFor(() => expect(input().getAttribute("aria-invalid")).toBe("true"));
    const describedBy = input().getAttribute("aria-describedby");
    expect(document.getElementById(describedBy ?? "")?.textContent).toContain("not valid JSON");
  });

  it("offers the self-host link when the demo is offline", async () => {
    mockFetch(503, { ok: false, offline: true, error: { code: "demo_offline", message: "x" } });
    render(<Playground />);

    await userEvent.click(submitButton());

    await expectStatus("demo is offline");
    expect(screen.getByRole("link", { name: /self-host instructions/i })).toBeTruthy();
  });

  it("shows our wording for a rate limit, not the server's text", async () => {
    mockFetch(429, { ok: false, error: { code: "rate_limited", message: "server wording" } });
    render(<Playground />);

    await userEvent.click(submitButton());

    await expectStatus("Too many requests");
    expect(screen.getByRole("status").textContent).not.toContain("server wording");
  });

  it("blocks text over the limit before sending", async () => {
    const fetchMock = mockFetch(200, {});
    render(<Playground />);

    await userEvent.clear(input());
    await userEvent.click(input());
    await userEvent.paste("a".repeat(10_001));
    await userEvent.click(submitButton());

    await expectStatus("10,001 characters");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

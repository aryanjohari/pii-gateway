import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Fails on serious or critical violations. Automated checks find only part of the problems;
// a clean scan is not proof of accessibility.
async function expectNoSeriousViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const serious = violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(
    serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`),
  ).toEqual([]);
}

const SANITIZED = {
  ok: true,
  result: { text: "Clinic note, 12 March: <PERSON> attended with a sore knee. NHI <NZ_NHI>." },
  meta: { entity_summary: { PERSON: 1, NZ_NHI: 1 }, duration_ms: 12 },
};

test("happy path: a preset shows what was removed, with labels in text", async ({ page }) => {
  await page.route("**/api/sanitize", (route) => route.fulfill({ json: SANITIZED }));
  await page.goto("/");
  await expectNoSeriousViolations(page);

  await page.getByRole("button", { name: /clinic note/i }).click();
  await page.getByRole("button", { name: "Sanitize" }).click();

  await expect(page.getByRole("status")).toContainText("Removed PERSON: 1, NZ_NHI: 1");
  await expect(page.getByRole("heading", { name: "Your text" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What the AI would see" })).toBeVisible();
  await expect(page.getByText("<NZ_NHI>", { exact: false }).first()).toBeVisible();
  await expect(page.locator("mark", { hasText: "ZAC5361" })).toBeVisible();
  await expectNoSeriousViolations(page);
});

test("error path: demo offline gives a message and a way forward", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Sanitize" }).click();

  await expect(page.getByRole("status")).toContainText("The public demo is offline");
  await expect(page.getByRole("link", { name: /self-host instructions/i })).toBeVisible();
  await expectNoSeriousViolations(page);
});

test("keyboard only: skip link, visible focus, type, submit with Enter", async ({ page }) => {
  await page.route("**/api/sanitize", (route) => route.fulfill({ json: SANITIZED }));
  await page.goto("/");

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();

  const input = page.getByRole("textbox", { name: /input/i });
  for (let presses = 0; presses < 15 && !(await input.evaluate((el) => el === document.activeElement)); presses += 1) {
    await page.keyboard.press("Tab");
  }
  await expect(input).toBeFocused();
  const outlineStyle = await input.evaluate((el) => getComputedStyle(el).outlineStyle);
  expect(outlineStyle).not.toBe("none");

  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Sanitize" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toContainText("Removed");
});

test("phone width: no horizontal scroll and no serious violations", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.route("**/api/sanitize", (route) => route.fulfill({ json: SANITIZED }));
  await page.goto("/");
  await page.getByRole("button", { name: "Sanitize" }).click();
  await expect(page.getByRole("status")).toContainText("Removed");

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  await expectNoSeriousViolations(page);
});

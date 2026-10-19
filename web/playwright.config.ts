import { defineConfig } from "@playwright/test";

const PORT = 3100;

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  // Reduced motion keeps axe from measuring contrast while the entrance animations are mid-fade.
  use: { baseURL: `http://127.0.0.1:${PORT}`, reducedMotion: "reduce" },
  // Serves the production build (run `npm run build` first). No PII_GATEWAY_* variables are set,
  // so the real /api/sanitize route answers "demo offline", which the error-path test relies on.
  webServer: {
    command: `npm run start -- -p ${PORT}`,
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: !process.env.CI,
    env: { PII_GATEWAY_API_URL: "", PII_GATEWAY_API_KEY: "" },
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});

import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";
import jsxA11y from "eslint-plugin-jsx-a11y";

const config = [
  ...coreWebVitals,
  ...typescript,
  // Next's config enables a handful of jsx-a11y rules; the recommended set covers the rest.
  {
    rules: {
      ...jsxA11y.flatConfigs.recommended.rules,
      // A named, focusable region is the WCAG technique for a scrollable code block (axe:
      // scrollable-region-focusable). Allowed for regions only; other elements still error.
      "jsx-a11y/no-noninteractive-tabindex": ["error", { roles: ["tabpanel", "region"] }],
    },
  },
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
];

export default config;

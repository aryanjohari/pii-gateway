import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";
import jsxA11y from "eslint-plugin-jsx-a11y";

const config = [
  ...coreWebVitals,
  ...typescript,
  // Next's config enables a handful of jsx-a11y rules; the recommended set covers the rest.
  { rules: { ...jsxA11y.flatConfigs.recommended.rules } },
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
];

export default config;

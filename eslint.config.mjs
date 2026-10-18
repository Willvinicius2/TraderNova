import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Research outputs, vendored sources, build artifacts and external material
    // are not app code: `eslint .` reports app/, components/, lib/, hooks/, db/
    // and the root tooling (scripts/, tests/, config files) only.
    "research/**",
    "vendor/**",
    "dist/**",
    "outputs/**",
    "work/**",
    "public/**",
    ".vinext/**",
    ".wrangler/**",
    ".claude/**",
    // The mobile app is a separate package with its own tooling (mobile/).
    "mobile/**",
  ]),
  {
    files: ["components/ui/**/*.{ts,tsx}", "hooks/use-mobile.ts"],
    rules: {
      // These files are vendored verbatim from shadcn@4.17.0. Keep the
      // registry source intact while applying the stricter rules to Site code.
      "@typescript-eslint/no-unused-vars": "off",
      "react-hooks/purity": "off",
      "react-hooks/set-state-in-effect": "off",
    },
  },
]);

export default eslintConfig;

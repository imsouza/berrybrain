import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",
        muted: "var(--color-muted)",
        panel: "var(--color-panel)",
        border: "var(--color-border)",
        accent: "var(--color-accent)"
      }
    }
  },
  plugins: []
};

export default config;

/** Tailwind config — Skynet Nixtio-inspired theme.
 * Pure black bg, lime + orange accents, chunky rounded cards.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pure black surfaces (no navy bias)
        bg: {
          base: "#000000",       // page background
          card: "#0F0F10",       // elevated card
          card2: "#161618",      // nested surface
          chip: "#1C1C1F",       // small chips / pills
          line: "#26262A",       // hairline borders
        },
        // Brand & accent
        lime: {
          DEFAULT: "#B6F25A",
          dark: "#9DDA3D",
        },
        tang: {
          DEFAULT: "#FB923C",
          dark: "#F97316",
        },
        // Text
        ink: {
          high: "#FFFFFF",
          mid: "#D4D4D8",
          low: "#A1A1AA",
          dim: "#71717A",
        },
        // Reuse semantic shortcuts
        ok: "#B6F25A",
        warn: "#FB923C",
        danger: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
      },
      borderRadius: {
        chunk: "20px",
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 0 0 1px rgba(255,255,255,0.05)",
      },
      animation: {
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
      },
    },
  },
  plugins: [],
};

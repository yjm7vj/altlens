/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Cool ledger paper rather than a warm cream: this is a document you
        // read numbers off, not a marketing page.
        canvas: "#EEF0F3",
        surface: "#FFFFFF",
        ink: "#171C24",
        muted: "#5C6675",
        rule: "#D3D8E0",
        // The two accents carry meaning: teal is cash actually returned,
        // ochre is value still marked on paper. Nothing else is coloured.
        realized: "#0F5C63",
        realizedSoft: "#CFE2E3",
        unrealized: "#A9762B",
        unrealizedSoft: "#EEDFC5",
        called: "#3C4658",
        accent: "#2F3E8F",
        negative: "#8C2F29",
      },
      fontFamily: {
        sans: ["'Inter Tight'", "Inter", "system-ui", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"],
      },
      fontSize: {
        micro: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.01em" }],
      },
      borderRadius: {
        panel: "3px",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(23, 28, 36, 0.06)",
      },
    },
  },
  plugins: [],
};

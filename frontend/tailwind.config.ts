import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202A",
        panel: "#F7F8FA",
        line: "#D9DEE7",
        signal: "#0F766E",
        amber: "#B45309"
      }
    }
  },
  plugins: []
};

export default config;


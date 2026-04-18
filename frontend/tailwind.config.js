/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // China stock market colors — red=up, green=down
        'rise': '#f23645',      // 涨 (red)
        'fall': '#089981',      // 跌 (green)
        'flat': '#787b86',      // 平
        'gold': '#f0b90b',      // 涨停
        'deep-green': '#0a3d2e',
        'dark-bg': '#0d1117',
        'card-bg': '#161b22',
        'border': '#30363d',
        'text-primary': '#e6edf3',
        'text-secondary': '#8b949e',
        'accent-blue': '#388bfd',
        'accent-orange': '#f78166',
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-fast': 'pulse 0.8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flash-rise': 'flashRise 0.5s ease-in-out',
        'flash-fall': 'flashFall 0.5s ease-in-out',
      },
      keyframes: {
        flashRise: {
          '0%, 100%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(242, 54, 69, 0.2)' },
        },
        flashFall: {
          '0%, 100%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(8, 153, 129, 0.2)' },
        },
      },
    },
  },
  plugins: [],
};

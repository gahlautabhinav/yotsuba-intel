import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#2b2622',
        'canvas-soft': '#383330',
        hairline: '#3f3a36',
        ink: '#f7f5f0',
        'body-strong': '#dad2c1',
        body: '#c9c0ad',
        mute: '#aea69c',
        primary: '#f7f5f0',
        'on-primary': '#2b2622',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        serif: ['Instrument Serif', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
} satisfies Config

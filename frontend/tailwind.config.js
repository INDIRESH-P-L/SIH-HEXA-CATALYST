/**
 * Design tokens for the Skill Intelligence Platform.
 *
 * Dashboard Pro x Swiss/International: grid-based, data-dense, hairline rules
 * instead of shadows. Light theme only — a government analytics tool read by
 * working officials, where restraint reads as institutional credibility.
 *
 * Every colour in the application comes from here. No component contains a raw
 * hex value. There is no dark mode and no `dark:` variant anywhere.
 *
 * Tailwind is pinned to v3 deliberately: v4 replaced this config format with
 * CSS `@theme`, which would silently drop every token below.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // primary / secondary / muted text
        ink: { DEFAULT: '#12161C', 2: '#535E6E', 3: '#8A93A1' },
        // page ground
        paper: '#F7F8FA',
        // cards / table header, inset
        surface: { DEFAULT: '#FFFFFF', 2: '#FAFBFC' },
        // border / inner divider
        rule: { DEFAULT: '#DCE1E8', 2: '#EDF0F4' },
        accent: { DEFAULT: '#1F4FA3', wash: '#E7EDF8', line: '#B9CBE8' },

        // GAP SEVERITY — status palette, fixed, never reused as a series colour.
        // Five bands, matching the classification the gap engine produces.
        critical: { DEFAULT: '#D03B3B', bg: '#FBEAEA' },
        significant: { DEFAULT: '#C25A2E', bg: '#FDEDE6' }, // text-safe step of #EC835A
        emerging: { DEFAULT: '#B07800', bg: '#FEF6E4' }, // text-safe step of #FAB219
        met: { DEFAULT: '#0CA30C', bg: '#E8F6E8' },
        strength: { DEFAULT: '#1F4FA3', bg: '#E7EDF8' }, // above expectation: a mentor

        // Architecture layer accents, used only on the architecture map.
        layer: {
          source: '#8A93A1',
          foundation: '#1F4FA3',
          measure: '#1BAF7A',
          decide: '#EB6834',
          observe: '#7A5AA8',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: { DEFAULT: '6px', sm: '4px', lg: '8px' },
      fontSize: {
        // The whole scale. Nothing outside it.
        11: ['11px', { lineHeight: '16px' }],
        12: ['12px', { lineHeight: '18px' }],
        13: ['13px', { lineHeight: '20px' }],
        14: ['14px', { lineHeight: '22px' }],
        16: ['16px', { lineHeight: '24px' }],
        20: ['20px', { lineHeight: '28px' }],
        24: ['24px', { lineHeight: '32px' }],
        32: ['32px', { lineHeight: '38px' }],
        48: ['48px', { lineHeight: '54px' }],
      },
      spacing: {
        // 8 / 12 / 16 / 24 / 32 / 48 — high dashboard density
        1.5: '6px',
        4.5: '18px',
        18: '72px',
        60: '240px', // sidebar
      },
      maxWidth: {
        content: '1200px',
        prose: '75ch', // AI explanations and feedback
      },
      height: { topbar: '56px', control: '36px' },
      boxShadow: {
        // The single permitted shadow, for popovers and dropdowns only.
        popover: '0 4px 12px rgba(18,22,28,0.08)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'level-fill': {
          from: { transform: 'scaleX(0)' },
          to: { transform: 'scaleX(1)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 180ms ease-out',
        'level-fill': 'level-fill 400ms ease-out',
      },
    },
  },
  plugins: [],
}

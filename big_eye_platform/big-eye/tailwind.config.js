/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: 'class',
	content: [
		'./pages/**/*.{ts,tsx}',
		'./components/**/*.{ts,tsx}',
		'./app/**/*.{ts,tsx}',
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px',
			},
		},
		extend: {
			colors: {
				// Dark mode backgrounds (Level 0-3)
				'bg-pure-black': '#000000',
				'bg-near-black': '#0a0a0a',
				'bg-dark-surface': '#141414',
				'bg-hover-surface': '#1e1e1e',
				'bg-elevated-surface': '#282828',
				
				// Text colors
				'text-primary': '#e4e4e7',
				'text-secondary': '#a1a1aa',
				'text-tertiary': '#71717a',
				'text-monospace': '#d4d4d8',
				
				// Threat-level semantic colors
				'threat-critical': '#ef4444',
				'threat-warning': '#f59e0b',
				'threat-safe': '#10b981',
				
				// Accent colors
				'accent-primary': '#3b82f6',
				'accent-hover': '#60a5fa',
				
				// Border colors
				border: {
					subtle: 'rgba(255, 255, 255, 0.1)',
					moderate: 'rgba(255, 255, 255, 0.15)',
					strong: 'rgba(255, 255, 255, 0.2)',
				},
			},
			fontFamily: {
				sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
				mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
			},
			fontSize: {
				'hero': '48px',
				'h1': '36px',
				'h2': '24px',
			},
			borderRadius: {
				sm: '8px',
				md: '12px',
				lg: '16px',
				full: '9999px',
			},
			boxShadow: {
				card: '0 0 0 1px rgba(255, 255, 255, 0.1), 0 4px 12px rgba(0, 0, 0, 0.5)',
				modal: '0 0 0 1px rgba(255, 255, 255, 0.15), 0 8px 24px rgba(0, 0, 0, 0.7)',
				'glow-primary': '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3)',
				'glow-critical': '0 0 16px rgba(239, 68, 68, 0.6)',
				'glow-warning': '0 0 16px rgba(245, 158, 11, 0.6)',
			},
			animation: {
				'fade-in': 'fadeIn 0.25s ease-out',
				'slide-up': 'slideUp 0.25s ease-out',
				'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' },
				},
				slideUp: {
					'0%': { transform: 'translateY(8px)', opacity: '0' },
					'100%': { transform: 'translateY(0)', opacity: '1' },
				},
				pulseGlow: {
					'0%, 100%': { boxShadow: '0 0 16px rgba(59, 130, 246, 0.4)' },
					'50%': { boxShadow: '0 0 24px rgba(59, 130, 246, 0.6)' },
				},
			},
		},
	},
	plugins: [require('tailwindcss-animate')],
}

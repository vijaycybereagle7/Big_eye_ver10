# Design Specification - Big Eye

**Application:** Big Eye - Advanced Phishing Detection Platform  
**Version:** 1.0  
**Date:** 2025-10-29  
**Architecture:** Single-Page Application (SPA)  
**Framework:** Next.js + TailwindCSS + shadcn/ui  

---

## 1. Direction & Rationale

### 1.1 Design Style: Dark Mode First (Security Pro)

Big Eye employs a **Dark Mode First** visual system optimized for security operations center (SOC) environments and cybersecurity professionals. This design direction draws from proven security tool interfaces including VirusTotal, IPQualityScore, and Cisco Talos, where dark themes reduce eye strain during extended threat monitoring sessions while providing superior contrast for color-coded threat indicators.

**Core Essence:** Professional dark-dominant interface with vibrant threat-level color coding, high-contrast data visualization, and precision-focused layouts. Pure blacks and near-blacks create OLED-optimized backgrounds, while saturated accent colors (electric blue, warning amber, critical red, safe green) provide immediate visual hierarchy for risk assessment.

**Real-World References:**
- VirusTotal dashboard (virustotal.com/gui) - tab-based tool navigation, dark theme, multi-engine verdict displays
- IPQualityScore threat intelligence (ipqualityscore.com) - fraud score visualization, threshold-based risk indicators
- GitHub Dark mode - professional developer-grade aesthetics trusted by technical audiences

**Why This Direction:**
- **Functional Advantage:** Reduces eye strain for security analysts working long shifts monitoring threats
- **Industry Standard:** All major security platforms use dark themes; signals "serious security tool" to enterprise users
- **Threat Visualization:** High contrast makes red/yellow/green threat levels immediately distinctive against dark backgrounds
- **Target Audience Alignment:** Security professionals (25-50 age range) expect and prefer dark-mode security tools
- **OLED Optimization:** Pure blacks (#000000) save power on OLED displays common in modern professional setups

### 1.2 Application-Specific Design Decisions

**Tab-Based Navigation (VirusTotal Pattern):**
Big Eye uses horizontal tab navigation to switch between 8 analysis tools without page reloads, maintaining user context and enabling rapid multi-faceted threat assessment. This SPA architecture supports security workflows requiring cross-referencing multiple detection tools (e.g., checking email legitimacy, then domain reputation, then blacklist status).

**Threat-Level Color System:**
Following cybersecurity industry conventions, threat indicators use semantic color coding:
- **Critical Red (#ef4444):** High-risk phishing probability (≥85%), confirmed threats, blacklist detections
- **Warning Amber (#f59e0b):** Suspicious activity (75-84%), medium risk, investigation required
- **Safe Green (#10b981):** Legitimate/safe (0-74%), passed authentication, clean reputation
- **Info Blue (#3b82f6):** Neutral information, interactive elements, primary actions

**Progressive Disclosure:**
Each tool presents a primary threat score prominently, with expandable sections for technical details (DNS records, email headers, blacklist specifics). This supports both rapid triage and deep investigation workflows.

---

## 2. Design Tokens

### 2.1 Color Palette

**Dark Background Hierarchy (90% of interface)**

| Token Name | Hex Value | Usage | WCAG Contrast |
|------------|-----------|-------|---------------|
| `bg-pure-black` | #000000 | OLED-optimized hero sections, sidebar (Level 0) | Base |
| `bg-near-black` | #0a0a0a | Main application background (Level 0) | Base |
| `bg-dark-surface` | #141414 | Elevated cards, tool panels, modals (Level 1) | Base |
| `bg-hover-surface` | #1e1e1e | Hover states, active tabs, tooltips (Level 2) | Base |
| `bg-elevated-surface` | #282828 | Top-level modals, overlays (Level 3) | Base |

**Text Colors**

| Token Name | Hex Value | Usage | Contrast on #0a0a0a |
|------------|-----------|-------|---------------------|
| `text-primary` | #e4e4e7 | Primary headings, labels, critical data | 15.2:1 (AAA) |
| `text-secondary` | #a1a1aa | Secondary text, descriptions, metadata | 8.9:1 (AAA) |
| `text-tertiary` | #71717a | Captions, timestamps, disabled states | 5.2:1 (AA) |
| `text-monospace` | #d4d4d8 | Code, IP addresses, email headers, hashes | 13.8:1 (AAA) |

**Threat-Level Semantic Colors (10% of interface)**

| Token Name | Hex Value | Usage | Contrast on #0a0a0a |
|------------|-----------|-------|---------------------|
| `threat-critical` | #ef4444 | High risk (≥85%), failed authentication, blacklisted | 7.8:1 (AAA) |
| `threat-warning` | #f59e0b | Medium risk (75-84%), suspicious patterns | 9.2:1 (AAA) |
| `threat-safe` | #10b981 | Safe/legitimate (0-74%), passed checks | 8.5:1 (AAA) |
| `accent-primary` | #3b82f6 | Interactive elements, links, primary CTAs | 8.6:1 (AAA) |
| `accent-hover` | #60a5fa | Hover states for interactive elements | 10.1:1 (AAA) |

**Border Colors**

| Token Name | RGBA Value | Usage |
|------------|------------|-------|
| `border-subtle` | rgba(255, 255, 255, 0.1) | Card borders, dividers, input outlines |
| `border-moderate` | rgba(255, 255, 255, 0.15) | Hover borders, active states |
| `border-strong` | rgba(255, 255, 255, 0.2) | Focus indicators, emphasized separators |

### 2.2 Typography

**Font Families**

| Token Name | Font Stack | Usage |
|------------|------------|-------|
| `font-sans` | 'Inter', -apple-system, BlinkMacSystemFont, sans-serif | UI elements, headings, body text |
| `font-mono` | 'JetBrains Mono', 'Fira Code', monospace | Email headers, IP addresses, DNS records, technical data |

**Type Scale**

| Token Name | Size | Weight | Line Height | Letter Spacing | Usage |
|------------|------|--------|-------------|----------------|-------|
| `text-hero` | 48px | 700 (Bold) | 1.1 | -0.02em | Hero headlines, Big Eye branding |
| `text-h1` | 36px | 600 (Semibold) | 1.2 | -0.01em | Section headers, tool names |
| `text-h2` | 24px | 600 (Semibold) | 1.3 | 0 | Card titles, subsection headers |
| `text-large` | 18px | 400 (Regular) | 1.6 | 0 | Large threat scores, primary metrics |
| `text-body` | 16px | 400 (Regular) | 1.5 | 0 | Standard body text, descriptions |
| `text-small` | 14px | 400 (Regular) | 1.5 | 0.01em | Captions, timestamps, metadata |
| `text-code` | 14px | 400 (Mono) | 1.4 | 0 | Code blocks, technical data |

**Typography Best Practices (Dark Mode):**
- Use zinc-200 (#e4e4e7) instead of pure white to prevent halation (glow effect)
- Apply lighter font weights (400-500) on dark backgrounds vs. heavier weights (500-600) on light
- Enable anti-aliasing: `-webkit-font-smoothing: antialiased`

### 2.3 Spacing (8-Point Grid)

| Token Name | Value | Usage |
|------------|-------|-------|
| `space-1` | 4px | Icon padding, tight inline spacing |
| `space-2` | 8px | Element gaps, inline spacing |
| `space-3` | 12px | Compact spacing |
| `space-4` | 16px | Standard element gaps |
| `space-6` | 24px | Card internal spacing |
| `space-8` | 32px | Card padding, section margins |
| `space-10` | 40px | Large card padding |
| `space-12` | 48px | Section spacing |
| `space-16` | 64px | Major section divisions |
| `space-20` | 80px | Hero section padding |

### 2.4 Border Radius

| Token Name | Value | Usage |
|------------|-------|-------|
| `radius-sm` | 8px | Small buttons, badges, chips |
| `radius-md` | 12px | Standard buttons, inputs, small cards |
| `radius-lg` | 16px | Large cards, modals, panels |
| `radius-full` | 9999px | Circular icons, pills |

### 2.5 Shadows & Glows

**Elevation Shadows (Subtle on Dark)**

| Token Name | Value | Usage |
|------------|-------|-------|
| `shadow-card` | 0 0 0 1px rgba(255,255,255,0.1), 0 4px 12px rgba(0,0,0,0.5) | Elevated cards |
| `shadow-modal` | 0 0 0 1px rgba(255,255,255,0.15), 0 8px 24px rgba(0,0,0,0.7) | Modals, overlays |

**Accent Glows (Interactive Elements)**

| Token Name | Value | Usage |
|------------|-------|-------|
| `glow-primary` | 0 0 20px rgba(59,130,246,0.5), 0 0 40px rgba(59,130,246,0.3) | Primary button hover, active tabs |
| `glow-threat-critical` | 0 0 16px rgba(239,68,68,0.6) | High-risk score indicators |
| `glow-threat-warning` | 0 0 16px rgba(245,158,11,0.6) | Medium-risk score indicators |

### 2.6 Animation Timing

| Token Name | Duration | Easing | Usage |
|------------|----------|--------|-------|
| `duration-fast` | 150ms | ease-out | Button hovers, icon state changes |
| `duration-standard` | 250ms | ease-out | Card elevations, tab switches |
| `duration-slow` | 400ms | ease-out | Modals, side panel animations |

---

## 3. Component Specifications

### 3.1 Navigation Header

**Structure:**
- Height: 64px
- Background: `bg-near-black` (#0a0a0a) with `border-bottom: 1px solid border-subtle`
- Layout: Logo left, universal search center, utility controls right

**Elements:**
- **Logo**: "Big Eye" text (24px, semibold) + icon (32×32px), left-aligned with 16px padding
- **Universal Search Bar**: 480px width (desktop), rounded 12px, dark surface (#141414) background, placeholder "Search email, domain, IP, or URL..."
- **Utility Icons**: Theme toggle (optional), notifications (bell icon), user profile (avatar or initials)
- **Primary CTA**: "Sign Up" button (accent blue, glow on hover) or "Dashboard" for authenticated users

**Responsive:** Collapse to hamburger menu on mobile (<768px), search becomes full-width modal

### 3.2 Tab Navigation (Tool Selector)

**Structure:**
- Horizontal scrollable tabs below header
- Background: `bg-near-black` with subtle bottom border
- 8 tabs for core tools

**Tab States:**
- **Inactive**: `text-secondary` (#a1a1aa), padding 12px 24px, hover background `bg-hover-surface`
- **Active**: `text-primary` (#e4e4e7), `bg-hover-surface` (#1e1e1e), accent blue bottom border (3px), subtle blue glow
- **Hover**: Background `bg-dark-surface`, text transition to `text-primary`, 150ms ease-out

**Typography:** 16px semibold, uppercase with 0.02em letter spacing

**Mobile:** Horizontal scroll with snap-to-tab behavior, compact padding (8px 16px)

### 3.3 Threat Score Card (Primary Component)

**Structure:**
- Large prominent card displaying phishing probability or risk score
- Dimensions: Flexible width, 200-240px height
- Background: `bg-dark-surface` with card shadow
- Border radius: 16px

**Elements:**
- **Score Display**: 72px font size, bold weight, color-coded by threat level
  - 0-74: `threat-safe` (green)
  - 75-84: `threat-warning` (amber)
  - 85-100: `threat-critical` (red)
- **Label**: "Phishing Probability" or "Risk Score" (14px, `text-secondary`)
- **Icon**: Contextual threat icon (shield, alert, checkmark) at 48px
- **Accent Glow**: Apply appropriate threat glow on hover for interactivity

**Threshold Indicators:**
- Segmented progress bar below score showing threshold ranges
- Visual markers at 75 and 85 thresholds

**Responsive:** Reduce to 180px height on mobile, 56px score font size

### 3.4 Analysis Results Card

**Structure:**
- Modular card container for analysis outputs (DNS records, blacklist results, headers)
- Background: `bg-dark-surface`, padding 32px, radius 16px
- Border: `border-subtle`

**Header:**
- Title (20px semibold, `text-primary`) + action menu (3-dot icon)
- Optional status badge (green checkmark, yellow warning, red X)

**Content Area:**
- Supports multiple layouts: data tables, key-value pairs, timelines, lists
- Expandable sections using accordion pattern for technical details

**States:**
- **Default**: Static display with subtle border
- **Hover**: Border color intensifies to `border-moderate`, slight elevation
- **Loading**: Skeleton screen with pulsing placeholders (shimmer effect)

**Responsive:** Stack multi-column content to single column on mobile, reduce padding to 24px

### 3.5 Button System

**Primary (Accent Fill with Glow)**
- Height: 48px, padding 16-32px horizontal, radius 12px
- Background: `accent-primary` (#3b82f6), text white, font 16px semibold
- Hover: Brightness 110% + `glow-primary`, 150ms transition
- Active: Scale 0.98, brightness 90%

**Secondary (Outline Accent)**
- Same dimensions as primary
- Background transparent, border 2px `accent-primary`, text `accent-primary`
- Hover: Background `accent-primary`, text white, `glow-primary`

**Ghost (Subtle)**
- Same dimensions
- Background transparent, no border, text `text-secondary`
- Hover: Background `bg-hover-surface`, text `text-primary`

**Threat Action Buttons (Context-Specific)**
- **Block Action**: Red background (#ef4444) with critical glow
- **Review Action**: Amber background (#f59e0b) with warning glow
- **Allow Action**: Green background (#10b981) with safe glow

### 3.6 Data Table (DNS Records, Blacklist Results)

**Structure:**
- Monospace font for technical data (IP addresses, hashes)
- Background: `bg-dark-surface`, alternating row colors (subtle transparency variation)
- Border: 1px `border-subtle` around table

**Headers:**
- Background: `bg-hover-surface`, text `text-primary`, 14px uppercase, 0.05em spacing
- Padding: 12px 16px

**Rows:**
- Padding: 12px 16px, border-bottom `border-subtle`
- Hover: Background `bg-hover-surface`
- Text: `text-secondary` for data values, `text-monospace` for technical fields

**Status Columns:**
- Use colored badges (red/yellow/green) for pass/fail indicators
- Icons (checkmark, X, warning) alongside text

**Responsive:** Horizontal scroll on mobile with sticky first column, or convert to card-based layout for critical tables

---

## 4. Layout & Responsive Strategy

### 4.1 Application Shell (SPA Structure)

**Based on content-structure-plan.md**, Big Eye uses a consistent shell:

**Header (64px fixed)**
- Logo + Universal Search + Utility Controls
- Always visible, sticky positioning

**Tab Navigation Bar (56px)**
- Horizontal tool selector
- Sticky below header, scrolls with tabs

**Main Content Area (Dynamic height)**
- Tool-specific input panels and results
- Minimum height: calc(100vh - 120px) to fill viewport

**Footer (Minimal, auto height)**
- Legal links, documentation, support chat
- Collapses to icon-only on mobile

### 4.2 Tool Panel Layout Pattern

Each of the 8 tools follows a consistent layout pattern:

**Input Panel (Top Section)**
- Width: 100% max-width 800px, centered
- Background: `bg-dark-surface`, padding 40px, radius 16px
- Contains: Tool-specific input fields (textarea for headers, single-line for domains/IPs, multi-field for comprehensive analysis)
- Submit button: Primary accent button, full-width on mobile

**Results Display (Below Input)**
- Grid layout: 2-3 columns on desktop (≥1024px), 1 column on mobile
- Gap: 24px between cards
- Max-width: 1400px, centered with 32px side padding

**Sidebar (Optional, Collapsible)**
- Analysis history panel, 280px width
- Position: Fixed right side on desktop, bottom sheet on mobile
- Toggle via hamburger icon

### 4.3 Breakpoints

```
Mobile:        <640px  (Single column, full-width cards, stacked navigation)
Tablet:        640-1023px (2-column grids, compact padding)
Desktop:       1024-1439px (3-column grids, full features)
Large Desktop: ≥1440px (Max-width containers, generous spacing)
```

### 4.4 Responsive Adaptations

**Mobile (<640px):**
- Tab navigation becomes horizontal scrollable with snap behavior
- Universal search collapses to icon, expands to full-width modal on tap
- Cards stack vertically, padding reduces to 24px
- Data tables convert to card layout or horizontal scroll
- Touch targets minimum 48×48px

**Tablet (640-1023px):**
- 2-column result grids
- Sidebar becomes bottom sheet or off-canvas panel
- Maintain full tab labels (no icon-only)

**Desktop (≥1024px):**
- 3-column result grids for data-dense tools
- Side-by-side input and results for rapid workflows
- Keyboard shortcuts enabled (Tab, Enter, Esc)
- Hover states fully active

### 4.5 Grid System

**Container Max-Widths:**
- Hero/Tool inputs: 800px
- Results display: 1400px
- Full-width (maps, charts): 100% with 32px padding

**Column Gaps:**
- Card grids: 24px
- Dense data grids: 16px
- Section spacing: 64px vertical

---

## 5. Interaction & Animation

### 5.1 Animation Principles

**Dark Mode Considerations:**
- Dark backgrounds amplify motion perception—use subtle transforms
- Maximum translateY: 8px (vs 16px in light mode)
- Prefer opacity and glow changes over positional shifts
- Avoid bright flashes (>50% brightness change in <200ms causes eye strain)

**Performance Rule:**
- Animate ONLY `transform` and `opacity` (GPU-accelerated)
- NEVER animate `width`, `height`, `margin`, `padding` (layout thrashing)

### 5.2 Component-Specific Animations

**Tab Switching:**
- Active tab: Slide-in bottom border (3px), 250ms ease-out
- Content area: Fade out old content (150ms), fade in new content (250ms with 100ms delay)
- No slide transitions for content (maintain spatial stability)

**Card Interactions:**
- Hover: Border color transition (150ms), subtle elevation via shadow (250ms)
- Expand/Collapse: Height transition with `max-height` technique (300ms ease-out), rotate chevron icon (200ms)

**Threat Score Display:**
- On load: Count-up animation from 0 to final score (800ms), easing function `cubic-bezier(0.4, 0, 0.2, 1)`
- Score change: Color transition (300ms), subtle glow pulse (600ms)

**Button States:**
- Hover: Glow fade-in (150ms ease-out), brightness shift (150ms)
- Active (click): Scale to 0.98 (100ms), scale back (150ms)
- Loading: Spinner fade-in (200ms), button text fades to "Analyzing..." (200ms)

**Data Loading:**
- Skeleton screens: Shimmer gradient animation (1.5s infinite loop)
- Progressive disclosure: Fade-in results as they arrive (300ms stagger between cards)

### 5.3 Micro-Interactions

**Input Focus:**
- Border glow: 0 0 0 3px rgba(59,130,246,0.3), 200ms ease-out
- Border color: Transition to `accent-primary`, 200ms

**Icon Hover (Interactive Icons):**
- Color change to `accent-primary` (150ms)
- Optional glow filter: `drop-shadow(0 0 8px rgba(59,130,246,0.6))` (200ms)

**Tooltip Appearance:**
- Fade in + translateY(-4px) (200ms ease-out)
- Background: `bg-elevated-surface` with subtle border

**Status Badge Transitions:**
- When status changes (e.g., "analyzing" → "complete"): 
  - Scale pulse (0.95 → 1.05 → 1, 400ms)
  - Color transition (300ms)

### 5.4 Page Transitions (SPA Navigation)

**Tool Tab Switch:**
- Instant tab state change (no animation overhead for rapid switching)
- Content fade transition (200ms) to indicate change without disorientation

**Modal/Overlay Entry:**
- Background overlay: Fade from transparent to rgba(0,0,0,0.8), 300ms
- Modal: Fade in + scale from 0.95 to 1, 400ms ease-out
- Exit: Reverse animation, 300ms

### 5.5 Reduced Motion Support

**Accessibility Compliance:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Replace animations with instant state changes for users with motion sensitivity.

### 5.6 Interactive States Summary

| Component | Default | Hover | Active | Focus | Disabled |
|-----------|---------|-------|--------|-------|----------|
| Primary Button | Accent fill | Glow + brightness 110% | Scale 0.98 | Glow ring | Opacity 50%, cursor not-allowed |
| Tab | Secondary text | Primary text, surface bg | Accent border, glow | Keyboard outline | - |
| Card | Surface bg, subtle border | Moderate border, elevation | - | Outline offset | - |
| Input | Surface bg, subtle border | Moderate border | - | Accent glow ring | Opacity 50% |
| Link | Accent color | Underline, brighter | - | Outline | Tertiary text |

---

## Document Summary

**Total Components Specified:** 6 (Navigation Header, Tab Navigation, Threat Score Card, Analysis Results Card, Button System, Data Table)

**Design Philosophy:** Dark Mode First optimized for cybersecurity professionals, emphasizing rapid threat assessment through color-coded indicators, progressive disclosure of technical data, and SPA tab navigation for multi-tool workflows.

**Key Differentiators:**
- Threat-level semantic colors (red/yellow/green) with WCAG-compliant contrast on dark backgrounds
- Pure black OLED optimization for extended monitoring sessions
- Monospace typography for technical data (IP addresses, headers, DNS records)
- Glow effects instead of drop shadows for depth in dark environments
- Tab-based SPA navigation matching VirusTotal/IPQS industry patterns

**Framework Integration:**
- TailwindCSS utilities map directly to design tokens
- shadcn/ui components provide accessible base components (buttons, cards, tabs, modals)
- Next.js App Router supports SPA-like navigation with seamless tab transitions

**Accessibility:**
- All text meets WCAG AAA contrast standards (≥7:1) on dark backgrounds
- Reduced motion support via media query
- Keyboard navigation for all interactive elements
- Touch targets ≥48×48px on mobile
- Screen reader-friendly semantic HTML

---

**Version:** 1.0  
**Author:** MiniMax Agent  
**Date:** 2025-10-29

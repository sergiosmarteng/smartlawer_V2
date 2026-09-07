---

name: ui-ux-design
description: Design, review and improve high-quality responsive user interfaces and user experiences for Next.js, React, TypeScript and modern web applications.
license: MIT
compatibility: opencode
metadata:
  category: design
  stack: ui-ux
  version: "1.0.0"
orchestration:
  lead_for:
    - ui-redesign
  support_for: []
  conflicts_with:
    - nextjs-frontend
---

# UI/UX Design

Use this skill whenever designing, implementing, reviewing or improving user interfaces, user flows, dashboards, forms, landing pages, mobile-responsive layouts or design systems.

The objective is to create interfaces that are clear, visually refined, accessible, consistent, responsive and easy to use.

Do not optimize only for appearance. A high-quality interface must also support usability, accessibility, performance and real user goals.

## Core Design Principles

Every interface should be:

* Clear
* Consistent
* Accessible
* Responsive
* Visually balanced
* Easy to scan
* Easy to navigate
* Forgiving of user mistakes
* Predictable
* Appropriate for the product context

Prefer clarity over decoration.

Prefer familiar interaction patterns unless a custom interaction provides clear value.

Avoid unnecessary complexity, visual noise and excessive animation.

## Initial Inspection

Before modifying an interface:

1. Inspect the current component structure.
2. Identify the design system or styling approach.
3. Inspect existing:

   * colors
   * typography
   * spacing
   * border radius
   * shadows
   * buttons
   * forms
   * cards
   * tables
   * modal patterns
4. Determine:

   * target users
   * primary user goals
   * desktop and mobile usage
   * accessibility requirements
   * existing UI conventions
5. Reuse existing components and tokens where possible.
6. Avoid introducing a second visual language into the same product.

Do not redesign isolated screens without considering the wider application.

## User-Centered Design

Before designing, identify:

* Who is using the interface?
* What is their primary task?
* What information is most important?
* What decision must they make?
* What can go wrong?
* What state are they currently in?
* What should happen next?

Prioritize the main task visually.

Secondary actions should not compete with the primary action.

Avoid presenting every available option at the same visual priority.

## Visual Hierarchy

Use hierarchy to guide attention.

Control hierarchy through:

* size
* weight
* contrast
* spacing
* position
* grouping
* color
* alignment

A screen should clearly communicate:

1. Where the user is.
2. What the screen is about.
3. What information matters most.
4. What action should be taken next.

Avoid using several elements with equal high emphasis.

Use one dominant primary action per section where possible.

## Layout

Use structured and predictable layouts.

Prefer:

* consistent content widths
* clear alignment
* logical grouping
* stable spacing
* meaningful whitespace
* responsive grids
* readable line lengths

Avoid:

* random alignment
* overly wide text blocks
* cramped sections
* unnecessary nested cards
* excessive boxed containers
* large unused areas without purpose
* content touching screen edges

For text-heavy content, aim for a readable line length rather than full-width paragraphs.

Use containers and grids consistently across pages.

## Spacing System

Use a consistent spacing scale.

Example:

```text
4px
8px
12px
16px
24px
32px
48px
64px
```

Prefer multiples of four unless the existing design system specifies otherwise.

Use spacing to communicate relationships:

* smaller spacing within a group
* larger spacing between groups
* larger section spacing between unrelated content

Do not fix layout problems with arbitrary margins scattered across components.

Centralize spacing through design tokens or utility classes.

## Typography

Typography should create clear hierarchy and remain readable.

Use a limited type scale.

Example hierarchy:

```text
Display
Page title
Section title
Card title
Body
Supporting text
Caption
```

Guidelines:

* Use no more than two font families unless required.
* Use font weight intentionally.
* Avoid very light text for body content.
* Maintain sufficient line height.
* Avoid overly small text.
* Use sentence case for most interface labels.
* Keep headings concise.
* Keep body text readable on mobile.
* Avoid excessive uppercase text.
* Do not use bold for every important sentence.

Recommended minimum sizes:

* Body text: 16px where practical
* Supporting text: 14px
* Small labels: avoid going below 12px
* Form inputs: at least 16px on mobile to reduce browser zoom issues

## Color

Use color with purpose.

Color should communicate:

* hierarchy
* interaction
* status
* branding
* emphasis

Do not use color as the only way to communicate meaning.

Ensure text and interactive elements have sufficient contrast.

Use semantic colors consistently:

* Success
* Warning
* Error
* Information
* Neutral
* Primary action

Avoid:

* too many accent colors
* saturated colors everywhere
* low-contrast gray text
* excessive gradients
* inconsistent status colors
* decorative color that reduces readability

Support both light and dark mode only when the product requires it.

Dark mode should be designed deliberately, not generated by simply inverting colors.

## Design Tokens

Prefer reusable tokens for:

* colors
* typography
* spacing
* radius
* borders
* shadows
* breakpoints
* transitions
* z-index

Example:

```typescript
const tokens = {
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
  radius: {
    sm: "0.375rem",
    md: "0.625rem",
    lg: "0.875rem",
  },
};
```

Do not hardcode slightly different visual values across many components.

## Components

Create reusable components only when reuse is real.

Common reusable components include:

* Button
* Input
* Select
* Checkbox
* Radio group
* Textarea
* Modal
* Dialog
* Drawer
* Card
* Table
* Badge
* Tooltip
* Dropdown
* Tabs
* Pagination
* Alert
* Toast
* Empty state
* Skeleton
* Breadcrumb
* Avatar

Every reusable component should support:

* consistent visual states
* keyboard interaction
* disabled state
* loading state
* error state where applicable
* responsive behavior
* accessible labels
* focus visibility

Avoid creating overly generic components with dozens of configuration props.

## Buttons

Buttons should communicate action priority.

Use a limited hierarchy:

* Primary
* Secondary
* Tertiary
* Destructive
* Icon-only

Rules:

* Use clear action-oriented labels.
* Avoid vague labels such as “Submit” when a more specific label is possible.
* Use “Create assignment” instead of “Submit”.
* Use “Save changes” instead of “Confirm”.
* Keep destructive actions visually distinct.
* Do not place multiple primary buttons together without strong reason.
* Maintain adequate touch target size.
* Show loading state during submission.
* Prevent accidental duplicate submission.
* Keep icon-only buttons accessible with labels or tooltips.

Recommended touch target:

```text
Minimum 44 × 44 CSS pixels
```

## Forms

Forms should minimize cognitive effort.

Use:

* visible labels
* logical grouping
* helpful instructions
* sensible defaults
* inline validation
* clear required indicators
* appropriate input types
* autocomplete attributes
* error summaries for long forms
* success confirmation

Avoid:

* placeholder-only labels
* validation only after final submission
* clearing user input after an error
* excessive required fields
* confusing date formats
* unexplained technical terms
* generic error messages

Form errors should explain:

* what is wrong
* how to correct it

Example:

```text
Password must contain at least 8 characters.
```

Avoid:

```text
Invalid input.
```

For long forms:

* group fields into sections
* use progressive disclosure
* show progress when appropriate
* preserve entered values
* allow users to go back safely

## Input States

Every form control should support:

* Default
* Hover
* Focus
* Filled
* Disabled
* Read-only
* Error
* Success where useful

Focus states must remain visible.

Do not remove browser outlines unless replaced with an equally visible focus indicator.

## Navigation

Navigation should be predictable.

Use:

* clear active states
* meaningful labels
* stable placement
* breadcrumbs for deep hierarchy
* responsive mobile navigation
* accessible keyboard behavior

Avoid:

* hiding important sections behind unclear icons
* changing navigation placement across pages
* using identical styling for active and inactive items
* overly deep nesting
* menus that close unexpectedly
* navigation labels based on internal technical terminology

The current location should always be understandable.

## Dashboard Design

Dashboards should help users understand status and take action.

Prioritize:

1. Critical alerts
2. Important trends
3. Actionable metrics
4. Recent activity
5. Supporting detail

Avoid filling dashboards with decorative metrics that do not support decisions.

For each metric, consider:

* label
* current value
* comparison period
* trend
* context
* status
* action

Use charts only when they communicate information more clearly than text or a table.

Do not display a chart merely to make the screen look advanced.

## Data Tables

Tables should support scanning and decision-making.

Include where relevant:

* clear column labels
* alignment by data type
* sorting
* filtering
* pagination
* search
* row actions
* loading state
* empty state
* error state
* responsive behavior

Align:

* text to the left
* numbers to the right
* statuses consistently
* dates consistently

Do not overload every row with many visible actions.

Use a menu for secondary row actions.

For mobile:

* allow horizontal scrolling where necessary
* provide card alternatives only when they improve usability
* keep important columns visible
* avoid hiding critical information without another access path

## Cards

Cards should group related content.

Use cards when they create meaningful separation.

Avoid:

* putting every section inside a card
* cards inside cards
* excessive shadows
* several competing border styles
* large empty cards
* decorative cards with no functional purpose

Cards should have:

* clear title
* structured content
* consistent padding
* optional action
* clear state

## Modals and Dialogs

Use modals only for focused tasks that should temporarily interrupt the current flow.

Good uses:

* confirmation
* short form
* focused detail
* destructive action verification

Avoid modals for:

* long workflows
* complex multi-step forms
* large data tables
* content that should have a shareable URL
* actions that require significant navigation

Modal requirements:

* focus trapping
* escape-key support
* accessible title
* clear close action
* return focus after closing
* background interaction prevented
* mobile-safe layout
* scroll handling

Destructive confirmations should clearly name the affected item.

## Feedback and System Status

The interface must communicate what is happening.

Provide feedback for:

* loading
* success
* failure
* empty data
* partial completion
* background processing
* offline state
* permission denial
* rate limits

Users should never wonder whether an action worked.

Use:

* inline messages
* status banners
* toast notifications
* progress indicators
* skeletons
* disabled states

Use toast notifications for temporary confirmation, not for critical information that must remain visible.

## Loading States

Choose loading indicators based on expected duration.

Use:

* button spinner for short actions
* skeleton for content loading
* progress bar for measurable operations
* status message for long-running processes

Avoid:

* full-screen spinners for small local updates
* changing the whole page layout during loading
* indefinite spinners without explanation
* fake progress percentages

Prevent layout shift by reserving space where possible.

## Empty States

Empty states should explain:

* why there is no data
* whether this is expected
* what the user can do next

Example:

```text
No assignments have been created yet.

Create your first assignment to start adding questions.
```

Avoid empty tables with only:

```text
No data.
```

Provide an action when appropriate.

## Error States

Error messages should be:

* clear
* actionable
* polite
* specific
* safe

Explain what the user can do next.

Example:

```text
We could not load the student list. Check your connection and try again.
```

Do not expose:

* stack traces
* database messages
* raw API errors
* internal IDs unless useful for support
* security-sensitive details

For persistent failures, include a retry action.

## Destructive Actions

Destructive actions should:

* be visually distinct
* clearly explain impact
* require confirmation when irreversible
* avoid accidental placement near common actions
* support undo when practical

Do not use generic confirmation text such as:

```text
Are you sure?
```

Use:

```text
Delete “Anatomy Final Exam”?

This action cannot be undone.
```

## Responsive Design

Design mobile-first where practical.

Test common breakpoints, but do not design only for fixed device widths.

Ensure:

* text remains readable
* controls remain tappable
* tables remain usable
* navigation adapts
* dialogs fit the viewport
* content does not overflow
* actions remain reachable
* forms do not become excessively long or cramped

Avoid:

* horizontal page scrolling
* fixed widths that break on small screens
* hidden critical actions
* tiny touch targets
* hover-only interactions
* desktop layouts simply scaled down

Use responsive grids and flexible widths.

## Mobile UX

On mobile:

* prioritize essential content
* keep primary actions reachable
* avoid excessive top padding
* reduce unnecessary columns
* use bottom sheets or drawers where appropriate
* ensure sticky elements do not cover content
* support the on-screen keyboard
* test landscape and portrait orientation
* account for safe areas

Place frequent primary actions within comfortable reach where appropriate.

Do not put critical interactions only in hover states.

## Accessibility

Target WCAG 2.2 AA where practical.

Check:

* semantic HTML
* logical heading order
* keyboard access
* visible focus
* form labels
* accessible names
* sufficient contrast
* text resizing
* screen-reader announcements
* modal focus management
* table semantics
* landmark regions
* skip navigation
* error identification
* status updates
* reduced-motion support

Use native HTML elements before custom ARIA implementations.

Prefer:

```html
<button type="button">Save changes</button>
```

Avoid:

```html
<div role="button" tabindex="0">Save changes</div>
```

Use ARIA only when native semantics are insufficient.

## Keyboard Interaction

Ensure users can:

* navigate with Tab and Shift+Tab
* activate controls with Enter or Space
* close dialogs with Escape
* navigate menus appropriately
* identify current focus
* avoid keyboard traps

Interactive elements should follow logical DOM order.

Do not use positive `tabindex` values.

## Focus Management

Manage focus after:

* modal opening
* modal closing
* form validation failure
* navigation
* dynamic content insertion
* deletion
* route changes where necessary

After an error, move focus to the error summary or first invalid field where appropriate.

After deleting an item, move focus to a logical nearby element.

## Animation and Motion

Use motion to explain relationships and state changes.

Good uses:

* menu opening
* modal transitions
* state changes
* content insertion
* drag interaction
* progress feedback

Avoid:

* excessive parallax
* long page transitions
* animation on every element
* distracting floating effects
* motion that delays interaction
* dramatic animation in professional tools

Animations should generally be fast and subtle.

Typical duration:

```text
120ms–250ms
```

Support reduced-motion preferences.

Example:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Microcopy

Interface text should be:

* concise
* specific
* human
* consistent
* action-oriented

Prefer:

```text
Save changes
Create question
Upload PDF
Try again
```

Avoid:

```text
Proceed
Execute
Confirm action
Operation failed
```

Use terminology users understand, not internal database or engineering terminology.

Keep capitalization consistent.

## Icons

Icons should support understanding, not replace clear labels unnecessarily.

Use:

* familiar icons
* consistent icon family
* consistent size
* text labels for unfamiliar actions
* tooltips for icon-only controls

Do not use several different icon styles in one interface.

Do not rely on icons alone for destructive or ambiguous actions.

## Content Design

Content should be:

* concise
* structured
* scannable
* relevant
* written for the user’s level of knowledge

Use:

* headings
* short paragraphs
* bullets when useful
* descriptive labels
* progressive disclosure

Avoid:

* long unbroken text
* technical jargon
* repeated instructions
* verbose helper text
* unexplained abbreviations

## Consistency

Maintain consistency in:

* component behavior
* naming
* spacing
* color meaning
* button hierarchy
* form patterns
* table actions
* navigation
* empty states
* error messages
* loading indicators

Users should not need to relearn interactions on every page.

## Design System Integration

When a design system exists:

* reuse its primitives
* follow token values
* extend components carefully
* document new variants
* avoid one-off overrides
* maintain visual compatibility

When no design system exists, establish a minimal shared foundation before building many screens.

At minimum define:

* color palette
* typography scale
* spacing scale
* border radius
* shadows
* breakpoints
* button variants
* form controls
* status colors

## Tailwind CSS

When using Tailwind:

* reuse existing utility patterns
* use theme tokens
* avoid arbitrary values unless justified
* extract repeated component styles
* keep class names organized
* preserve responsive readability
* avoid giant unreadable class strings where component abstraction would help

Prefer:

```tsx
<div className="rounded-lg border bg-card p-6 shadow-sm">
```

Avoid repeated arbitrary values such as:

```tsx
<div className="rounded-[13px] p-[19px] shadow-[0_3px_17px_rgba(...)]">
```

unless they come from a defined design specification.

## High-Quality Visual Style

Aim for a refined interface through restraint.

Use:

* clean surfaces
* balanced whitespace
* consistent alignment
* subtle borders
* restrained shadows
* clear type hierarchy
* limited accent color
* polished interaction states
* meaningful visual grouping

Avoid common low-quality patterns:

* excessive gradients
* glowing borders everywhere
* overly large headings
* glassmorphism on every surface
* too many floating cards
* unnecessary shadows
* random rounded corners
* inconsistent icon sizing
* overcrowded dashboards
* low-contrast gray text
* excessive animation
* decorative charts without meaning
* generic AI-style purple gradients unless appropriate to the brand

A professional interface should feel intentional, not overdesigned.

## Product-Specific UX

For education, healthcare or enterprise systems:

* prioritize clarity and trust
* avoid playful visuals that reduce seriousness
* make critical statuses obvious
* show confirmation for high-impact actions
* preserve auditability
* provide clear progress and history
* avoid hiding important information
* support dense data without becoming cluttered

For medical or academic systems:

* do not use color alone for critical status
* make labels explicit
* keep data presentation precise
* separate draft, published, submitted and evaluated states clearly
* prevent accidental destructive actions
* show save and synchronization status
* use readable tables and filters
* support long names and domain terminology

## UX Flow Review

When reviewing a user flow, trace the complete journey:

1. Entry point
2. Orientation
3. Main action
4. Validation
5. Confirmation
6. Failure path
7. Recovery
8. Completion
9. Next action

Check for:

* dead ends
* unclear next steps
* unnecessary steps
* repeated data entry
* missing confirmation
* poor error recovery
* lost user progress
* permission confusion
* hidden system status

A polished screen can still have a poor user flow.

## UX Heuristics

Review against these principles:

* System status is visible.
* Language matches the user’s mental model.
* Users remain in control.
* Patterns are consistent.
* Errors are prevented where possible.
* Users should recognize options rather than remember them.
* Frequent tasks should be efficient.
* Interfaces should remain visually focused.
* Errors should support recovery.
* Help should be available when needed.

## Review Output Format

When reviewing an existing interface, provide findings in priority order.

Use:

```text
[Priority] Finding title

Location:
Page, component or interaction.

Problem:
What makes the experience difficult, unclear or inconsistent.

User impact:
How this affects real users.

Recommendation:
The smallest practical improvement.

Acceptance criteria:
How to verify the improvement.
```

Priority levels:

* Critical: blocks task completion or causes serious accessibility or safety risk
* High: creates frequent confusion, errors or major friction
* Medium: meaningfully reduces clarity or efficiency
* Low: polish or consistency improvement
* Suggestion: optional enhancement

Do not report visual preferences as objective defects.

## Implementation Workflow

When asked to improve a UI:

1. Inspect existing styles and components.
2. Identify the primary user task.
3. Fix information hierarchy.
4. Fix layout and spacing.
5. Improve component consistency.
6. Add complete states.
7. Improve responsive behavior.
8. Improve accessibility.
9. Add restrained visual polish.
10. Verify functionality and performance.

Do not begin by changing colors and shadows before addressing structure and usability.

## Required States

For every interactive or data-driven feature, consider:

* Default
* Hover
* Focus
* Active
* Selected
* Disabled
* Loading
* Empty
* Error
* Success
* Unauthorized
* Not found

Do not ship only the ideal success state.

## Testing

Test on:

* desktop
* tablet
* mobile
* keyboard-only navigation
* reduced motion
* slow network
* empty data
* long content
* validation errors
* API failure
* unauthorized access

Use project tools where available:

* Playwright
* Cypress
* React Testing Library
* Storybook
* axe
* Lighthouse

Example checks:

```bash
npm run lint
npm run typecheck
npm run build
npx playwright test
```

For accessibility:

```bash
npx axe http://localhost:3000
```

Use the actual configured commands in the repository.

## Visual Verification

Check:

* alignment
* spacing consistency
* text wrapping
* overflow
* hover state
* focus state
* mobile layout
* empty state
* error state
* dark mode if supported
* long labels
* large datasets
* zoom at 200%
* browser console errors

Take screenshots only when useful for comparing layout and regressions.

## Completion Criteria

A UI/UX task is complete only when:

* the primary task is clear
* visual hierarchy is intentional
* layout is responsive
* typography is readable
* spacing is consistent
* components follow the same design language
* loading, empty, error and success states exist
* keyboard navigation works
* focus states are visible
* color contrast is sufficient
* destructive actions are protected
* forms provide clear feedback
* important flows are tested
* lint, type checking and build pass
* remaining limitations are reported honestly

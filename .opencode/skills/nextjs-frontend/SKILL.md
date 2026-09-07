---

name: nextjs-frontend
description: Build, review and debug production Next.js, React, TypeScript and JavaScript applications using safe server-client boundaries, strong typing and reliable UI behavior.
license: MIT
compatibility: opencode
metadata:
  category: frontend
  stack: nextjs
  version: "1.0.0"
orchestration:
  lead_for:
    - nextjs-feature
  support_for:
    - bug-fix
    - code-review
  conflicts_with:
    - ui-ux-design
---

# Next.js Frontend

Use this skill whenever implementing, reviewing, debugging or refactoring a Next.js, React, TypeScript or JavaScript application.

The objective is to produce correct, accessible, maintainable and production-ready frontend behavior.

## Initial Inspection

Before changing code:

1. Read project-level `AGENTS.md`.
2. Inspect:

   * `package.json`
   * lockfile
   * `next.config.*`
   * `tsconfig.json`
   * ESLint configuration
   * Tailwind configuration
   * app or pages directory
3. Determine:

   * Next.js version
   * React version
   * package manager
   * App Router or Pages Router
   * state-management approach
   * API client pattern
   * authentication approach
4. Search for existing components and conventions.
5. Use current documentation when framework behavior is version-specific.

Do not assume APIs based on memory.

## Project Structure

Follow the existing repository structure.

Common areas:

```text
app/
pages/
components/
features/
lib/
services/
hooks/
types/
schemas/
styles/
public/
tests/
```

Do not create duplicate utility layers if an existing one already serves the purpose.

## Server and Client Components

Prefer Server Components by default in App Router projects.

Use Client Components only when the component requires:

* state
* effects
* event handlers
* browser APIs
* client-only libraries
* interactive context

Do not add `"use client"` unnecessarily.

Keep server-only code out of client bundles.

Never import into a Client Component:

* database clients
* private environment variables
* filesystem access
* server authentication helpers
* internal service credentials
* server-only SDKs

Use `server-only` guards where appropriate.

## Data Fetching

Use the project’s established data-fetching pattern.

For server-side fetching:

* verify authentication
* understand cache behavior
* use explicit revalidation when needed
* avoid caching user-specific data globally
* handle failures
* validate external responses
* avoid leaking private data through shared caches

For client-side fetching:

* show loading state
* show error state
* handle cancellation
* prevent stale requests from overwriting newer data
* avoid duplicate requests
* support retries only where useful
* clean up effects

Do not fetch the same data independently in multiple nested components without reason.

## Caching

Treat caching as a correctness concern.

Check:

* static versus dynamic rendering
* user-specific data
* tenant-specific data
* authentication state
* revalidation timing
* cache keys
* invalidation after mutation
* deployment behavior

Never allow private user data to be reused across users through shared caching.

Use current Next.js documentation for version-specific caching APIs.

## TypeScript

* Keep strict mode enabled when the project supports it.
* Avoid `any`.
* Avoid unsafe type assertions.
* Avoid unnecessary non-null assertions.
* Distinguish:

  * optional
  * nullable
  * missing
  * empty
* Use discriminated unions for stateful workflows.
* Validate runtime data.
* Keep frontend and backend contracts aligned.
* Prefer reusable domain types without coupling client code to server-only modules.

A TypeScript type does not validate API data at runtime.

## Runtime Validation

Validate untrusted data from:

* APIs
* local storage
* URL parameters
* search parameters
* forms
* third-party SDKs
* WebSockets
* server actions
* cookies

Use the project’s validation library if available.

Do not cast unverified data into trusted domain types.

## Components

Components should:

* have a clear responsibility
* use descriptive props
* avoid excessive prop drilling
* avoid large mixed-responsibility files
* preserve accessibility
* support loading and error states
* avoid hidden side effects

Split components when it improves ownership and readability, not merely because a file is long.

## State Management

Choose the smallest suitable state scope.

Use:

* local state for local interaction
* URL state for shareable filters and navigation
* server state tools for remote data
* context for stable cross-tree concerns
* global stores only for genuinely global client state

Avoid copying server data into local state unnecessarily.

Avoid storing derived values when they can be computed safely.

## Effects

Use effects only for synchronization with external systems.

Check for:

* missing dependencies
* unstable dependencies
* infinite loops
* stale closures
* missing cleanup
* repeated event registration
* duplicate requests
* race conditions
* timers not cleared
* subscriptions not removed

Do not use effects to compute values that can be derived during render.

## Forms

For every form:

* validate on the server
* provide useful client feedback
* disable or protect duplicate submission
* preserve entered values when errors occur
* show pending state
* map field errors correctly
* handle network failure
* prevent mass assignment
* verify authorization server-side

Do not trust hidden fields for:

* user ID
* role
* price
* branch
* permission
* ownership
* status

Server actions must validate all inputs again.

## Server Actions

Check:

* authentication
* authorization
* input validation
* origin or CSRF concerns where applicable
* cache invalidation
* redirect behavior
* duplicate execution
* database transaction safety
* error shape

Do not treat Server Actions as inherently secure.

## Route Handlers

Route handlers should:

* validate request input
* authenticate and authorize
* return consistent response shapes
* use correct status codes
* avoid exposing internal errors
* set cache headers intentionally
* enforce request-size limits
* protect expensive operations

Do not place secrets in responses or client-visible headers.

## Authentication

Check authentication across:

* middleware
* layouts
* pages
* route handlers
* server actions
* API requests
* client transitions

Do not rely only on hiding UI elements.

Every protected server operation must independently verify access.

## Environment Variables

Separate server-only and public values.

Only variables intentionally exposed to the browser may use:

```text
NEXT_PUBLIC_
```

Never expose:

* database credentials
* API secrets
* JWT secrets
* private tokens
* SMTP credentials
* cloud secrets

Validate required environment variables during startup or build.

## Error States

Every data-driven screen should deliberately handle:

* loading
* empty data
* failure
* unauthorized access
* not found
* success
* retry where appropriate

Do not leave users with blank screens or endless spinners.

Use:

* `error.tsx`
* `loading.tsx`
* `not-found.tsx`
* local error boundaries
* clear inline error messages

according to the project architecture.

## Accessibility

Check:

* semantic HTML
* keyboard navigation
* visible focus
* labels for inputs
* button names
* image alt text
* dialog focus management
* error announcements
* color contrast
* heading hierarchy
* table semantics
* form instructions

Do not use clickable `div` elements when a button or link is appropriate.

## Images and Media

* Use correct image sizing.
* Avoid layout shift.
* Configure remote image domains explicitly.
* Provide meaningful alt text.
* Use empty alt text only for decorative images.
* Do not expose private media through permanent public URLs.
* Handle broken images.
* Avoid loading oversized media unnecessarily.
* Validate uploaded media on the backend.

## Styling

Follow the existing styling system.

Prefer:

* reusable design tokens
* consistent spacing
* responsive layouts
* clear states
* accessible contrast

Avoid:

* arbitrary repeated values
* global CSS overrides for local problems
* overly specific selectors
* inline styles when the project uses a structured styling system
* unnecessary UI libraries

## API Integration

Check:

* base URL
* authentication headers
* timeout behavior
* error parsing
* response validation
* status handling
* retry behavior
* request cancellation
* duplicate requests
* token refresh
* logout behavior
* upload progress where needed

Do not assume every non-200 response has JSON.

## WebSockets and Streaming

Check:

* connection lifecycle
* authentication
* reconnection strategy
* duplicate listeners
* stale state
* message validation
* ordering
* buffering
* cleanup on unmount
* error state
* user logout
* tab visibility

Treat every incoming message as untrusted.

## Performance

Optimize based on evidence.

Check for:

* unnecessary client components
* oversized bundles
* repeated renders
* duplicate data fetching
* large dependencies
* unoptimized images
* expensive work during render
* long lists without virtualization where needed
* unnecessary context updates
* repeated parsing
* hydration mismatch
* blocking third-party scripts

Do not add memoization automatically.

Use profiling, bundle analysis or measured behavior.

## Security

Check:

* secret exposure
* authorization only in UI
* unsafe HTML
* open redirects
* untrusted URLs
* CSRF
* sensitive local storage
* cross-user caching
* server-only imports in client code
* unsafe iframe use
* unrestricted file access
* sensitive errors
* XSS through rendered content

Avoid `dangerouslySetInnerHTML` unless the content is sanitized and the need is justified.

## Testing

Add tests for:

* normal rendering
* loading
* empty state
* error state
* unauthorized state
* form validation
* duplicate submission
* API failure
* navigation
* responsive behavior
* keyboard interaction
* critical user flows
* regression scenarios

Use the project’s configured tools, such as:

* Vitest
* Jest
* React Testing Library
* Playwright
* Cypress

Prefer behavior-focused tests.

## Verification

Use the repository’s package manager.

Typical commands:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Or:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Run focused tests first.

Examples:

```bash
npm test -- assignment-form
```

```bash
npx playwright test tests/assignment-flow.spec.ts
```

Also verify:

* production build succeeds
* changed page renders
* API contract matches backend
* authentication still works
* loading and error states work
* browser console has no new errors
* responsive layout remains usable

## Completion Criteria

A Next.js task is complete only when:

* server and client boundaries are correct
* runtime data is validated
* authentication and authorization remain secure
* loading, empty and error states exist
* types are correct
* accessibility is preserved
* relevant tests pass
* lint and type checks pass
* production build succeeds
* remaining limitations are reported honestly

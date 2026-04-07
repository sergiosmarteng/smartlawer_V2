# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- `npm run dev` - Start development server
- `npm run build` - Build production bundle
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test` - Run tests

### Testing
- `npm run test:unit` - Run unit tests
- `npm run test:e2e` - Run end-to-end tests

## Architecture

### Project Structure
```
├── src/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   └── styles/
├── next.config.js
├── tsconfig.js
├── .env
└── .github/
    ├── ISSUE_TEMPLATE/
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

### Key Directories
- `src/components` - Reusable UI components
- `src/lib` - Utility functions and services
- `src/hooks` - Custom React hooks
- `src/types` - TypeScript type definitions

## GitHub Integration

All tasks must be created and tracked on GitHub using Issues and Projects.

### GitHub Setup
- Repository: `schinasergio/smartlawer_V2`
- Owner: `schinasergio`
- Token: Configured via `GITHUB_TOKEN` in `.env`

### Task Management
1. Create issues via GitHub interface for all features, bugs, and tasks
2. Use issue templates for consistency:
   - Feature Request
   - Bug Report
   - Enhancement
3. Assign issues to team members based on roles:
   - Orchestrator: Process flow management
   - Architecture: System design and documentation
   - Developers: Implementation and coding
   - QA: Testing and validation
   - Supervisor: Code quality control

### Workflow
- Issues → In Progress → Review → Done
- Use GitHub Projects board to visualize workflow
- Link commits to issues using references (e.g., "Fixes #123")
- Create pull requests for all changes
- Require approval before merging to main branch

## Environment Setup

### .env File
```
# SuperTokens Authentication
NEXT_PUBLIC_SUPERTOKENS_PUBLISHABLE_KEY=
SUPERTOKENS_SECRET_KEY=
SUPERTOKENS_API_DOMAIN=
SUPERTOKENS_APP_INFO={}

# SuperTokens Configuration (can be left as defaults if running locally)
SUPERTOKENS_CONNECTION_URI=http://localhost:3567
SUPERTOKENS_API_KEY=

# GitHub Integration (for MCP)
GITHUB_TOKEN=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
GITHUB_OWNER=schinasergio
GITHUB_REPO=smartlawer_V2
```

### Next.js Configuration
```js
// next.config.js
module.exports = {
  images: {
    domains: ['your-domain.com'],
  },
};
```

## Quick Start
1. Clone repository
2. Install dependencies: `npm install`
3. Create .env file with SuperTokens and GitHub credentials
4. Start development: `npm run dev`

## Notes
- Use `npm run lint` before committing
- All environment variables are stored in .env (ignored by Git)
- TypeScript configuration ensures type safety
- Next.js provides server-side rendering and static site generation
- All tasks must be tracked via GitHub Issues
- Pull requests must be reviewed before merging

---

This file was generated to help Claude Code understand the project structure and development workflow. It should be updated as the project evolves.

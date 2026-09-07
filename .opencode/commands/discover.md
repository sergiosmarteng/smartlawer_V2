---
description: Discover genuinely new capabilities or improvement opportunities for a repository, project, feature, or service without recommending existing or duplicate functionality
---

Use the `repo_map` custom tool to map the repository structure and identify relevant directories. Use `prompt_budget` to estimate context size of files that need inspection.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/repo_map.py [path]
- python tools/prompt_budget.py --dir <path>

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Workflow:

1. Determine the scope — full repository/project or a specific feature/service area.
2. Detect the repository type from actual files and configuration (when analyzing at repo level).
3. Build a compact inventory of existing features, components, patterns, and architecture relevant to the scope.
4. Compare items semantically, not only by filename or name.
5. Exclude:

   * existing features and patterns
   * planned work (from docs, tickets, comments)
   * aliases or alternative names for the same thing
   * simple renames of existing functionality
   * substantial duplicates
6. Identify genuine gaps and improvement opportunities relevant to the scope.
7. For each potential addition or improvement, verify:

   * why current code or implementation is insufficient
   * nearest existing feature or pattern
   * distinct value it would add
   * expected impact (quality, performance, maintainability, etc.)
   * implementation scope
8. Prefer extending an existing pattern when a separate addition is not justified.
9. Rank validated recommendations:

   * High priority
   * Medium priority
   * Experimental
10. List rejected duplicates explicitly.
11. Do not modify files.

Required output:

# Discovery

## Scope

Describe the scope of this analysis (repository, project, feature, or service).

## Current State Summary

## Confirmed Gaps

## Recommended New Capabilities or Improvements

For each recommendation:

* Name:
* Type (new capability / improvement):
* Why it is new or better:
* Nearest existing feature or component:
* Distinct value:
* Priority:

## Rejected Duplicates

## Recommended Roadmap

Do not recommend existing functionality as new.
Do not invent capabilities.
Keep the result proportional to the scope of the analysis.

$ARGUMENTS
# Phase 6 — UI/UX architecture

## Product experience

The platform should feel like a calm, observable software engineering workspace rather than a stream of AI chat messages. The primary question the interface answers is: **what is the engineering team doing, why is it doing it, and what needs my attention?**

## Information architecture

### 1. Projects
Entry surface for creating and reopening projects. The primary action is `New project`; recent projects show lifecycle status, last activity, and actionable failures.

### 2. Project workspace
The project workspace is the core application shell.

Desktop structure:
- top bar: project identity, lifecycle state, usage summary, pause/cancel controls
- left rail: Overview, Files, Agents, Tasks, Logs, Tests, Preview, Settings
- main workspace: selected tool/panel
- optional right inspector: selected task/agent/file/build details

Mobile structure:
- compact top bar
- bottom navigation for Overview, Files, Tasks, Preview, More
- full-screen drill-down sheets for agent/task/file details
- logs use a dedicated screen rather than a permanently visible console

## Overview

The overview prioritizes operational understanding:
1. current project phase and overall progress
2. active/waiting/failed agents
3. dependency-aware task pipeline
4. blockers requiring attention
5. recent meaningful events

Do not display raw hidden chain-of-thought. Agent detail surfaces may display task objective, concise decision summary, actions, files affected, tool results, errors, retries, duration, and provider usage when available.

## Agent pipeline

Each agent state has both text and iconography; color is supplemental only.

States: idle, queued, running, waiting, reviewing, testing, repairing, failed, completed, escalated.

A running agent card shows agent role, configured model label, current task, elapsed duration, and compact activity. Completed cards collapse by default. Failed/escalated cards rise above routine activity and expose the next action.

## Files

Use an IDE-style tree plus code viewer. On narrow screens, the tree and viewer become separate navigation levels. File operations must identify originating task/agent and project version. Destructive operations require explicit confirmation when user initiated.

## Tasks

Default task view is a dependency-aware list, not a decorative graph. A graph view can be optional on large screens. Each task exposes objective, owner agent, prerequisites, state, attempts, review requirement, affected paths, and failure summary.

## Logs

Logs are structured events, filterable by severity, agent, task, event type, and time. Secrets must already be redacted server-side; the UI is not a security boundary. Collapse repetitive low-value events.

## Tests

Show suites, pass/fail/skip counts, duration, associated build/version, and failure details. Never show a success state merely because tests were not run.

## Preview

Preview is visually separated from production. Show sandbox/build state and version. Failed builds replace the iframe with an actionable failure state. Mobile preview offers viewport presets without pretending to be physical-device testing.

## Settings

Sections: agents/models, project limits, execution policy, provider status, appearance/preferences. Secret values are write-only/masked; APIs must never return stored provider secrets.

## Project creation journey

1. User describes the product and names the project.
2. UI validates input locally for usability; server remains authoritative.
3. Project enters planning.
4. Planner and Architect activity appears immediately.
5. Architecture/task plan becomes inspectable.
6. Independent engineering tasks visibly fan out only after dependencies permit them.
7. Review/test/repair cycles are summarized as engineering events rather than raw model transcripts.
8. Completion requires integration/build/test evidence, not just agent completion.

## Required states

Every asynchronous surface must define:
- initial/empty
- loading/queued
- partial data
- success
- recoverable failure with retry
- non-recoverable/escalated failure
- disconnected/reconnecting for future realtime transport
- permission denied where ownership/authentication applies

## Accessibility

Target WCAG 2.2 AA. Requirements include keyboard navigation, visible focus, semantic landmarks/headings, labels for icon-only controls, minimum practical touch targets, non-color status indicators, reduced-motion support, readable code contrast, screen-reader announcements for important asynchronous status changes, and no forced auto-scroll in logs.

## Responsive behavior

- mobile: single primary pane, bottom navigation, drill-down details
- tablet: collapsible rail + primary pane; inspector overlays when needed
- laptop/desktop: persistent rail + primary pane + optional inspector
- very wide screens: constrain reading widths; do not stretch logs/code prose indefinitely

## Motion

Motion communicates state transitions and hierarchy. Use short restrained transitions for panel changes, progress updates, expanding details, and agent state changes. Avoid perpetual glow/pulse effects. Respect `prefers-reduced-motion`.

## Visual direction

Developer-focused dark and light themes with neutral surfaces, strong typography, restrained glass treatment only where layering benefits comprehension, subtle borders, and a small semantic status palette. Avoid excessive gradients, neon borders, and decorative animation.

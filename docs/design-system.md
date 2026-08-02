# Dashboard design system

This document defines implementation constraints for the future frontend. It intentionally avoids binding Phase 6 to a specific component library.

## Principles

1. Status before decoration.
2. Progressive disclosure over information dumping.
3. Consistent agent/task language across every screen.
4. Dense enough for developers, touch-friendly enough for mobile.
5. Accessibility is part of the component contract.

## Layout tokens

Use a 4px base spacing unit. Preferred spacing steps: 4, 8, 12, 16, 24, 32, 48, 64.

Suggested shell dimensions:
- desktop navigation rail: 224–256px
- inspector: 320–400px
- readable prose width: about 72 characters
- primary touch target: at least 44x44 CSS px where practical

## Typography roles

- display: rare project/empty-state headings
- heading: page and panel hierarchy
- body: normal interface text
- label: controls and metadata
- mono: code, paths, task IDs, structured logs, usage numbers where alignment matters

Do not use monospace for general body text.

## Semantic status model

Components consume semantic status names, never arbitrary per-screen colors:
- neutral: idle/inactive
- info: queued/planning
- active: running
- waiting: dependency/provider wait
- review: reviewing/testing
- warning: repairing/degraded
- danger: failed/escalated/security warning
- success: completed/passed

Every status presentation includes a textual label or accessible name.

## Core components

### AppShell
Responsive navigation + content + optional inspector. Must preserve selected project/tool across responsive transitions.

### ProjectPrompt
Project name, prompt field, validation, build action, optional advanced constraints. Do not place provider secrets here.

### StatusBadge
Semantic state, icon, readable label. Never color-only.

### AgentCard
Role, model display label, current task, status, duration, usage when available. Expand for decision/action/error summaries; never hidden chain-of-thought.

### TaskRow
Task ID, objective, agent, dependencies, state, attempts, review marker, affected-path count. Must support keyboard selection.

### EventFeed
Structured events with severity and filtering. Preserve user scroll position when new events arrive.

### FileTree / CodeViewer
Keyboard-accessible hierarchy and syntax-aware viewing. Mobile uses separate tree/viewer screens.

### TestSummary
Explicit passed/failed/skipped/not-run states. Failure details link to related task/build when available.

### PreviewFrame
Sandbox/version label, loading/build/failed/running states, viewport controls, explicit isolation indicator.

### Inspector
Contextual detail surface. Must not be the only location for critical errors/actions.

## Feedback patterns

- skeletons: only when shape is predictable
- spinner: short indeterminate action
- progress: use real progress only when meaningful; otherwise show phase/state
- toast: transient confirmation, never the sole home of failures
- inline error: nearest actionable location
- blocker banner: project-level problem requiring attention

## Empty-state language

Explain why the surface is empty and the next meaningful action. Avoid celebratory copy for states that simply have no data.

## Interaction rules

- primary action: one dominant action per local context
- destructive actions: explicit language and confirmation proportional to impact
- disabled controls: provide discoverable reason when non-obvious
- retry: preserve user input and completed work
- cancel/pause: distinguish stopping new scheduling from terminating active sandbox work

## Reduced motion

When reduced motion is requested, remove nonessential transforms and animated progress flourishes. State changes remain perceivable through text/icon updates.

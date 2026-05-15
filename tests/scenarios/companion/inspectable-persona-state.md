# companion.inspectable-persona-state

## Purpose

Verify the companion profile exposes its persona and continuity policy in inspectable form.

## Setup

- a profile manifest defines companion settings
- canonical identity state exists alongside the profile manifest
- the CLI can read the profile directory

## Steps

1. inspect the profile state from the CLI
2. inspect the relationship-memory policy hook
3. verify the mode is reported as text-first
4. verify the persona controls are visible in plain text

## Expected Assertions

- canonical identity state is loaded and shown
- the relationship-memory policy is visible
- the CLI does not hide persona state behind prompt text

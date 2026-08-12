# AURELIX Private Control Center

This directory contains the first browser interface for the AURELIX private Control Center.

## Security boundary

This is a UI shell only. It does **not** contain credentials, API keys, secrets, direct execution hooks, or authorization logic.

The production deployment must place it behind an authenticated HTTPS transport and the AURELIX Private API. Browser actions must remain narrow API operations and must continue through the Control Plane and Governor.

## Design language

The interface uses a green-first operational language:

- green = healthy / operational / active;
- gold = pending owner decision;
- no red error treatment as a normal dashboard state.

A failure can still be represented semantically, but the UI should avoid turning the dashboard into a wall of red indicators.

## Current status

The page is a static shell until the authenticated API adapter is implemented. Sample activity and pending decisions are explicitly mock display data and must be replaced by API responses before production use.

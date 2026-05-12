# Safe Real Functionality Design

## Goal

Turn the current MVP placeholders into safe, useful technician functionality without weakening the ActionEngine safety model or adding broad destructive behavior.

## Scope

This pass implements read-only Windows status checks, safer cleanup executors, reversible per-user registry tweaks, better report recommendations, and a stronger Debloat/Startup/Power foundation. It does not package the app to an exe, silently elevate, disable security features, remove protected Windows components, or perform automatic debloat.

## Safety Boundaries

- Every changing operation remains an Action with preview, confirmation, logging, and risk metadata.
- Cleanup only targets known cache/temp locations and refuses personal folders.
- Registry writes are limited to explicit HKCU safe rules, with JSON backup and .reg export where available.
- Debloat detection may read desktop registry uninstall keys and AppX package names, but removal is still manual/explicit.
- PowerShell commands use fixed strings or validated identifiers through PowerShellRunner.

## User Experience

The customer-facing flow stays simple. Advanced pages gain real controls where safe, but risky operations stay hidden behind technician/Expert gates. Reports become more useful by including snapshots and honest recommendations from scanner facts.

## Verification

The pass must add failing tests first for the new behavior, then implement until `pytest`, smoke startup, compileall, and a targeted security scan pass.

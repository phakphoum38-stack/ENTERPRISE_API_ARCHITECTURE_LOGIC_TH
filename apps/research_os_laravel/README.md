# Research OS Laravel Platform

Laravel 13 Platform component for Research OS.

This application is an integration/control-plane platform, not a replacement for the canonical Research OS Platform. It consumes canonical contracts through adapters and must not manufacture security decisions.

## Runtime baseline

- Laravel 13.x
- PHP 8.3+
- API version: v1

## Bounded modules

Core, Identity, Authorization, Workflow, Messaging, Tools, Evidence, Audit, Operations, Configuration, Versioning and Control.

## Architecture rule

HTTP/API -> Application -> Contracts/Domain -> Infrastructure adapters.

Security authority remains in the canonical Research OS Platform.

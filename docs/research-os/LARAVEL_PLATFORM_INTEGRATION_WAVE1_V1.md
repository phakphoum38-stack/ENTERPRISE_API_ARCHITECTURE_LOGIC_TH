# Laravel Platform Integration Wave 1

## Purpose

Wire Laravel to the canonical Research OS Platform without replacing or duplicating canonical capabilities.

## Adapter chain

`Client/API -> Laravel contract -> canonical adapter -> existing Research OS Platform`

The adapter carries:

- request ID
- correlation ID
- actor
- contract version
- idempotency key

## Integrated boundaries

- Identity
- Authorization
- Workflow
- Messaging
- Evidence
- Audit

Authorization remains fail-closed. Transport errors or malformed authorization responses resolve to `UNKNOWN`; Laravel never converts an unknown result into `ALLOWED`.

## Execution boundary

Workflow dispatch and messaging remain transport/adaptation only. Laravel does not directly invoke a runner. The canonical execution model remains:

`Engine -> Queue/Event -> Stateless Worker -> Evidence/Audit`

## Qualification

Adapter existence is not equivalent to production qualification. Endpoint compatibility, failure/recovery behavior, security authorization, and cross-surface E2E remain Final Gate concerns.

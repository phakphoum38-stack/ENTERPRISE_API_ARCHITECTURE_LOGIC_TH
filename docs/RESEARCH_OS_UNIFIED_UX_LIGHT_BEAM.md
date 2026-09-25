# Research OS Unified UX — Light Beam System

The Platform is the source of truth for the Research OS visual language. Windows,
Web, and iOS consume one UX contract rather than maintaining independent primary
palettes.

## Visual language

- Dark-first surfaces: deep navy/blue-black.
- Analogous palette: blue → cyan → indigo.
- Cyan is the primary interaction accent.
- Indigo is the secondary/intelligence accent.
- Green, amber, red, and blue are semantic state colors.
- Upward light beams are state/focus effects, not permanent decoration.

## State language

| State | Visual |
|---|---|
| IDLE | no beam |
| FOCUS | subtle glow |
| ACTIVE | upward beam |
| PROCESSING | animated upward beam |
| SUCCESS | success accent |
| WARNING | warning accent |
| ERROR | error accent |

## Surface rule

The same token names and semantic meanings apply to Windows, Web, and iOS.
Platform-specific implementation is allowed, but a surface must not redefine the
primary visual language.

## Legacy UX

Existing production UX is classified as ACTIVE, MIGRATE, DEPRECATED, or
COMPATIBILITY. Unknown UX is HOLD. New production surfaces must conform to the
contract; compatibility surfaces require explicit declaration.

## Accessibility

Beam/glow effects must remain subordinate to content and must not be the only
indicator of state. Semantic state must also be represented with text, iconography,
or other accessible information.

The contract is evidence-backed; visual regression does not itself become merge
authority.

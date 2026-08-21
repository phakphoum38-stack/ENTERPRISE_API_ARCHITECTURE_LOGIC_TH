# GUI Asset Manifest

`assets.json` is the deterministic registry for design assets that are intentionally handed off to Research OS UI implementation.

## Entry shape

```json
{
  "path": "design/icons/assistant.png",
  "type": "png",
  "role": "assistant-icon",
  "source": "ibispaint",
  "editable": false
}
```

## Rules

- `path` must point to a real repository file under `design/`.
- `type` must match the file extension and be one of the validator-supported formats.
- `role` describes the UI purpose, not the tool used to create it.
- `source` records the authoring tool when useful (`ibispaint`, `figma`, or `generated`).
- `editable` is `true` when the source should remain editable (for example layered PSD artwork).
- Do not add temporary files, caches, or machine-specific paths.

Keep the manifest empty until real design assets are added; never create placeholder binaries just to satisfy CI.

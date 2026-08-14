# Research OS — Owner Special / Friend Complete V1.3

Owner Special is a separate owner-only release line built on the certified V3 Clean core.

V1.3 adds a bounded **Turbo Helper Pool** with 1,000,000 logical helpers and a hard active-worker ceiling of 128, an OpenAI-compatible provider adapter with Windows DPAPI-protected credential storage, Provider Settings/Test Connection in the Owner Desktop, a Windows ServiceHost, and a one-click Setup.exe pipeline.

The million-helper value is a logical planning/routing capacity. The runtime does not spawn one million operating-system processes. It activates only the workers needed for the current batch, which keeps CPU/RAM bounded and makes large jobs faster and safer.

Owner data stays under `ProgramData\ResearchOSOwnerSpecial`, scoped by owner/profile/session. The installer and in-place upgrade preserve this data, and uninstall removes the program/service while preserving owner data.

Provider credentials are never included in source bundles, status responses, logs, or evidence. On installed Windows builds the service stores the credential as a DPAPI machine-protected blob. The source bundle contains owned orchestration, Brain/Skills/Memory/Tools/Provider adapters, Friend Service, Desktop source, ServiceHost, installer source, tests, and manifests; hosted model weights and private model internals are not embedded.

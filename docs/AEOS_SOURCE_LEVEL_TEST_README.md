# Source-Level Test Gate

AEOS treats `TEST` as a source-code verification operation.

The gate follows the real implementation path rather than trusting registry declarations. It requires a concrete source boundary and executable logic, and it records gaps instead of converting them to PASS.

Source-level verification covers the decision path, negative states, evidence/provenance binding, freshness, independence, and regression behavior.

# Software Factory Quick Start

```python
from pathlib import Path

from software_factory import AdaptiveControlPlane

plane = AdaptiveControlPlane(Path.cwd())
plan = plane.configure_versions(["v1", "v2", "v3"])

print(plan.profile.label)
print(plane.summary())
```

The control plane chooses the smallest supported logical power profile that can hold the requested version factories, while activating only the factories and orchestrator paths needed by the current workload.

Each active version receives one complete nine-role factory and an isolated workspace under `.factory_state/<version>`.

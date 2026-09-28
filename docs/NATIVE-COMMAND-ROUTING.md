# Native Command Routing

The Native Control Center now has a single bounded routing boundary between
prepared commands and the existing Research OS capability executors.

~~~text
USER / FRIEND
    ↓
CONTROL CENTER
    ↓
PREPARE COMMAND
    ↓
VALIDATE
    ↓
ROUTE
    ↓
EXISTING EXECUTOR
    ↓
OBSERVE
    ↓
EVIDENCE
~~~

The router deliberately stops short of execution authority. DRY_RUN,
SIMULATION, and REPLAY never execute. A LIVE mutation is also stopped at the
external human-authorization boundary.

The capability registry already identifies canonical UI, contract, runtime,
executor, observation, evidence, state, and inspector references. This slice
turns those references into one deterministic routing object without creating
another runtime, scheduler, queue, memory system, assurance engine, or
authority system.

Non-goals:

- no automatic merge or release
- no workflow dispatch
- no credential discovery
- no new executor
- no second command bus
- no history rewrite
- no automatic truth promotion

Unknown capability/executor state fails closed.

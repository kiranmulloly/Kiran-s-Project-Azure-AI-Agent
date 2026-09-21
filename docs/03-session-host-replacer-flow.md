# Flow: Session Host Replacer (Self-Healing)

**Goal:** Detect an unhealthy/unresponsive AVD session host and replace it
automatically, with zero manual intervention for the common case.

## Why this exists

Session hosts can go unhealthy for lots of reasons: failed agent heartbeat,
disk pressure, botched patch, stuck user session. Waiting for a human to
notice and manually rebuild the VM means degraded capacity for hours. This
flow closes that loop automatically.

## Steps

1. **Detect** — a health check (AVD agent status, heartbeat age, or a
   scheduled monitor) flags a session host as unhealthy.
2. **Drain** — the host is put into drain mode so no new user sessions land
   on it; existing sessions are allowed to complete or are force-logged-off
   per policy.
3. **Deregister** — the host is removed from the host pool registration and
   any load-balancing/scaling-plan association.
4. **Delete** — the underlying VM, NICs, and disks are deleted. (This step
   is guarded against a known class of bug: deleting VM extensions on a
   stopped/deallocated VM can return a 409 conflict — power state is checked
   first.)
5. **Re-provision** — the replacer triggers the same Terraform provisioning
   flow (see doc 02) to bring host count back to the desired state, tagged
   correctly so it's indistinguishable from a normally-provisioned host.
6. **Re-validate** — a smoke test confirms the new host registers
   successfully and accepts sessions before the run is marked complete.

## Guardrails learned the hard way

- **Never operate on a null/empty host list.** An empty or null array
  from the discovery step must short-circuit the run with a clear log
  message, not throw a downstream null-reference/index error.
- **Tag hygiene matters.** Hosts missing expected tags (region, persona,
  environment) are treated as "unknown" and excluded from automatic
  deletion — better to flag for human review than delete the wrong host.
- **One host at a time by default**, with an optional batch mode — avoids
  taking out an entire pool's capacity in one automation run.

## Generic example

See `sample-code/session-host-replacer/replace_session_host.py` for an
illustrative, non-proprietary implementation of this control loop.

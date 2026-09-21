# Flow: Session Host Replacer (Zero-Downtime Image Rollout + Self-Healing)

**Goal:** Two related but distinct triggers, one control loop:

1. **Unhealthy host detected** -> replace that one host, immediately, 1:1.
2. **A new golden image version is published** -> roll the *entire* host
   pool onto the new image, in batches, **without dropping capacity or
   forcing mid-session logoffs at any point during the rollout.**

Trigger #2 is the interesting one, and the reason this exists as custom
automation at all: Azure's own AVD control plane does not offer a built-in
"roll out a new image across this host pool with zero downtime" operation.
Some dedicated third-party DaaS/VDI management platforms sell this as a
premium feature. I didn't have access to one of those, so I built the
capability myself.

## Why this exists

Session hosts get rebuilt from a versioned "golden image" (an Azure Compute
Gallery image definition/version) that bakes in OS patches, the AVD agent,
and baseline software. Every time a new image version ships, every host in
every affected pool is technically out of date until it's rebuilt from that
version. The two bad options without this automation:

- **Manual, host-by-host rebuild** -- slow, error-prone, and someone has to
  babysit session counts to avoid kicking active users off a host being
  replaced.
- **Recreate the whole pool at once** -- fast, but drops capacity to zero
  (or near-zero) for the rollout window, which is a real user-facing outage
  for a "routine" image update.

The replacer automates a **create-before-delete, capacity-preserving
rolling upgrade** instead -- the same pattern you'd use for a zero-downtime
deploy of a stateless web fleet, applied to VDI session hosts.

## Steps -- image-drift rolling replacement (the zero-downtime path)

1. **Detect drift** -- for each host pool, compare the `image_version` tag
   baked onto each existing session host against the latest published
   version in the Compute Gallery. Hosts on an older version are the
   replacement candidates.
2. **Provision a new batch first** -- create N new session hosts (N = batch
   size, typically 1-2 per pool) from the *new* image version via the same
   Terraform flow used for normal provisioning (see doc 02). Pool capacity
   goes up before anything is removed.
3. **Wait for health + registration** -- new hosts must register with the
   host pool, pass an agent-heartbeat check, and be out of drain mode
   before they count as "ready."
4. **Drain one old-version host at a time** -- stop assigning new sessions
   to it; existing sessions are allowed to finish naturally (or are handled
   per the pool's session-logoff policy during an announced maintenance
   window -- this automation does not silently force-logoff users).
5. **Deregister + delete the old host** -- once drained, remove it from the
   pool and delete the underlying VM/NIC/disks.
6. **Repeat batch by batch** until every host in the pool is on the new
   image version, always keeping total *ready* capacity at or above the
   pool's configured minimum throughout the whole rollout.
7. **Re-validate** -- a smoke test confirms new hosts accept sessions
   correctly before the rollout is marked complete.

## Steps -- unhealthy-host replacement (the fast path)

Unchanged from a simple health-check loop: detect an unhealthy host, drain,
deregister, delete, re-provision one replacement from the pool's *current*
image version, validate. This path is 1:1 and immediate -- it doesn't wait
for a batch window because an unhealthy host is already not serving
capacity, so there's no "downtime to avoid" the way there is with a
planned image rollout.

## Guardrails learned the hard way

- **Never drop below minimum ready capacity.** The rolling upgrade
  explicitly checks `ready_host_count >= pool_minimum` before draining the
  next old-version host -- if a new host fails to come up healthy, the
  rollout pauses rather than pressing on and starving the pool.
- **Never operate on a null/empty host list.** An empty or null array from
  the discovery step must short-circuit the run with a clear log message,
  not throw a downstream null-reference/index error.
- **Tag hygiene matters.** Hosts missing expected tags (region, persona,
  environment, image_version) are treated as "unknown" and excluded from
  automatic deletion -- better to flag for human review than delete or
  misclassify the wrong host.
- **Power-state check before touching extensions.** Deleting VM extensions
  on a stopped/deallocated VM returns a 409 conflict; power state is
  checked first.
- **Batch size is configurable per pool**, defaulting small (1-2 hosts) --
  avoids taking out a meaningful chunk of a pool's capacity in one
  automation cycle even during a "safe" rolling upgrade.

## Generic example

See `sample-code/session-host-replacer/replace_session_host.py` for an
illustrative, non-proprietary implementation of both control loops
described above.

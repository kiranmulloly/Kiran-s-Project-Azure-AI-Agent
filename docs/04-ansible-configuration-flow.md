# Flow: Ansible Configuration Management

**Goal:** Apply consistent OS-level configuration and software installs across
session hosts, on a schedule or on-demand, without hand-touching VMs.

## Steps

1. **Author a playbook** using a shared wrapper/template pattern so every
   playbook automatically supports:
   - Targeting a single host pool or all host pools for a persona
   - An optional "single host" mode for testing before a fleet-wide rollout
   - Idempotent host-pool power management (start hosts before configuring,
     restore prior power state after) — gated by a boolean flag so it can be
     skipped for single-run/manual invocations
2. **Register the playbook** in an explicit allow-list consumed by the
   pipeline's interactive trigger form — this is a deliberate safety choice:
   arbitrary playbooks can't be run against production fleets; only
   reviewed, merged, allow-listed playbooks show up as selectable options.
3. **Push to source control** (feature branch → review → merge to the
   environment branch).
4. **Refresh automation cache** so the pipeline picks up the new/changed
   playbook and allow-list entry.
5. **Trigger via pipeline** — an operator selects environment, persona,
   host pool, and playbook from a form; the pipeline runs Ansible against
   the target inventory and reports pass/fail per host.

## Common failure modes handled

- **Missing `default` filters on optional facts** — a task referencing
  `result.stdout` when `result` might be an empty dict on an unreachable
  host causes a crash; playbooks defensively use `| default('')` and
  explicit `when: result is defined` guards.
- **Power-state assumptions** — tasks that require a running VM check/
  set power state explicitly rather than assuming hosts are already on.

## Generic example

See `sample-code/ansible/playbook-example.yml` for an illustrative,
non-proprietary playbook using the wrapper pattern described above, and
`sample-code/ansible/hostpool_wrapper.yml` for the wrapper itself.

## Why the wrapper disables/re-enables the scaling plan

This is worth calling out on its own because it's the single most common
cause of a "config didn't stick" ticket if you skip it.

AVD scaling plans ramp session hosts up and down on a schedule or based on
active-session thresholds, completely independent of whatever Ansible run
might be in flight. If the scaling plan deallocates -- or force-logs-off and
drains -- a host in the middle of a configuration run:

- The install/config task gets killed mid-way, leaving the host in a
  half-applied state that's worse than not having run at all.
- Ansible reports a hard connection failure (WinRM/SSH drop), which looks
  identical to a real infrastructure problem -- wasting triage time.
- If the scaling plan's own schedule brings the host back up shortly after,
  it can restart with the OLD configuration still active, silently masking
  a failed run until a user reports something's wrong days later.

The wrapper's fix is simple: disable the scaling plan for just the target
host pool right before the run starts, and re-enable it right after --
scoped narrowly enough that every other pool keeps autoscaling normally the
whole time. It's a small amount of extra orchestration for a whole class of
intermittent, hard-to-reproduce failures eliminated.

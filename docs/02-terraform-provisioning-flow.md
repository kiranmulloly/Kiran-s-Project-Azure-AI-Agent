# Flow: Terraform Provisioning

**Goal:** Stand up (or resize) an AVD host pool and its supporting Azure
resources in a repeatable, reviewable way.

## Steps

1. **Author/modify persona config** — engineer edits a `.tfvars`-style config
   for the target persona (e.g. session host count, VM SKU, region).
2. **Feature branch + plan** — change is pushed to a feature branch; the
   pipeline runs `terraform plan` and posts the diff for human review.
3. **Pilot validation** — the same change is applied to a shared pilot
   environment first, so the "baseline" every future diff is compared
   against never goes stale.
4. **Approval gate** — a human reviews the plan output (resource adds/
   changes/destroys) before anyone can click apply. Destructive changes
   (especially `destroy` on session hosts or networking) get extra scrutiny.
5. **Apply** — Terraform provisions/updates:
   - Resource group / networking (or references to shared networking)
   - Host pool + workspace + application group
   - Session host VMs (scale set or individual VMs, depending on persona)
   - Scaling plan attachment
6. **Promote to production** — once validated in pilot, the identical change
   is merged to the production branch and re-applied through the same
   plan → approve → apply sequence against the prod environment.

## Common failure modes handled

- **Orphaned state lock** after a cancelled/timed-out apply → documented
  force-unlock + state reconciliation procedure.
- **Subnet exhaustion** during scale-out → pre-flight IP capacity check.
- **Invalid resource naming** (e.g. application name length limits) →
  validation rules enforced at the `tfvars` layer before plan even runs.

## Generic example

See `sample-code/terraform/` for an illustrative (non-proprietary) module
skeleton showing the host-pool + session-host pattern, and
`docs/07-terraform-module-repo-pattern.md` for how the actual resource
logic is published from a separate, versioned module repository rather
than copy-pasted into every persona's deployment repo.

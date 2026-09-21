# Architecture Overview

## Problem statement

As the hands-on engineer responsible for a large Azure Virtual Desktop (AVD)
footprint -- **2 regions, 50 host pools, 500+ applications** -- I needed a way
to provision, configure, and operate all of it without hand-touching VMs one
at a time. The requirements I coded against:
- **Consistency**: every environment provisioned the same way, no snowflakes.
- **Safety**: no infrastructure change applies without a reviewed plan.
- **Resilience**: unhealthy session hosts are detected and replaced automatically.
- **Extensibility**: onboarding a new persona/business unit is a config change,
  not a bespoke engineering project.

## Design pattern: the "Persona" abstraction I built

Each of the 50 host pools is modeled as a **persona**: a named configuration
bundle I authored containing host pool size, VM SKU, region, application list,
and scaling schedule. Personas are declared in a single structured config file
and consumed by both the Terraform modules and the Ansible playbooks I wrote.
Adding persona #51 means adding one config block, not writing new automation --
that was the whole point.

## Components

| Layer | Technology | Responsibility |
|---|---|---|
| Infra provisioning | Terraform | Host pools, VM scale sets/session hosts, networking, scaling plans |
| Configuration management | Ansible | OS-level config, application installs, registry/policy changes |
| Pipeline orchestration | CI/CD orchestrator (plan/approve/apply model) | Sequencing, human approval gates, environment promotion (dev → pilot → prod) |
| Self-healing | Custom automation (PowerShell/Python) | Detect unhealthy hosts, drain, deregister, delete, trigger re-provision |
| Observability | Dashboards + log aggregation | Utilization-based rightsizing, deployment health, cost trends |

## Environment promotion model

Changes flow through three environments before reaching production:

1. **Dev/feature branch** — engineer validates a change in isolation.
2. **Pilot** — shared pre-prod environment; acts as the "known good" baseline
   that every feature branch is diffed against before merge (this caught a
   whole class of bugs where a stale pre-prod baseline silently diverged
   from what was actually live).
3. **Production** — promoted only after pilot validation + human approval gate.

## Key operational lessons baked into the design

- **State locks must be force-recoverable.** Interrupted applies (timeouts,
  SIGTERM) can orphan a Terraform state lock; the pipeline includes a
  documented unlock-and-reconcile runbook rather than leaving engineers to
  hand-edit state.
- **Subnet capacity is a first-class scaling constraint.** Rapid scale-out
  can exhaust available IPs in a subnet faster than anyone expects; capacity
  checks are part of pre-flight validation, not an afterthought discovered
  during an incident.
- **VM extensions fail loudly on stopped/deallocated VMs.** Any automation
  that touches VM extensions (config, diagnostics, etc.) checks power state
  first to avoid spurious 409 conflicts.
- **"No session hosts registered" is a common day-1 failure**, usually caused
  by a missing prerequisite step (host pool registration token, scaling plan
  attachment) rather than a code bug — the onboarding runbook front-loads
  those prerequisite checks.

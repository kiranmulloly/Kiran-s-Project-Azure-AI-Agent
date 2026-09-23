# Resume / LinkedIn "Experience" Bullet Points

Pick and adapt the ones that best match the role you're applying for. Keep
company-specific names out of your resume unless your employer explicitly
permits it -- describe scope generically (e.g. "large enterprise VDI
environment spanning 2 regions") rather than naming internal systems.

Scope for reference: **2 Azure regions, 50 host pools, 500+ applications**.

## Infrastructure as Code / Terraform
- Wrote and maintained Terraform modules provisioning a multi-tenant Azure
  Virtual Desktop platform across 2 regions and 50 host pools, using a
  plan/approve/apply pipeline to eliminate un-reviewed production changes.
- Built a persona-driven configuration pattern that reduced onboarding a new
  host pool from a multi-day engineering effort to a single config change.
- Personally diagnosed and resolved recurring Terraform state-lock and
  subnet-capacity failures, writing runbooks that cut incident resolution
  time significantly.

## Automation / Self-Healing Infrastructure
- Coded a zero-downtime, image-drift-triggered rolling session-host
  replacer across 50 host pools: create-before-delete batching rolls a new
  golden image across a pool with no capacity dip and no forced logoffs --
  a capability not natively offered by Azure's own AVD control plane.
- Built a separate fast-path replacement loop for unhealthy hosts
  (detect -> drain -> deregister -> delete -> re-provision), with safety
  guardrails (tag validation, power-state checks) preventing destructive
  action on ambiguous or partially-configured resources.

## Configuration Management / Ansible
- Authored a reusable Ansible playbook framework (wrapper/template pattern)
  delivering and maintaining 500+ applications across the fleet, supporting
  both single-host testing and fleet-wide rollout.
- Introduced a playbook allow-list model integrated into the deployment
  pipeline, restricting production automation runs to reviewed, merged
  playbooks only -- improving change-control posture.

## CI/CD & Pipeline Orchestration
- Built and operated a CI/CD pipeline orchestrating infrastructure
  (Terraform) and configuration (Ansible) changes through a consistent
  plan -> approve -> apply -> validate flow across dev, pilot, and
  production environments.
- Designed and implemented interactive, form-driven pipeline triggers
  (environment / persona / host pool / playbook selection) to reduce
  operator error on high-blast-radius operations.

## AI-Driven Deployment Orchestration
- Built an AI agent that sits in front of the CI/CD pipeline, turning a
  plain-language or ticket-based request into a planned, human-approved,
  monitored deployment -- with tool-calling scoped so destructive actions
  are unreachable without an explicit approval step.
- Wired the agent to a knowledge base of past incidents so failed runs get
  an automatic root-cause suggestion instead of a blank error message.
- Built the web-serving platform around the agent itself -- boot lifecycle,
  session/process management (cold-start vs. warm reuse), and a two-tier
  knowledge-retrieval strategy (a lightweight static summary baked in at
  boot, plus semantic vector search invoked on-demand mid-conversation).

## Troubleshooting / Operations
- Acted as the hands-on escalation point for production VDI incidents
  across 2 regions and 50 host pools, root-causing issues spanning
  Terraform state management, Azure VM extension lifecycle, network
  capacity, and scaling-plan misconfiguration.
- Wrote internal documentation/runbooks turning one-off incident fixes into
  repeatable, self-service troubleshooting guides.

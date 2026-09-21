# LinkedIn Post — Long / Article Version

---

## Building a self-healing Azure Virtual Desktop automation platform

Over the past couple of years, one of the most hands-on problems I've worked
on has been building and operating a large, multi-tenant Azure Virtual Desktop
(AVD) footprint: **2 Azure regions, 50 host pools, and 500+ applications**,
all running on automation I wrote and maintained myself.

I recently put together a generic portfolio write-up of the architecture
(no proprietary code or company details — just the patterns), and wanted to
share the highlights here.

**The core problem:** VDI at scale has a handful of recurring failure modes I
hit and fixed myself -- session hosts silently going unhealthy, Terraform
state locks getting orphaned by interrupted runs, subnets running out of IPs
during bursty scale-out, and onboarding a new host pool taking real
engineering time instead of being a config change.

**What I built and wrote, hands-on:**

1. **Provisioning (Terraform)** — every environment is declared as code, run
   through a strict plan → human-approval → apply sequence, and promoted
   through dev → pilot → production so the pilot baseline never silently
   drifts from what's actually live.

2. **Configuration (Ansible)** — a wrapper-playbook pattern handles
   fleet-wide software installs and OS config, with an explicit allow-list
   so only reviewed playbooks are ever selectable for a production run —
   no ad-hoc scripts against live fleets.

3. **Self-healing (custom automation)** — a control loop continuously
   watches for unhealthy session hosts and automatically drains,
   deregisters, deletes, and triggers re-provisioning — with guardrails
   like "never auto-delete a host missing expected tags" and "check power
   state before touching VM extensions to avoid spurious 409 conflicts."

4. **Orchestration (CI/CD pipeline)** — every change, whether infra or
   config, goes through the same reviewable pipeline. Interactive trigger
   forms (pick environment / persona / host pool / playbook from validated
   dropdowns) cut down on the classic "ran it against the wrong
   environment" mistake.

**What I learned building it:**
- Idempotency and defensive defaults (`| default('')`, explicit empty-list
  returns instead of `null`) prevent an entire category of 2am pages.
- A true approval gate before `apply` is worth the friction, every time.
- Multi-tenancy only scales if onboarding a new tenant is a config change,
  not a new engineering effort.

Full architecture write-up, diagrams, and generic sample code (Terraform,
Ansible, and the self-healing control loop) are in the repo — link in the
comments.

Happy to go deeper with anyone building similar VDI/EUC, IaC, or
self-healing infrastructure platforms.

#Azure #AVD #VirtualDesktop #Terraform #Ansible #CloudEngineering #DevOps
#InfrastructureAsCode #PlatformEngineering #SRE #CareerGrowth

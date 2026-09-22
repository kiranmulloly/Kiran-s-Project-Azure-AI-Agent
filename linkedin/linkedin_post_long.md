# LinkedIn Post — Long / Article Version

---

## Building a self-healing, zero-downtime Azure Virtual Desktop automation platform

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

2. **Configuration (Ansible)** -- a wrapper-playbook pattern handles
   fleet-wide software installs and OS config, with an explicit allow-list
   so only reviewed playbooks are ever selectable for a production run --
   no ad-hoc scripts against live fleets. The wrapper also disables each
   target host pool's scaling plan for the run and re-enables it right
   after -- otherwise autoscale can deallocate a host mid-install and
   either hard-fail the run or silently bring the host back up with the
   OLD config still in place.

3. **Zero-downtime image rollout + self-healing (custom automation)** -- a
   control loop with two triggers: an unhealthy host gets replaced
   immediately, 1:1; a new golden image version gets rolled across the
   *entire* pool in batches using create-before-delete sequencing, so
   capacity never dips and no one gets force-logged-off mid-session.
   Azure's own AVD control plane doesn't offer that as a built-in
   operation -- I built it from scratch.

4. **Orchestration (CI/CD pipeline)** -- every change, whether infra or
   config, goes through the same reviewable pipeline. Interactive trigger
   forms (pick environment / persona / host pool / playbook from validated
   dropdowns) cut down on the classic "ran it against the wrong
   environment" mistake.

5. **AI deployment agent** -- sits in front of the pipeline so a
   plain-language or ticket-based request gets planned, gated on human
   approval, deployed, monitored, and reported on automatically -- without
   loosening any of the approval-gate guardrails above.

**What I learned building it:**
- Idempotency and defensive defaults (`| default('')`, explicit empty-list
  returns instead of `null`) prevent an entire category of 2am pages.
- A true approval gate before `apply` is worth the friction, every time --
  including when an AI agent is the one asking for it.
- Create-before-delete beats delete-then-create for anything user-facing;
  the few extra minutes of overlap capacity is cheap compared to an outage.
- Multi-tenancy only scales if onboarding a new tenant is a config change,
  not a new engineering effort.

Full architecture write-up, diagrams, and generic sample code (Terraform,
Ansible, the rolling-replacer control loop, and the AI agent skeleton) are
in the repo -- link in the comments.

One thing I want to be direct about: the zero-downtime rolling session-host
replacer is not a Microsoft feature, and it wasn't adapted from a
Microsoft reference architecture -- Azure's AVD control plane doesn't offer
that as a built-in capability. I designed and built it from scratch, and it
was reviewed by a Microsoft AVD architect who called it out as going
beyond what Azure natively provides.

Happy to go deeper with anyone building similar VDI/EUC, IaC, self-healing
infrastructure, or AI-driven ops platforms.

#Azure #AVD #VirtualDesktop #Terraform #Ansible #CloudEngineering #DevOps
#InfrastructureAsCode #PlatformEngineering #SRE #AIAgents #CareerGrowth

# LinkedIn Post — Short Version

---

Just published a portfolio project showcasing hands-on work I've done building
and operating **large-scale Azure Virtual Desktop (AVD) automation** --
spanning **2 Azure regions, 50 host pools, and 500+ applications**.

I personally wrote and operate:

- **Terraform** for repeatable, reviewed infrastructure provisioning
- **Ansible** for fleet-wide configuration management, wrapped so scaling
  plans get safely disabled/re-enabled around every maintenance run
- A **zero-downtime, image-drift-triggered rolling session-host replacer**
  I built from scratch -- rolls a new golden image across a host pool with
  create-before-delete batching, no capacity dip, no forced logoffs
- An **AI agent** I built that sits in front of the pipeline: plans a
  change, gates on human approval, triggers the deploy, monitors it, and
  reports back
- A **CI/CD pipeline pattern** (plan -> approve -> apply) so no infra change
  ever touches production without a human-reviewed diff

I wrote up the architecture, the code patterns, and some of the gnarlier
production bugs I personally debugged (state-lock recovery, subnet exhaustion,
VM extension conflicts on stopped VMs) as a generic reference project -- link
in comments.

If you're working on VDI/EUC automation, Terraform-based infra platforms, or
self-healing systems in general, I'd love to compare notes.

#Azure #AVD #Terraform #Ansible #DevOps #InfrastructureAsCode #CloudEngineering #IaC #SRE

---
*(Post the GitHub repo link as the first comment — LinkedIn's algorithm
generally favors posts without an outbound link in the body.)*

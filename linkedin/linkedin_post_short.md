# LinkedIn Post — Short Version

---

Just published a portfolio project showcasing hands-on work I've done building
and operating **large-scale Azure Virtual Desktop (AVD) automation** --
spanning **2 Azure regions, 50 host pools, and 500+ applications**.

I personally wrote and operate:

- **Terraform** for repeatable, reviewed infrastructure provisioning
- **Ansible** for fleet-wide configuration management
- A **self-healing session-host replacer** that detects unhealthy hosts and
  automatically drains, deregisters, deletes, and re-provisions them
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

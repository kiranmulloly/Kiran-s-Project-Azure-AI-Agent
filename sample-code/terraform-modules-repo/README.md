# terraform-avd-modules (illustrative)

This folder simulates a **separate git repository** dedicated solely to
reusable Terraform modules for the AVD platform -- in a real setup this
would live at its own remote (e.g. `terraform-avd-modules`), with its own
commit history, its own PR review process, and its own release tags,
completely independent from any single deployment/persona repo.

## Why modules live in their own repo instead of being copy-pasted

With 50 host pools across 2 regions, every one of them needs the same
host-pool + session-host resource shapes. Two ways to handle that:

1. **Copy-paste the `.tf` files into every persona's config repo.** Works
   until you need to fix a bug or add a feature -- now you're hunting down
   50 copies, most of which have quietly drifted from each other.
2. **Publish the shared logic as versioned modules in their own repo**,
   and have every deployment repo pull a *pinned* version of it. A fix
   ships once, and each environment adopts it on its own schedule by
   bumping its own `ref`.

This project uses option 2.

## Versioning strategy

Releases are tagged with semver (`v1.0.0`, `v1.4.0`, ...). A deployment
repo pins an exact tag:

```hcl
module "host_pool" {
  source = "git::https://github.com/example-org/terraform-avd-modules.git//modules/host-pool?ref=v1.4.0"
  # ...
}
```

- **Patch/minor bumps** (bug fixes, new optional variables) are safe for
  any deployment repo to adopt whenever convenient.
- **Major bumps** (breaking variable changes) require an explicit,
  reviewed change in the *consuming* deployment repo's `ref` -- nothing
  ever auto-upgrades underneath a live environment.
- Pilot environments typically track a newer tag than production, so a
  module change gets soak time in pilot before any production repo bumps
  its own `ref` to match.

## Layout

```
terraform-avd-modules/            <- this simulated repo
├── modules/
│   ├── host-pool/                <- host pool, workspace, application group
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── session-hosts/            <- NICs, VMs, DSC registration extension
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── README.md                     <- you are here
```

An alternative to git-sourced modules worth knowing about: a **private
Terraform module registry** (Terraform Cloud/Enterprise, or a self-hosted
equivalent) gives you the same "publish once, consume by version" model
with a cleaner `source = "app.terraform.io/example-org/host-pool/azurerm"`
syntax instead of a git URL + `ref`. Git-sourced modules were the simpler
starting point here and worked fine at this scale.

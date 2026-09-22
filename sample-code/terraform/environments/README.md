# Environments -- nested tfvars layout

```
environments/
├── pilot/
│   └── example-persona.tfvars
└── prod/
    └── example-persona.tfvars
```

## Why nested by environment, then by persona

- **One file per persona per environment.** In the real platform this
  folder holds 50 files under `prod/` (one per persona) and a matching 50
  under `pilot/` -- each named after its persona (`<persona_name>.tfvars`).
  This portfolio includes one representative example in each.
- **The pipeline trigger form (see docs/05) picks the file, not a human
  typing a path.** An operator selects environment + persona from
  dropdowns; the pipeline resolves that to
  `environments/<environment>/<persona_name>.tfvars` and passes it to
  `terraform plan -var-file=...`. There's no way to fat-finger a path and
  accidentally apply persona A's sizing against persona B's resources.
- **Pilot is not a toy sandbox.** As covered in docs/01, every production
  change is validated against the exact same `.tfvars` shape in `pilot/`
  first -- notice the two example files below intentionally mirror each
  other's variable set, differing only in the values (smaller session host
  count, shorter/looser scaling schedule, non-prod resource IDs in pilot).
- **Secrets are never in these files**, in either environment -- `admin_username`,
  `admin_password`, and `registration_token` are injected at apply-time
  from a secrets store / pipeline secret variables, even in pilot.

Almost every non-secret variable defined in `../variables.tf` is set
explicitly in both example files below (rather than relying on defaults),
so a reviewer can see the full effective configuration for a persona in
one place without cross-referencing module defaults.

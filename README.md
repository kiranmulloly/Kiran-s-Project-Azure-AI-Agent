# Enterprise VDI Automation Platform (Portfolio Showcase)

> **Note:** This repository is a *generic, from-scratch recreation* of the architecture
> and automation patterns I designed and operated for a large-scale enterprise
> Azure Virtual Desktop (AVD) environment. All code here is illustrative/synthetic —
> written to demonstrate the design, not copied from any employer's proprietary
> codebase. No company names, hostnames, credentials, or internal identifiers are
> included.

## What this project demonstrates

I built and operated the automation backbone for a multi-tenant Azure Virtual
Desktop platform spanning **2 Azure regions**, running **50 host pools**
("personas") and delivering **500+ applications** to end users. I wrote the
Terraform, the Ansible playbooks, the self-healing automation, and the pipeline
glue myself, and was the hands-on engineer for the full lifecycle:
**provision → configure → validate → heal → scale**.

**Hands-on work demonstrated here:**
- Wrote Terraform modules for repeatable, auditable Azure provisioning across
  2 regions and 50 host pools, published from a separate, versioned module
  repo and consumed by every persona's thin deployment repo via a pinned ref
- Authored Ansible playbooks delivering and maintaining 500+ applications
  across the fleet, wrapped in a reusable host-pool wrapper pattern
- Built a zero-downtime, image-drift-triggered rolling session-host
  replacer from scratch (a capability not natively offered by Azure's own
  AVD control plane)
- Wired up CI/CD pipeline stages for infra changes (plan → approve → apply)
- Built an AI agent that sits in front of the pipeline to plan, gate, and
  monitor deployment requests end-to-end
- Built the web-serving platform around that agent: boot lifecycle, session/
  process management, and a two-tier (static + dynamic) knowledge-retrieval
  strategy
- Implemented the multi-tenant "persona" config pattern used to onboard new
  business units without new engineering work
- Debugged and fixed production issues: state locks, IP/subnet exhaustion, VM
  extension conflicts, scaling-plan misconfiguration

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Source["Source Control"]
        A[Infra-as-Code Repo\nTerraform + Ansible + Pipeline Configs]
    end

    subgraph Pipeline["CI/CD Orchestrator"]
        B1[Plan Stage\nterraform plan]
        B2[Approval Gate\nhuman review]
        B3[Apply Stage\nterraform apply]
        B4[Config Stage\nAnsible playbook run]
        B5[Validation Stage\nsmoke tests]
    end

    subgraph Azure["Azure Environment"]
        C1[Host Pool - Persona A]
        C2[Host Pool - Persona B]
        C3[Host Pool - Persona N]
        D[Scaling Plan]
        E[Session Hosts / VMs]
    end

    subgraph Healing["Self-Healing Layer"]
        F1[Health Monitor]
        F2[Session Host Replacer]
    end

    A --> B1 --> B2 --> B3 --> B4 --> B5
    B3 --> C1
    B3 --> C2
    B3 --> C3
    C1 --> E
    C2 --> E
    C3 --> E
    D --> E
    F1 -->|detects unhealthy host| F2
    F2 -->|drain, deregister, delete| E
    F2 -->|re-provision via Terraform| B3
```

## AI Agent Platform

The automation above doesn't just run on its own -- I also built the AI
agent that sits in front of it: a browser-based chat agent that operators
use to request, approve, monitor, and troubleshoot deployments in plain
language, backed by a retrieval-augmented knowledge base of past
incidents and runbooks. This is the part of the project I'd point to as
most aligned with where infrastructure engineering is heading -- agentic,
tool-calling AI wired directly into the operational systems it manages,
not just a chatbot bolted on the side.

```mermaid
flowchart TD
    A[Container starts] --> B[Sync source + knowledge store\nvector index + relational fallback]
    B --> C[Bake a static knowledge summary\ninto the agent's system prompt]
    C --> D[Web server ready]

    D --> E[Browser: login + chat message]
    E --> F{Agent session\nalready warm?}
    F -- No --> G[Cold start: spawn agent process,\nrun warmup handshake]
    F -- Yes --> H[Reuse existing warm process]
    G --> I
    H --> I[Agent reasoning loop begins]

    I --> J{Needs more context\nthan static summary?}
    J -- Yes --> K[On-demand semantic search\nvector store, primary]
    J -- Yes --> L[Keyword search over docs\nfallback]
    J -- No --> M[Answer directly]
    K --> M
    L --> M

    M --> N{Deployment action\nrequested?}
    N -- Yes --> O[Tool-calling flow: plan -> human\napproval gate -> trigger -> monitor]
    N -- No --> P[Respond in chat]
    O --> P
    P --> Q[Structured JSON response\nrendered in the browser]
```

Two design decisions worth calling out, both covered in depth in
`docs/06` and `docs/08`:

- **Static vs. dynamic knowledge, kept deliberately separate.** A cheap
  summary is baked into the agent's config once at boot so it always has
  baseline context; deeper, semantic retrieval only happens per-turn, on
  the agent's own decision -- so routine questions don't pay a retrieval
  tax, and hard questions still get a real, current answer.
- **Tool-calling with a hard approval gate, not just a prompt instruction.**
  The agent can always answer "what would this change do?" (read-only
  tools, no gate). It can never actually trigger a deployment without an
  explicit human-approved plan first -- enforced by the tool contract
  itself, not by asking the model nicely.

**Where this is headed:** `docs/08` includes a walkthrough of
[Pydantic AI](https://ai.pydantic.dev/) as the natural next step for this
kind of platform -- replacing hand-rolled terminal-output parsing with
typed tool signatures, structured outputs, and dependency-injected tool
clients, so the approval gate becomes a type-system guarantee instead of
a runtime check.

## Repository Layout

```
AVD-Automation-Portfolio/
├── README.md                              <- you are here
├── docs/
│   ├── 01-architecture-overview.md        <- system design & design decisions
│   ├── 02-terraform-provisioning-flow.md  <- IaC provisioning flow
│   ├── 03-session-host-replacer-flow.md   <- zero-downtime image rollout + self-healing
│   ├── 04-ansible-configuration-flow.md   <- config management flow + scaling-plan rationale
│   ├── 05-cicd-orchestration-flow.md      <- pipeline orchestration flow
│   ├── 06-ai-deployment-agent.md          <- AI agent that drives the pipeline
│   ├── 07-terraform-module-repo-pattern.md <- shared modules repo, pinned by ref
│   └── 08-ai-agent-web-platform.md        <- serving platform: boot, sessions, KB strategy
├── sample-code/
│   ├── terraform/                         <- "deployment repo": thin, calls modules by pinned ref
│   │   └── environments/pilot|prod/           <- nested per-environment, per-persona tfvars
│   ├── terraform-modules-repo/            <- "module repo": networking, host-pool, workspace,
│   │                                          session-hosts, private-endpoint, scaling-plan
│   ├── concord/                           <- orchestrator flows: template, session-host-replacer,
│   │                                          redeploy-session-hosts (Concord's public DSL)
│   ├── ansible/                           <- task playbook + host-pool wrapper
│   ├── session-host-replacer/             <- rolling-upgrade + unhealthy-host replace loops
│   └── ai-agent/                          <- tool-calling deployment agent skeleton
└── linkedin/
    ├── linkedin_post_short.md
    ├── linkedin_post_long.md
    └── resume_bullet_points.md
```

## Recognition

The zero-downtime rolling session-host replacer (see `docs/03`) is a
custom-built capability -- Azure's AVD control plane doesn't offer
zero-downtime image rollout natively, and this wasn't adapted from a
Microsoft reference architecture or first-party tool. It was designed and
built from scratch, and reviewed by a Microsoft AVD architect who
recognized it as going beyond Azure's native capabilities.

## Why I built it this way

Running 50 host pools across 2 regions with 500+ applications by hand doesn't
scale — and enterprise VDI has a few recurring failure modes I hit personally:
session hosts silently go unhealthy, Terraform state locks orphan after
interrupted runs, subnets run out of IPs during bursty scale-out, and
onboarding a new business unit ("persona") by hand eats real engineering time.
The choices in this code — declarative IaC, an explicit approval gate before
any `apply`, an idempotent persona pattern, and an automated replacer loop
instead of manual VM babysitting — were direct fixes for problems I ran into
and debugged myself.

See `docs/` for a deeper walkthrough of each flow.

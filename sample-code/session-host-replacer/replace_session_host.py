"""
Generic example: session-host replacer supporting two control loops.

Illustrative only -- a from-scratch, non-proprietary implementation showing
the patterns described in docs/03-session-host-replacer-flow.md. Not
intended to be run as-is against a real environment.

Loop 1: unhealthy-host replacement (fast path, 1:1, immediate)
Loop 2: image-drift rolling replacement (zero-downtime, create-before-delete)
"""

from dataclasses import dataclass
from typing import Optional
import logging
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("session-host-replacer")


@dataclass
class SessionHost:
    name: str
    host_pool: str
    region: str
    tags: dict
    is_healthy: bool
    power_state: str    # "running" | "deallocated" | "stopped"
    image_version: str
    active_sessions: int = 0
    drained: bool = False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def has_required_tags(host: SessionHost) -> bool:
    required = {"region", "persona", "environment", "image_version"}
    return required.issubset(host.tags.keys())


def drain(host: SessionHost) -> None:
    log.info("Draining %s (no new sessions will be assigned)", host.name)
    host.drained = True


def deregister(host: SessionHost) -> None:
    log.info("Deregistering %s from host pool %s", host.name, host.host_pool)


def safe_delete(host: SessionHost) -> None:
    """Delete the VM and its resources, guarding against a known 409
    conflict when deleting extensions on a stopped/deallocated VM."""
    if host.power_state == "running":
        log.info("Removing extensions from %s before delete", host.name)
    else:
        log.info(
            "%s is %s; skipping extension removal to avoid 409 conflict",
            host.name, host.power_state,
        )
    log.info("Deleting VM resources for %s", host.name)


def reprovision(host_pool: str, count: int, image_version: str) -> list[SessionHost]:
    log.info(
        "Triggering IaC re-provision of %d host(s) for %s on image %s",
        count, host_pool, image_version,
    )
    # Real implementation triggers the Terraform provisioning flow
    # (see docs/02-terraform-provisioning-flow.md), then polls for the
    # resulting VMs. Returned here as placeholders for illustration.
    return [
        SessionHost(
            name=f"{host_pool}-new-{i}",
            host_pool=host_pool,
            region="eastus2",
            tags={"region": "eastus2", "persona": host_pool,
                  "environment": "prod", "image_version": image_version},
            is_healthy=True,
            power_state="running",
            image_version=image_version,
        )
        for i in range(count)
    ]


def wait_until_healthy(hosts: list[SessionHost], timeout_seconds: int = 600) -> bool:
    """Poll new hosts until they've registered with the pool, passed an
    agent-heartbeat check, and are out of drain mode. Placeholder sleep
    stands in for real polling against the AVD management API."""
    log.info("Waiting for %d new host(s) to register and pass health checks", len(hosts))
    time.sleep(0)  # real implementation: poll with backoff up to timeout_seconds
    return all(h.is_healthy for h in hosts)


# ---------------------------------------------------------------------------
# Loop 1: unhealthy-host replacement -- fast path, immediate, 1:1
# ---------------------------------------------------------------------------

def discover_unhealthy_hosts(host_pool: str) -> list[SessionHost]:
    """Never returns None -- an empty list means 'nothing to do', which
    keeps downstream code from needing null-checks (a real null-array bug
    used to crash this exact step)."""
    return []  # placeholder for illustration


def replace_unhealthy_hosts(host_pool: str, batch_size: int = 1) -> None:
    unhealthy = discover_unhealthy_hosts(host_pool)
    if not unhealthy:
        log.info("No unhealthy hosts found in %s; nothing to do", host_pool)
        return

    for host in unhealthy[:batch_size]:
        if not has_required_tags(host):
            log.warning(
                "%s is missing required tags; flagging for manual review "
                "instead of auto-deleting", host.name,
            )
            continue
        drain(host)
        deregister(host)
        safe_delete(host)

    # Unhealthy hosts are already not serving capacity -- no need to
    # create-before-delete here the way the rolling upgrade does below.
    reprovision(host_pool, count=min(batch_size, len(unhealthy)),
                image_version=unhealthy[0].image_version)


# ---------------------------------------------------------------------------
# Loop 2: image-drift rolling replacement -- zero-downtime, create-before-delete
# ---------------------------------------------------------------------------

def get_latest_published_image_version(persona: str) -> str:
    """Real implementation queries the Azure Compute Gallery for the
    latest image version tied to this persona's image definition."""
    return "1.5.0"  # placeholder for illustration


def discover_drifted_hosts(host_pool: str, latest_version: str) -> list[SessionHost]:
    """Returns hosts whose image_version tag doesn't match the latest
    published version. Never returns None."""
    return []  # placeholder for illustration


def rolling_replace_pool(
    host_pool: str,
    minimum_ready_capacity: int,
    batch_size: int = 1,
) -> None:
    """Zero-downtime rolling upgrade: create the replacement batch first,
    wait for it to be healthy, only THEN drain and delete the equivalent
    number of old-version hosts. Repeats until the whole pool is current.

    This is the capability that isn't natively available in Azure AVD's
    control plane -- built from scratch to behave like a blue/green
    rollout for VDI session hosts instead of a stateless web fleet.
    """
    latest_version = get_latest_published_image_version(persona=host_pool)
    drifted = discover_drifted_hosts(host_pool, latest_version)

    if not drifted:
        log.info("%s is already fully on image version %s", host_pool, latest_version)
        return

    log.info(
        "%d host(s) in %s are behind image version %s; starting rolling upgrade",
        len(drifted), host_pool, latest_version,
    )

    remaining = list(drifted)
    while remaining:
        batch = remaining[:batch_size]

        # 1. Create the new-version replacements FIRST -- capacity goes up
        #    before anything old is removed.
        new_hosts = reprovision(host_pool, count=len(batch), image_version=latest_version)

        # 2. Don't touch a single old host until the new batch is verified
        #    healthy and actually accepting sessions.
        if not wait_until_healthy(new_hosts):
            log.error(
                "New batch for %s failed health checks; pausing rollout "
                "without touching any old-version hosts", host_pool,
            )
            return

        # 3. Guardrail: never let ready capacity dip below the pool minimum,
        #    even transiently, while retiring old hosts.
        projected_ready = len(remaining) - len(batch) + len(new_hosts)
        if projected_ready < minimum_ready_capacity:
            log.error(
                "Draining this batch would drop %s below minimum ready "
                "capacity (%d); pausing rollout", host_pool, minimum_ready_capacity,
            )
            return

        # 4. Only now retire the old-version hosts in this batch.
        for old_host in batch:
            if not has_required_tags(old_host):
                log.warning(
                    "%s missing required tags; skipping auto-retire, "
                    "flagging for manual review", old_host.name,
                )
                continue
            drain(old_host)
            deregister(old_host)
            safe_delete(old_host)

        remaining = remaining[batch_size:]

    log.info("Rolling upgrade of %s to image version %s complete", host_pool, latest_version)


if __name__ == "__main__":
    replace_unhealthy_hosts(host_pool="example-persona", batch_size=1)
    rolling_replace_pool(host_pool="example-persona", minimum_ready_capacity=4, batch_size=2)

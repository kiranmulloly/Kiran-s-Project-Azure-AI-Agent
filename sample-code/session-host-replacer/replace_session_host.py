"""
Generic example: self-healing session host replacer.

Illustrative only — a from-scratch, non-proprietary implementation showing
the control-loop pattern described in docs/03-session-host-replacer-flow.md.
Not intended to be run as-is against a real environment.
"""

from dataclasses import dataclass
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("session-host-replacer")


@dataclass
class SessionHost:
    name: str
    host_pool: str
    region: str
    tags: dict
    is_healthy: bool
    power_state: str  # "running" | "deallocated" | "stopped"


def discover_unhealthy_hosts(host_pool: str) -> list[SessionHost]:
    """Query the host pool for hosts failing health checks.

    Real implementation would call the cloud provider / AVD management API.
    Returns an empty list (never None) so downstream code never has to
    null-check — a defensive pattern learned from a real null-array bug
    that used to crash this exact step.
    """
    return []  # placeholder for illustration


def drain(host: SessionHost) -> None:
    log.info("Draining %s (no new sessions will be assigned)", host.name)


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
            host.name,
            host.power_state,
        )
    log.info("Deleting VM resources for %s", host.name)


def has_required_tags(host: SessionHost) -> bool:
    required = {"region", "persona", "environment"}
    return required.issubset(host.tags.keys())


def reprovision(host_pool: str, count: int = 1) -> None:
    log.info("Triggering IaC re-provision of %d host(s) for %s", count, host_pool)
    # Real implementation triggers the Terraform provisioning flow
    # (see docs/02-terraform-provisioning-flow.md).


def replace_unhealthy_hosts(host_pool: str, batch_size: int = 1) -> None:
    unhealthy = discover_unhealthy_hosts(host_pool)

    if not unhealthy:
        log.info("No unhealthy hosts found in %s; nothing to do", host_pool)
        return

    for host in unhealthy[:batch_size]:
        if not has_required_tags(host):
            log.warning(
                "%s is missing required tags; flagging for manual review "
                "instead of auto-deleting",
                host.name,
            )
            continue

        drain(host)
        deregister(host)
        safe_delete(host)

    reprovision(host_pool, count=min(batch_size, len(unhealthy)))


if __name__ == "__main__":
    replace_unhealthy_hosts(host_pool="example-persona", batch_size=1)

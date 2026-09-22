"""
Generic example: AI deployment agent control loop.

Illustrative only -- a from-scratch, non-proprietary skeleton showing the
tool-registration and orchestration pattern described in
docs/06-ai-deployment-agent.md. This is NOT a working LLM integration; the
`decide_next_action` function stands in for wherever an actual model call
would go. Not intended to be run as-is.

Note: this hand-rolled dict-based tool registry is a fine v1, but see the
"Modernizing this with Pydantic AI" section in docs/06 (and docs/08 for the
broader argument) for how a framework like Pydantic AI replaces this with
typed tool signatures, structured outputs, and dependency-injected clients.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("deployment-agent")


# ---------------------------------------------------------------------------
# Tool registry -- every capability the agent can invoke is an explicit,
# independently auditable function. Nothing destructive is reachable except
# through trigger_deploy, and that tool refuses to run without an approval
# flag having been set first.
# ---------------------------------------------------------------------------

@dataclass
class DeploymentRequest:
    persona: str
    environment: str
    change_summary: str
    approved: bool = False
    plan_shown: bool = False


def get_plan(request: DeploymentRequest) -> str:
    log.info("[tool] get_plan: dry-run for %s/%s", request.persona, request.environment)
    request.plan_shown = True
    return f"Dry-run plan for {request.persona} ({request.environment}): 2 to add, 0 to destroy."


def trigger_deploy(request: DeploymentRequest) -> str:
    if not request.plan_shown:
        raise RuntimeError("Refusing to deploy: no plan has been shown yet")
    if not request.approved:
        raise RuntimeError("Refusing to deploy: change has not been approved")
    log.info("[tool] trigger_deploy: running pipeline for %s/%s",
              request.persona, request.environment)
    return "run-id-12345"


def get_status(run_id: str) -> str:
    log.info("[tool] get_status: polling %s", run_id)
    return "SUCCESS"


def search_knowledge_base(error_signature: str) -> Optional[str]:
    log.info("[tool] search_knowledge_base: %s", error_signature)
    return None  # placeholder: real implementation does semantic search


def update_ticket(ticket_id: str, status: str, note: str) -> None:
    log.info("[tool] update_ticket: %s -> %s (%s)", ticket_id, status, note)


def post_chat_notification(message: str) -> None:
    log.info("[tool] post_chat_notification: %s", message)


TOOLS: dict[str, Callable] = {
    "get_plan": get_plan,
    "trigger_deploy": trigger_deploy,
    "get_status": get_status,
    "search_knowledge_base": search_knowledge_base,
    "update_ticket": update_ticket,
    "post_chat_notification": post_chat_notification,
}


# ---------------------------------------------------------------------------
# Control loop
# ---------------------------------------------------------------------------

def handle_request(request: DeploymentRequest, ticket_id: str, human_approves: bool) -> None:
    """End-to-end illustrative flow: plan -> human gate -> deploy -> monitor
    -> report. `human_approves` stands in for wherever the real approval
    signal comes from (a chat reaction, a ticket transition, etc.)."""

    plan_summary = TOOLS["get_plan"](request)
    TOOLS["post_chat_notification"](f"Proposed change:\n{plan_summary}\nWaiting for approval.")

    if not human_approves:
        TOOLS["update_ticket"](ticket_id, "rejected", "Human did not approve the plan")
        return

    request.approved = True
    run_id = TOOLS["trigger_deploy"](request)
    TOOLS["update_ticket"](ticket_id, "in_progress", f"Deploy triggered: {run_id}")

    result = TOOLS["get_status"](run_id)

    if result == "SUCCESS":
        TOOLS["update_ticket"](ticket_id, "done", "Deploy completed successfully")
        TOOLS["post_chat_notification"](f"{request.persona} deploy complete.")
    else:
        hint = TOOLS["search_knowledge_base"](result)
        note = hint or "No matching known issue found; needs human triage"
        TOOLS["update_ticket"](ticket_id, "failed", note)
        TOOLS["post_chat_notification"](f"{request.persona} deploy failed: {note}")


if __name__ == "__main__":
    req = DeploymentRequest(
        persona="example-persona",
        environment="pilot",
        change_summary="Add 2 session hosts",
    )
    handle_request(req, ticket_id="TICKET-123", human_approves=True)

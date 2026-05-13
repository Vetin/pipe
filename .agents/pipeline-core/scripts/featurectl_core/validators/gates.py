"""State and gate-shape validators."""

from __future__ import annotations

from typing import Any

from ..shared import CONTRACT_VERSION, DEFAULT_GATES, VALID_GATE_STATES, VALID_WORKSPACE_LIFECYCLES


def validate_state_shape(state: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if state.get("artifact_contract_version") != CONTRACT_VERSION:
        blockers.append("state.yaml artifact_contract_version mismatch")
    if "next_skill" in state:
        blockers.append("state.yaml must not contain next_skill")
    gates = state.get("gates")
    if not isinstance(gates, dict):
        blockers.append("state.yaml gates must be a mapping")
    else:
        for gate in DEFAULT_GATES:
            if gate not in gates:
                blockers.append(f"state.yaml missing gate: {gate}")
            elif gates[gate] not in VALID_GATE_STATES:
                blockers.append(f"invalid gate status for {gate}: {gates[gate]}")
    stale = state.get("stale")
    if not isinstance(stale, dict):
        blockers.append("state.yaml stale must be a mapping")
    lifecycle = state.get("lifecycle")
    if lifecycle is not None and lifecycle not in VALID_WORKSPACE_LIFECYCLES:
        blockers.append(f"state.yaml invalid lifecycle: {lifecycle}")
    if state.get("read_only") is not None and not isinstance(state.get("read_only"), bool):
        blockers.append("state.yaml read_only must be boolean")
    return blockers

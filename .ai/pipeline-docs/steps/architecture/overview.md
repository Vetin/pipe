# Architecture Step

Describe how the feature fits into the system, how modules communicate, what
decisions are significant, and which risks must be managed before technical
design.

Architecture is a repository-grounded change set. Identify new, modified,
removed, and unchanged behavior; cite inspected modules or ADRs; document
alternatives and tradeoffs; and finish with a completeness/correctness/coherence
check before technical design starts.

Every architecture artifact must include a high-level Mermaid feature topology
that shows how actors, entry points, services/modules, persistence, events, and
external systems communicate. This topology is intentionally above code detail:
it should let a reviewer understand the feature shape before reading the
technical design.

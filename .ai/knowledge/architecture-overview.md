# Architecture Overview

Status: initial
Confidence: low
Needs human review: yes

The pipeline architecture is worktree-first. Feature work starts in a dedicated
git worktree, keeps in-progress artifacts under `.ai/feature-workspaces/`, and
promotes completed memory into `.ai/features/`.

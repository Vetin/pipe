#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: pipeline-lab/manual-check/preflight.sh <workspace>" >&2
  exit 2
fi

WORKSPACE="$1"
ROOT="$(git rev-parse --show-toplevel)"
FEATURECTL="$ROOT/.agents/pipeline-core/scripts/featurectl.py"

echo "== git branch =="
git branch --show-current

echo "== git status =="
git status --short

echo "== feature status =="
python "$FEATURECTL" status --workspace "$WORKSPACE"

echo "== base validation =="
python "$FEATURECTL" validate --workspace "$WORKSPACE"

echo "== planning package validation =="
python "$FEATURECTL" validate --workspace "$WORKSPACE" --planning-package

echo "== implementation readiness =="
if python "$FEATURECTL" implementation-ready --workspace "$WORKSPACE"; then
  echo "implementation_readiness: pass"
else
  echo "implementation_readiness: blocked"
fi

echo "== worktree status =="
if python "$FEATURECTL" worktree-status --workspace "$WORKSPACE"; then
  echo "worktree_status: pass"
else
  echo "worktree_status: blocked"
fi

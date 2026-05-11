# Context Step

Discover existing repository knowledge before drafting product behavior.

If `.ai/knowledge` is missing or sparse, inspect repository files and create
provisional knowledge documents with confidence and source notes.

For repeatable project discovery, run `featurectl.py init --profile-project` at
the repository root. Use the generated `project-index.yaml` and
`project-snapshot.md` as source maps, then verify claims by reading the cited
files before drafting feature behavior or architecture.

The context step must answer "does this already exist?" before proposing new
modules. Record a reuse map of related features, modules, contracts, tests,
jobs, schemas, migrations, and ADRs. Separate source-backed facts from
generated hypotheses, and carry any new ambiguity into the feature contract
instead of hiding it in assumptions.

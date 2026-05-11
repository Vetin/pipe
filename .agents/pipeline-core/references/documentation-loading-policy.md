# Documentation Loading Policy

`featurectl.py load-docset` lists step-specific required and optional docs. It
does not prove the LLM used those docs.

Every skill must therefore record docs actually used in `execution.md` under a
step-specific `Docs Consulted: <Step>` section.

If required docs are missing, the skill may continue only when the missing docs
are not required for safety. It must record the gap and any provisional
assumptions.

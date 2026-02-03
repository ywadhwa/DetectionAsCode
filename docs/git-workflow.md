# Git Workflow & Branching Strategy

This personal DaC repo uses a **single long-lived branch** and a **single short-lived branch prefix**:

- **`main`**: The only long-lived branch and release source of truth.
- **`dev/*`**: Short-lived working branches for all detection work and tooling changes.

## Scenario A — New Detections (dev/* → main via PR)

**Rule**: Never push detection changes directly to `main`.

```bash
git checkout main
git pull origin main

git checkout -b dev/new-suspicious-powershell

# Make changes and validate
./scripts/validate.sh

git add .
git commit -m "Add suspicious PowerShell detection"

git push origin dev/new-suspicious-powershell
```

Open a Pull Request targeting `main` and include a clear summary:
- What the detection does
- Data sources used
- Validation performed

## Scenario B — Small Fixes / Typos (direct to main)

You may push directly to `main` **only** for:
- typos
- comments
- README/docs wording
- non-functional formatting changes

**Commit message prefixes are required:**
- `FIX:` for small functional fixes
- `TYPO:` for documentation or spelling fixes

```bash
git checkout main
git pull origin main

git add .
git commit -m "TYPO: fix README wording"

git push origin main
```

## Scenario C — Infrastructure / Tooling (dev/pipeline-test → main via PR)

All changes to pipelines, scripts, validation tooling, or repo automation **must** use:

- `dev/pipeline-test`

```bash
git checkout main
git pull origin main

git checkout -b dev/pipeline-test

# Make changes and validate
./scripts/validate.sh

git add .
git commit -m "Update validation tooling"

git push origin dev/pipeline-test
```

Open a Pull Request targeting `main`.

## Local validation

Run the full validation suite before opening a PR:

```bash
./scripts/validate.sh
```

# Git Workflow & Branching Strategy

## Concise workflow (step-by-step)

1. **Create feature branch** from `develop` using `feature/<ticket>-<short-description>`.
2. **Author or update Sigma rules** under `detections/dev/` and include required metadata.
3. **Open PR to `develop`** with required template, labels, and reviewers.
4. **CI runs on PR**: lint → schema/metadata/quality checks → conversion → unit tests.
5. **Merge to `develop`** after approvals and green checks.
6. **Promote to test** by creating a `release/<version>` branch from `develop`.
7. **CI runs on release**: lint → conversion → integration tests (Splunk/ADX) → packaging.
8. **Merge release to `main`** after validation and approvals.
9. **Tag release** in `main` and deploy detections to production.
10. **Hotfixes** branch from `main` using `hotfix/<ticket>-<short-description>`, then PR back to `main` and `develop`.

## Branch roles & rules

- **main**: production branch. Only release/hotfix merges. Protected; no direct pushes.
- **develop**: integration branch for in-flight detections. Protected; no direct pushes.
- **feature/**: short-lived branches for rule changes and new detections.
- **release/**: stabilization branches for integration testing and packaging.
- **hotfix/**: urgent production fixes branched from `main`.

## Environment promotion model (dev → test → prod)

- **dev**: rules land in `develop` and live under `detections/dev/`.
- **test**: `release/*` branches promote rules into `detections/test/` for integration tests.
- **prod**: `main` contains `detections/prod/` for production deployment.

Promotion is handled via PRs that copy or move rules between environment folders with change control and review.

## Branch diagram (ASCII)

```
feature/* --> PR --> develop --> release/* --> PR --> main
                    ^                 |
                    |                 +--> tag vX.Y.Z
hotfix/*  ----------+------------------------------> main
  \______________________________________________> develop
```

## PR process (standards)

- **Naming**: `[DAC-1234] <short summary>`
- **Required templates**: PR template requires test evidence, rule metadata changes, and ATT&CK mapping summary.
- **Required labels**: `type/detection`, `env/dev` or `env/test`, `risk/low|med|high`.
- **Reviewers**: at least 2 approvals; 1 must be from Detection Engineering; 1 from Platform Security.
- **Checks**: all required status checks must pass; no bypasses.

## Branch protection (example settings)

**main**
- Require pull request reviews: 2
- Require review from CODEOWNERS: ✅
- Require status checks: lint, conversion, unit-tests, splunk-integration, adx-integration, packaging
- Require signed commits: ✅ (if org policy mandates)
- Require linear history: ✅
- Restrict who can push: release managers only
- No force pushes, no deletions

**develop**
- Require pull request reviews: 1–2
- Require review from CODEOWNERS: ✅
- Require status checks: lint, conversion, unit-tests
- Require signed commits: optional
- No force pushes, no direct pushes

## Versioning & tagging strategy

- **Semantic versioning**: `v<major>.<minor>.<patch>`
- **Release tags** are applied on `main` after merge from `release/*`.
- **Patch releases** originate from `hotfix/*` and bump `patch`.
- **Minor releases** aggregate new detections from `develop`.
- **Major releases** reserved for breaking changes in rule schema or pipeline behavior.

## CI/CD mapping by branch

| Event | Branch | Pipeline stages |
| --- | --- | --- |
| PR opened/updated | feature/* → develop | lint, schema/metadata/quality, conversion, unit tests |
| PR opened/updated | release/* → main | lint, conversion, integration tests (Splunk/ADX), packaging |
| Push | develop | lint, conversion, unit tests |
| Push | release/* | lint, conversion, integration tests, packaging |
| Push | main | deploy production detections + tag verification |

## Example CODEOWNERS guidance

```
# CODEOWNERS
/detections/** @org/detection-engineering
/scripts/** @org/detection-platform
/.github/** @org/security-platform
/azure-pipelines/** @org/security-platform
```

## Example folder structure for dev/test/prod

```
detections/
├── dev/
│   ├── endpoint/
│   ├── cloud/
│   └── network/
├── test/
│   ├── endpoint/
│   ├── cloud/
│   └── network/
└── prod/
    ├── endpoint/
    ├── cloud/
    └── network/
```

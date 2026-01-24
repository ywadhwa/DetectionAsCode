# Branching Workflow (Wiki)

## When to use each branch type

- **feature/**: Use for new detections or improvements that are not production-critical. Branch from `develop`.
- **release/**: Use to stabilize a set of changes for test/prod promotion. Branch from `develop`.
- **hotfix/**: Use for urgent production fixes. Branch from `main`.

## Step-by-step: pushing code

1. **Sync local repo**
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/DAC-1234-short-description
   ```

3. **Make changes and commit**
   ```bash
   git add .
   git commit -m "[DAC-1234] Add new detection for <case>"
   ```

4. **Push branch to GitHub**
   ```bash
   git push origin feature/DAC-1234-short-description
   ```

5. **Open PR to `develop`**
   - Ensure required labels and reviewers are applied.
   - Confirm all CI checks are green.

6. **Promote to release** (when ready for test/prod)
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.2.0
   git push origin release/v1.2.0
   ```
   - Open PR from `release/v1.2.0` → `main`.

7. **Hotfix flow** (urgent production issue)
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/DAC-5678-short-description
   git push origin hotfix/DAC-5678-short-description
   ```
   - Open PR from `hotfix/*` → `main`.
   - After merge, backport to `develop` via PR.

## PR requirements (summary)

- **Naming**: `[DAC-1234] <short summary>`
- **Labels**: `type/detection`, `risk/<level>`, `env/<dev|test|prod>`
- **Reviewers**: 2 approvals; 1 Detection Engineering, 1 Platform Security
- **Checks**: lint, validation, conversion, integration tests (for release/hotfix)

## Notes

- Only `main` and `develop` are long-lived protected branches.
- All changes must flow through PRs.
- Release tags are applied on `main` after merge.

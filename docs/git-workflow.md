# Git Workflow & Branching Strategy

This repository uses only **two long-lived branches**:

- **`develop`**: Daily work and integration. All changes land here first.
- **`main`**: Stable releases. Only updated when you decide to release.

## Normal work (develop)

```bash
git checkout develop
git pull origin develop

# Make changes, then commit
git add .
git commit -m "Describe your change"

git push origin develop
```

## Release (develop → main)

```bash
git checkout main
git pull origin main

git merge --no-ff develop
git push origin main

# Tag the release
git tag -a release-<version> -m "Release <version>"
git push origin release-<version>
```

### When to merge main → develop

Only do this if `main` has release-specific changes (for example, a version bump or
changelog edits) that should be reflected back in `develop`.

```bash
git checkout develop
git pull origin develop

git merge --no-ff main
git push origin develop
```

## Fixes (no hotfix branches)

If `main` needs a rollback, use `git revert` on `main`, then fix forward on `develop`.

```bash
# Roll back on main

git checkout main
git pull origin main

git revert <commit-sha>
git push origin main

# Fix forward on develop

git checkout develop
git pull origin develop
# apply the proper fix

git add .
git commit -m "Fix forward after revert"
git push origin develop
```

## Local validation

Run the full validation suite before pushing to `develop`:

```bash
./scripts/validate.sh
```

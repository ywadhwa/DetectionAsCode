# Detection-as-Code UI

This lightweight Flask UI lets detection engineers author Sigma rules, select conversion targets, and open GitHub pull requests.

## Run locally

```bash
pip install -r requirements.txt
export GITHUB_TOKEN="<token with repo scope>"
export GITHUB_REPO="org/repo"
export GITHUB_DEFAULT_BRANCH="main"
python ui/app.py
```

Open `http://localhost:5001` (or your configured `PORT`) and submit a rule. The UI creates a branch, commits the Sigma rule, and opens a pull request to trigger the CI/CD pipeline.

## Required environment variables

| Variable | Purpose |
| --- | --- |
| `GITHUB_TOKEN` | GitHub token with permissions to create branches, commits, and pull requests. |
| `GITHUB_REPO` | Repository in `owner/name` format. |
| `GITHUB_DEFAULT_BRANCH` | Base branch for PRs (defaults to repository default). |

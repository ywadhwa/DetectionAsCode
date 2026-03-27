#!/usr/bin/env python3
"""Simple web UI for creating/updating Sigma rules and opening GitHub PRs."""
import base64
import datetime as dt
import os
import re
import uuid
from typing import Dict, List, Optional

import requests
import yaml
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

ALLOWED_CATEGORIES = ["endpoint", "cloud", "macos", "network", "web"]


def normalize_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def build_rule_payload(form: Dict[str, str]) -> Dict[str, object]:
    references = [item.strip() for item in form.get("references", "").splitlines() if item.strip()]
    tags = [item.strip() for item in form.get("tags", "").splitlines() if item.strip()]
    falsepositives = [item.strip() for item in form.get("falsepositives", "").splitlines() if item.strip()]

    detection_yaml = form.get("detection", "").strip()
    if detection_yaml:
        detection = yaml.safe_load(detection_yaml)
    else:
        detection = {"selection": {"example": "value"}, "condition": "selection"}

    logsource = {key: value for key, value in {
        "product": form.get("logsource_product"),
        "category": form.get("logsource_category"),
        "service": form.get("logsource_service"),
    }.items() if value}

    conversion_targets = []
    if form.get("conversion_kql"):
        conversion_targets.append("kql")
    if form.get("conversion_splunk"):
        conversion_targets.append("splunk")

    return {
        "title": form.get("title"),
        "id": form.get("rule_id") or str(uuid.uuid4()),
        "status": form.get("status"),
        "description": form.get("description"),
        "references": references,
        "author": form.get("author"),
        "date": form.get("date") or dt.date.today().strftime("%Y/%m/%d"),
        "modified": dt.date.today().strftime("%Y/%m/%d"),
        "tags": tags,
        "conversion_targets": conversion_targets or ["kql", "splunk"],
        "logsource": logsource,
        "detection": detection,
        "falsepositives": falsepositives,
        "level": form.get("level"),
    }


def github_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def get_default_branch(repo: str, token: str) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{repo}",
        headers=github_headers(token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("default_branch", "main")


def create_branch(repo: str, token: str, base_branch: str, new_branch: str) -> None:
    ref_response = requests.get(
        f"https://api.github.com/repos/{repo}/git/ref/heads/{base_branch}",
        headers=github_headers(token),
        timeout=30,
    )
    ref_response.raise_for_status()
    base_sha = ref_response.json()["object"]["sha"]

    create_response = requests.post(
        f"https://api.github.com/repos/{repo}/git/refs",
        headers=github_headers(token),
        json={"ref": f"refs/heads/{new_branch}", "sha": base_sha},
        timeout=30,
    )
    create_response.raise_for_status()


def upsert_file(
    repo: str,
    token: str,
    branch: str,
    path: str,
    content: str,
    message: str,
) -> None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    existing = requests.get(
        url,
        headers=github_headers(token),
        params={"ref": branch},
        timeout=30,
    )
    sha = None
    if existing.status_code == 200:
        sha = existing.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=github_headers(token), json=payload, timeout=30)
    response.raise_for_status()


def create_pull_request(repo: str, token: str, head: str, base: str, title: str, body: str) -> str:
    response = requests.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=github_headers(token),
        json={"title": title, "head": head, "base": base, "body": body},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("html_url", "")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", categories=ALLOWED_CATEGORIES)


@app.route("/submit", methods=["POST"])
def submit_rule():
    form = request.form.to_dict()
    category = form.get("category")
    if category not in ALLOWED_CATEGORIES:
        return "Invalid category", 400

    filename_slug = normalize_slug(form.get("filename", "") or form.get("title", ""))
    if not filename_slug:
        return "Filename or title required", 400

    rule_path = form.get("rule_path")
    if not rule_path:
        rule_path = f"sigma-rules/{category}/{category}_{filename_slug}.yml"

    rule_payload = build_rule_payload(form)
    yaml_content = yaml.safe_dump(rule_payload, sort_keys=False)

    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    base_branch = os.getenv("GITHUB_DEFAULT_BRANCH")
    if not token or not repo:
        return "GITHUB_TOKEN and GITHUB_REPO are required to submit rules", 500

    if not base_branch:
        base_branch = get_default_branch(repo, token)

    branch_name = f"ui/{filename_slug}-{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    create_branch(repo, token, base_branch, branch_name)

    upsert_file(
        repo,
        token,
        branch_name,
        rule_path,
        yaml_content,
        message=f"Add/update Sigma rule: {rule_payload['title']}",
    )

    pr_url = create_pull_request(
        repo,
        token,
        branch_name,
        base_branch,
        title=f"Sigma rule update: {rule_payload['title']}",
        body="Automated submission from Detection-as-Code UI.",
    )

    return redirect(pr_url or url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")

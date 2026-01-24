#!/usr/bin/env python3
"""Generate detection and content pack documentation from metadata."""
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader


def main() -> None:
    repo_root = Path(__file__).parent.parent
    template_dir = repo_root / "templates"
    output_dir = repo_root / "documentation"
    (output_dir / "detections").mkdir(parents=True, exist_ok=True)
    (output_dir / "content-packs").mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=False)
    detection_template = env.get_template("detection.md.j2")
    pack_template = env.get_template("content_pack.md.j2")

    detections_index = []
    for rule_file in sorted((repo_root / "sigma-rules").rglob("*.yml")):
        rule = yaml.safe_load(rule_file.read_text(encoding="utf-8")) or {}
        meta_path = rule_file.with_suffix(".meta.yml")
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        content = detection_template.render(
            title=rule.get("title", rule_file.stem),
            id=rule.get("id", ""),
            status=rule.get("status", ""),
            version=rule.get("version", ""),
            owner=meta.get("owner", ""),
            content_pack=rule.get("content_pack"),
            description=rule.get("description", ""),
            logsource=rule.get("logsource", {}),
            tags=rule.get("tags", []) or [],
            references=rule.get("references", []) or [],
            falsepositives=rule.get("falsepositives", []) or [],
        )
        out_path = output_dir / "detections" / f"{rule_file.stem}.md"
        out_path.write_text(content, encoding="utf-8")
        detections_index.append(out_path.name)

    packs_index = []
    for pack_file in sorted((repo_root / "content-packs").glob("*.yml")):
        pack = yaml.safe_load(pack_file.read_text(encoding="utf-8")) or {}
        content = pack_template.render(
            name=pack.get("name", pack_file.stem),
            version=pack.get("version", ""),
            owner=pack.get("owner", ""),
            description=pack.get("description", ""),
            detections=pack.get("detections", []) or [],
        )
        out_path = output_dir / "content-packs" / f"{pack_file.stem}.md"
        out_path.write_text(content, encoding="utf-8")
        packs_index.append(out_path.name)

    index_lines = ["# Documentation Index", "", "## Detections"]
    index_lines.extend([f"- documentation/detections/{name}" for name in detections_index])
    index_lines.append("")
    index_lines.append("## Content Packs")
    index_lines.extend([f"- documentation/content-packs/{name}" for name in packs_index])
    (output_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

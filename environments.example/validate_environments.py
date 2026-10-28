#!/usr/bin/env python3
"""Structural + cross-file consistency checks for ~/.claude/environments/*.json.

Usage: python3 validate_environments.py [environments_dir]
Defaults to $CLAUDE_CONFIG_DIR/environments if that's set, else
~/.claude/environments — the same resolution qa-tester/testing-api/
routing-qa-tickets use.

Catches config-shape mistakes (missing required fields, wrong types, a
'workDir' that doesn't exist on disk, an
`api`/`surfaces` block with the wrong nested shape, a product with neither
block at all) and one class of live drift: a product's `jira.connector`
naming a connector that either isn't in atlassian-connectors.json at all, or
is mapped there to a different site than the product's own `jira.site` says.

It does NOT check whether that connector is actually authorized right now —
only that the files agree with each other. Confirm live authorization
separately with that connector's own getAccessibleAtlassianResources tool.
"""
import json
import os
import sys
from pathlib import Path

VALID_CLIENTS = {"bruno", "postman", "insomnia"}
VALID_PUBLISH_TARGETS = {"1password", "confluence", "none"}
VALID_EVIDENCE_MODES = {"auto", "ask"}
VALID_INSTALL_MODES = {"clean", "update", "installed"}
META_FILES = {"atlassian-connectors.json", "evidence.json", "qa-agent-migrations.json"}


def resolve_environments_dir():
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(override) if override else Path.home() / ".claude"
    return base / "environments"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def check_product_config(data, connectors):
    errors = []

    def require(field, typ, container=data, label=None):
        label = label or field
        if field not in container:
            errors.append(f"missing required field '{label}'")
            return None
        value = container[field]
        if not isinstance(value, typ):
            errors.append(f"'{label}' should be {typ.__name__}, got {type(value).__name__}")
            return None
        return value

    require("product", str)
    work_dir = require("workDir", str)
    if work_dir is not None:
        if not work_dir.strip():
            errors.append("'workDir' must be a non-empty path string")
        elif not Path(work_dir).expanduser().is_dir():
            errors.append(f"'workDir' ({work_dir}) doesn't exist — create it (mkdir -p)")
    if "projectSkill" in data:
        skill = data["projectSkill"]
        if not isinstance(skill, str) or not skill.strip():
            errors.append("'projectSkill' must be a non-empty path string when present")
        elif not (Path(skill).expanduser() / "SKILL.md").is_file():
            errors.append(f"'projectSkill' ({skill}) has no SKILL.md")
    prefixes = require("ticketPrefixes", list)
    if prefixes:
        if not all(isinstance(p, str) for p in prefixes):
            errors.append("'ticketPrefixes' items must all be strings")
    elif prefixes is not None:
        errors.append("'ticketPrefixes' must be a non-empty list")

    has_api = "api" in data
    has_surfaces = "surfaces" in data
    if not has_api and not has_surfaces:
        errors.append(
            "neither 'api' nor 'surfaces' present — routing-qa-tickets has no "
            "signal to classify this product at all"
        )

    if has_api:
        api = data["api"]
        if not isinstance(api, dict):
            errors.append("'api' must be an object")
        else:
            client = api.get("client")
            if client not in VALID_CLIENTS:
                errors.append(f"'api.client' must be one of {sorted(VALID_CLIENTS)}, got {client!r}")
            for f in ("repo", "collectionPath"):
                if f not in api:
                    errors.append(f"'api.{f}' is required when 'api' is present")
            for f in ("defaultEnvironment", "ticketEnvironment"):
                if f in api and (not isinstance(api[f], str) or not api[f].strip()):
                    errors.append(f"'api.{f}' must be a non-empty string")
            pub = api.get("publish")
            if pub is not None:
                if not isinstance(pub, dict):
                    errors.append("'api.publish' must be an object")
                else:
                    targets = []
                    for part in ("collection", "environments"):
                        t = pub.get(part, "none")
                        if t not in VALID_PUBLISH_TARGETS:
                            errors.append(f"'api.publish.{part}' must be one of {sorted(VALID_PUBLISH_TARGETS)}, got {t!r}")
                        targets.append(t)
                    if "1password" in targets:
                        op = pub.get("onePassword")
                        if not isinstance(op, dict):
                            errors.append("'api.publish.onePassword' is required when a part goes to 1password")
                        else:
                            for f in ("vault", "collectionItem", "environmentsItem"):
                                part = "collection" if f == "collectionItem" else "environments" if f == "environmentsItem" else None
                                if part and pub.get(part) != "1password":
                                    continue
                                if not isinstance(op.get(f), str) or not op[f].strip():
                                    errors.append(f"'api.publish.onePassword.{f}' is required when a part goes to 1password")
                    if "confluence" in targets and "confluence" not in api:
                        errors.append("'api.confluence' is required when api.publish sends a part to confluence")
            conf = api.get("confluence")
            if conf is not None:
                if not isinstance(conf, dict):
                    errors.append("'api.confluence' must be an object")
                else:
                    for f in ("cloudId", "spaceKey", "parentId", "pageTitle", "attachmentName"):
                        if f not in conf:
                            errors.append(f"'api.confluence.{f}' is required when 'api.confluence' is present")
                    for extra in conf.get("secondaryAttachments", []):
                        if not isinstance(extra, dict) or "name" not in extra or "sourcePath" not in extra:
                            errors.append(
                                "each 'api.confluence.secondaryAttachments[]' entry needs 'name' and 'sourcePath'"
                            )

    if has_surfaces:
        surfaces = data["surfaces"]
        if not isinstance(surfaces, dict) or not surfaces:
            errors.append("'surfaces' must be a non-empty object")
        else:
            for name, surface in surfaces.items():
                if not isinstance(surface, dict):
                    errors.append(f"'surfaces.{name}' must be an object")
                    continue
                if "platform" in surface:
                    # Mobile surface: no URL, but installMode must be a known value.
                    mode = surface.get("installMode", "clean")
                    if mode not in VALID_INSTALL_MODES:
                        errors.append(
                            f"'surfaces.{name}.installMode' must be one of "
                            f"{sorted(VALID_INSTALL_MODES)}, got {mode!r}"
                        )
                else:
                    app_url = surface.get("appUrl")
                    if not isinstance(app_url, str) or not app_url.startswith("http"):
                        errors.append(
                            f"'surfaces.{name}.appUrl' must be an http(s) URL string "
                            f"(or set 'platform' for a mobile surface)"
                        )
                if "repo" not in surface:
                    errors.append(f"'surfaces.{name}.repo' is required")

    if "targetBranch" in data:
        tb = data["targetBranch"]
        if not isinstance(tb, str) or not tb.strip():
            errors.append("'targetBranch' must be a non-empty branch name string")

    if "basicAuth" in data:
        ba = data["basicAuth"]
        if not isinstance(ba, dict) or "username" not in ba or "password" not in ba:
            errors.append("'basicAuth' needs 'username' and 'password'")

    if "jira" in data:
        jira = data["jira"]
        if not isinstance(jira, dict):
            errors.append("'jira' must be an object")
        else:
            site = jira.get("site")
            connector = jira.get("connector")
            if not site:
                errors.append("'jira.site' is required when 'jira' is present")
            if not connector:
                errors.append("'jira.connector' is required when 'jira' is present")
            elif connectors is not None:
                mapped = connectors.get(connector)
                if mapped is None:
                    errors.append(
                        f"'jira.connector' names '{connector}', which isn't a key in "
                        f"atlassian-connectors.json's 'connectors' map"
                    )
                elif site and mapped.get("site") != site:
                    errors.append(
                        f"'jira.site' ({site!r}) disagrees with atlassian-connectors.json's "
                        f"mapping for '{connector}' ({mapped.get('site')!r}) — one of the two "
                        f"files is stale"
                    )

    return errors


def check_connectors_file(data):
    errors = []
    connectors = data.get("connectors")
    if not isinstance(connectors, dict) or not connectors:
        errors.append("'connectors' must be a non-empty object")
        return errors, {}
    for name, entry in connectors.items():
        if not isinstance(entry, dict) or "site" not in entry:
            errors.append(f"connectors.{name} needs a 'site' field")
    return errors, connectors


def check_evidence_file(data):
    errors = []
    # 'dir' is optional: evidence goes to each product's workDir, and 'dir' is only
    # the fallback for runs that match no product config.
    if "dir" in data:
        folder = data["dir"]
        if not isinstance(folder, str) or not folder.strip():
            errors.append("'dir' must be a non-empty path string when present")
    mode = data.get("mode", "auto")
    if mode not in VALID_EVIDENCE_MODES:
        errors.append(f"'mode' must be one of {sorted(VALID_EVIDENCE_MODES)}, got {mode!r}")
    return errors


def main():
    env_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else resolve_environments_dir()
    if not env_dir.is_dir():
        print(f"No environments directory found at {env_dir}")
        return 1

    files = sorted(env_dir.glob("*.json"))
    if not files:
        print(f"No *.json files found under {env_dir}")
        return 0

    connectors_path = env_dir / "atlassian-connectors.json"
    connectors = None
    if connectors_path.exists():
        try:
            connectors_data = load_json(connectors_path)
            conn_errors, connectors = check_connectors_file(connectors_data)
            if conn_errors:
                print(f"{connectors_path.name}:")
                for e in conn_errors:
                    print(f"  - {e}")
        except json.JSONDecodeError as e:
            print(f"{connectors_path.name}: invalid JSON — {e}")

    any_errors = False
    evidence_path = env_dir / "evidence.json"
    if evidence_path.exists():
        try:
            evidence_errors = check_evidence_file(load_json(evidence_path))
        except json.JSONDecodeError as e:
            evidence_errors = [f"invalid JSON — {e}"]
        if evidence_errors:
            any_errors = True
            print(f"{evidence_path.name}:")
            for e in evidence_errors:
                print(f"  - {e}")
        else:
            print(f"{evidence_path.name}: ok")

    for path in files:
        if path.name in META_FILES:
            continue
        if path.is_symlink() and not path.exists():
            # The product's workDir (and its config/) was deleted or moved.
            print(f"{path.name}: dangling symlink to {os.readlink(path)} — remove it (./setup.sh does)")
            any_errors = True
            continue
        try:
            data = load_json(path)
        except json.JSONDecodeError as e:
            print(f"{path.name}: invalid JSON — {e}")
            any_errors = True
            continue
        errors = check_product_config(data, connectors)
        if errors:
            any_errors = True
            print(f"{path.name}:")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"{path.name}: ok")

    return 1 if any_errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# Copyright 2026 Ronny Trommer <ronny@no42.org>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail when a tag filter can select a task without what it depends on.

Two rules, each of which has shipped broken before:

- Registered values (#241): a task reads a variable that a task in the same
  role registers, and the reader carries a tag the registering task lacks. A
  filter on that tag runs the reader, skips the registration, and the reader
  fails on an undefined variable. A reader tagged `always` runs under every
  filter, so it needs a registering task tagged `always` too. Tag the
  registering task `always`.
- Includes (#175, #186): an include_tasks or include_role lacks a tag that a
  task in the included files carries. A dynamic include is entered only when
  its own tags match, so that inner tag selects nothing. Give the include the
  union of the inner tags. `apply:` tags reach the inner tasks but not the
  include itself, so the include still needs them, or `always`.

Reads the task YAML only; nothing is run. A variable counts as read where it
appears in a Jinja expression or a condition key (`when`, `that`, ...), so a
registered name that is also a module or key name is not mistaken for a read.
Known limit: templates, handlers and other roles are not scanned for readers;
no role reads a registered value there today.
"""

import glob
import os
import re
import sys

import yaml

ROLES = "roles"
COLLECTION = "indigo423.opennms."
IGNORED = {"always", "never"}
INCLUDE_TASKS = {"include_tasks", "ansible.builtin.include_tasks"}
INCLUDE_ROLE = {"include_role", "ansible.builtin.include_role"}
BLOCK_KEYS = ("block", "rescue", "always")
# Keys whose values are bare Jinja expressions, without {{ }}.
EXPRESSION_KEYS = {"when", "that", "until", "failed_when", "changed_when", "loop", "with_items"}
JINJA = re.compile(r"\{\{(.*?)\}\}|\{%(.*?)%\}", re.S)
# The os_family dispatch in this collection resolves to these two files only.
FAMILIES = ("Debian", "RedHat")


def tag_set(value):
    """Tags as a set; Ansible accepts a single tag as a plain string."""
    if not value:
        return set()
    return {value} if isinstance(value, str) else set(value)


def walk(tasks, inherited=frozenset()):
    """Yield (task, tags) for every task and every block, blocks with inherited tags.

    A block is yielded too, without its children, because its own `when`,
    `vars` or `loop` read variables like a task does.
    """
    for task in tasks or []:
        if not isinstance(task, dict):
            continue
        tags = tag_set(task.get("tags")) | inherited
        if any(key in task for key in BLOCK_KEYS):
            yield {key: value for key, value in task.items() if key not in BLOCK_KEYS}, tags
            for key in BLOCK_KEYS:
                yield from walk(task.get(key), frozenset(tags))
        else:
            yield task, tags


def load(path):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def task_files(role):
    return sorted(glob.glob(os.path.join(ROLES, role, "tasks", "*.yml")))


def expressions(value, key=None):
    """The Jinja text in a task value: whole values under condition keys,
    {{ }} and {% %} contents everywhere else."""
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from expressions(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from expressions(child, key)
    elif isinstance(value, str):
        if key in EXPRESSION_KEYS:
            yield value
        for match in JINJA.finditer(value):
            yield match.group(1) or match.group(2)


def reads(task, variable):
    body = {key: value for key, value in task.items() if key not in ("name", "tags", "register")}
    pattern = re.compile(r"(?<![\w.])" + re.escape(variable) + r"\b")
    return any(pattern.search(text) for text in expressions(body))


def include_targets(role, name):
    """Files an include_tasks name can resolve to."""
    if "{{" not in name:
        candidates = [name]
    elif "os_family" in name:
        candidates = [re.sub(r"\{\{.*?\}\}", family, name) for family in FAMILIES]
    else:
        pattern = os.path.join(ROLES, role, "tasks", re.sub(r"\{\{.*?\}\}", "*", name))
        candidates = sorted(os.path.basename(path) for path in glob.glob(pattern))
    paths = [os.path.join(ROLES, role, "tasks", candidate) for candidate in candidates]
    return [path for path in paths if os.path.exists(path)]


def local_role(name):
    """The local role an include_role name refers to, or None for another collection's."""
    if name.startswith(COLLECTION):
        name = name[len(COLLECTION):]
    if "." in name or not os.path.isdir(os.path.join(ROLES, name)):
        return None
    return name


def inner_tags(paths):
    tags = set()
    for path in paths:
        for _, task_tags in walk(load(path)):
            tags |= task_tags
    return tags - IGNORED


def check_registered(entries):
    findings = []
    checked = 0
    registered = {}
    for path, task, tags in entries:
        if "register" in task:
            registered.setdefault(task["register"], []).append((path, task, tags))
    for path, task, tags in entries:
        for variable, registrations in registered.items():
            if not reads(task, variable):
                continue
            for reg_path, reg_task, reg_tags in registrations:
                if reg_task is task:
                    continue
                checked += 1
                if "always" in reg_tags:
                    continue
                missing = (tags - reg_tags - IGNORED) | ({"always"} & tags)
                if missing:
                    findings.append(
                        f"{path}: '{task.get('name')}' reads `{variable}`, registered by "
                        f"'{reg_task.get('name')}' ({reg_path}) without tags {sorted(missing)}. "
                        "Tag the registering task `always`."
                    )
    return findings, checked


def check_includes(role, entries):
    findings = []
    checked = 0
    for path, task, tags in entries:
        for key in INCLUDE_TASKS | INCLUDE_ROLE:
            if key not in task:
                continue
            checked += 1
            if "always" in tags:
                continue
            argument = task[key]
            where = f"{path}: '{task.get('name')}'"
            if key in INCLUDE_TASKS:
                name = argument if isinstance(argument, str) else (argument.get("file") or argument.get("_raw_params"))
                targets = include_targets(role, name or "")
                if not targets:
                    findings.append(f"{where} includes `{name}`, which resolves to no file in {ROLES}/{role}/tasks.")
                    continue
                needed = inner_tags(targets)
                what = ", ".join(sorted(os.path.relpath(target, ROLES) for target in targets))
            else:
                name = argument.get("name") if isinstance(argument, dict) else argument
                apply_tags = tag_set((argument.get("apply") or {}).get("tags")) if isinstance(argument, dict) else set()
                target_role = local_role(name)
                if apply_tags:
                    needed = apply_tags - IGNORED
                elif target_role is None:
                    continue  # a role from another collection, without apply tags
                else:
                    needed = inner_tags(task_files(target_role))
                what = f"role {name}"
            missing = needed - tags
            if missing:
                findings.append(
                    f"{where} includes {what} without tags {sorted(missing)} used inside it. "
                    "Add them to the include."
                )
    return findings, checked


def main():
    roles = sorted(os.path.basename(path) for path in glob.glob(os.path.join(ROLES, "*")) if os.path.isdir(path))
    if not roles:
        print(f"::error::No roles found under {ROLES}/; run from the repository root.")
        return 1
    findings = []
    checked = 0
    for role in roles:
        entries = [(path, task, tags) for path in task_files(role) for task, tags in walk(load(path))]
        for check in (check_registered(entries), check_includes(role, entries)):
            findings += check[0]
            checked += check[1]
    for finding in findings:
        print(finding)
    print(f"Checked {checked} reads and includes in {len(roles)} roles: {len(findings)} unreachable under a tag filter.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

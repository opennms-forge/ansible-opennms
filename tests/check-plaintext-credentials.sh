#!/usr/bin/env sh
# Copyright 2026 Ronny Trommer <ronny@no42.org>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Fails if historical or common-placeholder credentials appear in role defaults
# or committed group_vars. Uses git ls-files so only tracked files are scanned,
# and fails explicitly when the scope matches zero files, which would otherwise
# hide a regression after a layout change.
set -eu

files=$(git ls-files \
  'roles/*/defaults/*.yml' 'roles/*/defaults/*.yaml' \
  'inventory/group_vars/*.yml' 'inventory/group_vars/*.yaml' \
  'inventory/group_vars/**/*.yml' 'inventory/group_vars/**/*.yaml' \
  2>/dev/null)
if [ -z "$files" ]; then
  echo "::error::Credential regression check matched zero files."
  echo "The repository layout may have drifted; update the scope in $0."
  exit 1
fi

# Historical defaults plus common placeholder strings that operators should
# never commit. Case-insensitive. The leading `^[[:space:]]*[^#[:space:]]`
# restricts matches to non-comment lines, so commented documentation examples
# are not false positives.
matches=$(echo "$files" | xargs grep -niE \
  '^[[:space:]]*[^#[:space:]].*(p4a55word|oth3rP455w0rd|changeme|password123|admin1234|secret123|defaultpw)' \
  2>/dev/null || true)
if [ -n "$matches" ]; then
  echo "::error::Plaintext credential detected in committed files:"
  echo "$matches"
  echo "Run indigo423.opennms.init_secrets and use vault references instead."
  exit 1
fi
echo "no plaintext credentials in $(echo "$files" | wc -l | tr -d ' ') files"

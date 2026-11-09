#!/bin/sh
# Validate the flat public skill catalog with the pinned Agent Skills reference CLI.
# This is a metadata check, not a security audit or a behavioral evaluation.
set -eu

if [ "$#" -gt 1 ]; then
    printf '%s\n' 'Usage: sh scripts/check-skills.sh [skill-container-directory]' >&2
    exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
catalog=${1:-"$script_dir/../skills"}
if [ ! -d "$catalog" ]; then
    printf 'check-skills: catalog does not exist: %s\n' "$catalog" >&2
    exit 2
fi
catalog=$(CDPATH= cd -- "$catalog" && pwd -P)
validator='git+https://github.com/agentskills/agentskills.git@83021e2be457a9b6679148719c1f6074f0ad975e#subdirectory=skills-ref'

# Run tools from our scripts directory, not from a skill being inspected.
cd -- "$script_dir"
checked=0
errors=0
for skill in "$catalog"/* "$catalog"/.[!.]* "$catalog"/..?*; do
    if [ ! -e "$skill" ] && [ ! -L "$skill" ]; then
        continue
    fi
    if [ -L "$skill" ]; then
        printf 'check-skills: symlink is not a standalone public bundle: %s\n' "$skill" >&2
        errors=$((errors + 1))
        continue
    fi
    [ -d "$skill" ] || continue
    if [ ! -f "$skill/SKILL.md" ]; then
        printf 'check-skills: missing SKILL.md: %s\n' "$skill" >&2
        errors=$((errors + 1))
        continue
    fi
    if ! command -v uvx >/dev/null 2>&1; then
        printf '%s\n' 'check-skills: uvx is required; install uv from https://docs.astral.sh/uv/.' >&2
        exit 2
    fi
    checked=$((checked + 1))
    printf 'check-skills: validating %s\n' "$skill"
    if uvx --no-env-file --from "$validator" skills-ref validate "$skill"; then
        :
    else
        errors=$((errors + 1))
    fi
done

if [ "$checked" -eq 0 ] && [ "$errors" -eq 0 ]; then
    printf '%s\n' 'check-skills: 0 public skills; nothing to validate.'
else
    printf 'check-skills: %s skills checked; %s errors.\n' "$checked" "$errors"
fi
[ "$errors" -eq 0 ]

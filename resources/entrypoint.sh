#!/bin/sh
set -eu
umask 077

mkdir -p "$CODEX_HOME" "$HOME/workspace"

if [ ! -e "$CODEX_HOME/config.toml" ]; then
    cp /usr/local/share/choir/codex/config.toml "$CODEX_HOME/config.toml"
fi

if [ -n "${CHOIR_INSTRUCTIONS:-}" ]; then
    if [ -e "$CODEX_HOME/AGENTS.md" ]; then
        if ! printf '%s\n' "$CHOIR_INSTRUCTIONS" | cmp -s "$CODEX_HOME/AGENTS.md" -; then
            echo 'Persona instructions already exist. Omit CHOIR_INSTRUCTIONS or edit AGENTS.md explicitly.' >&2
            exit 1
        fi
    else
        printf '%s\n' "$CHOIR_INSTRUCTIONS" > "$CODEX_HOME/AGENTS.md"
    fi
fi

unset CHOIR_INSTRUCTIONS
cd "$HOME/workspace"
exec "$@"

# shellcheck shell=sh
# Source from Bash or Zsh after any other runtime managers.
fleet_dir=${FLEET_HOME:-"$HOME/.local/share/fleet"}
# Homebrew's PostgreSQL client is keg-only. Prefer an existing psql if available.
if ! command -v psql >/dev/null 2>&1; then
  for fleet_pg_bin in /opt/homebrew/opt/libpq/bin /usr/local/opt/libpq/bin; do
    if [ -x "$fleet_pg_bin/psql" ]; then
      PATH="$fleet_pg_bin:$PATH"
      break
    fi
  done
fi
for fleet_bin in "$fleet_dir/bin" "$fleet_dir/node/bin" "$fleet_dir/npm/bin"; do
  case ":$PATH:" in
    *":$fleet_bin:"*) ;;
    *) PATH="$fleet_bin:$PATH" ;;
  esac
done
export PATH
unset fleet_bin fleet_dir fleet_pg_bin

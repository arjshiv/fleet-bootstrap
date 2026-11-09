# shellcheck shell=sh
# Source from Bash or Zsh after any other runtime managers.
fleet_dir=${FLEET_HOME:-"$HOME/.local/share/fleet"}
for fleet_bin in "$fleet_dir/bin" "$fleet_dir/node/bin" "$fleet_dir/npm/bin"; do
  case ":$PATH:" in
    *":$fleet_bin:"*) ;;
    *) PATH="$fleet_bin:$PATH" ;;
  esac
done
export PATH
unset fleet_bin fleet_dir

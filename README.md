# Fleet bootstrap

Use this checkout to set up a fresh coding machine or check an existing one. The same terminal tools run on a daily Mac, a stationary Mac, and a headless Linux worker.

| Profile | Installs |
| --- | --- |
| `core` | Git, GitHub CLI, zsh, tmux, jq, ripgrep and the managed tools below. Uses Homebrew on macOS and apt on Ubuntu/Debian. |
| `tools` | Node, pnpm, uv, Codex CLI, Claude Code, agent-browser and Heroku CLI. Installs under your home directory on macOS or glibc Linux, including distros where you supply your own system packages. |
| `desktop` | Mac apps including Edge, Chrome, 1Password, Claude, Cursor and Docker Desktop. Adds ChatGPT and Codex desktop on Apple Silicon, plus Tinycast on macOS 26 or newer. |

The tool profiles target arm64 and x86-64. Use an OS version supported by the underlying packages. Current desktop packages require macOS 14 or newer. Homebrew and apt packages follow their package sources. The versions in `manifests/` pin the managed tool releases, with separate Node checksums for each OS and architecture.

## First run

1. On macOS, install Apple's Command Line Tools with `xcode-select --install` and set up [Homebrew](https://docs.brew.sh/Installation). Follow Homebrew's shell setup instructions. On Ubuntu/Debian, use an account with sudo access for apt. On other glibc Linux distros, install Bash, Git, curl, certificates, tar, coreutils and your terminal tools with the distro package manager, then use the `tools` profile.
2. Get this Git checkout onto the machine, then run the commands below from its root. To reuse the original over Tailscale, run `git clone <ssh-host-alias>:<absolute-path-to-fleet-bootstrap>` after you have SSH access to the host with the original checkout.
3. Add the source line to the end of `~/.zshrc` or `~/.bashrc` after any other runtime managers. This gives the fleet versions precedence in new shells. For a custom install directory, export the same absolute `FLEET_HOME` before running the bootstrap and before sourcing `env.sh`.

```sh
./bootstrap plan
./bootstrap apply
. "$HOME/.local/share/fleet/env.sh"
./bootstrap doctor
```

`plan` prints the selected manifest. `doctor` checks installed versions on the current PATH and exits nonzero if required tools are missing or differ from the pins. The same commands accept `tools` or `desktop` as a second argument. Re-run `apply` after a version change or interrupted install. If a terminated process left an install lock, first check that no bootstrap is running, then remove the stale `.install-lock` inside the managed directory.

On a Mac with a graphical session, run `./bootstrap plan desktop` and `./bootstrap apply desktop` for the desktop apps. Use the standard macOS Terminal app for zsh and tmux. On a headless host, start work inside `tmux new-session -A -s work` to keep the session running when SSH disconnects.

## Shell settings

The tracked [tmux settings](shell/tmux.conf) preserve the existing Ctrl-A prefix, split shortcuts, pane navigation, and status line. On a fresh machine, copy the file to `~/.tmux.conf`. For an existing tmux config, review and merge it.

To get the same zsh look, install [Oh My Zsh](https://ohmyz.sh/#install) and source the tracked [zsh profile](shell/zshrc) from `~/.zshrc`. It selects the existing Robby Russell theme and the portable plugins, plus the macOS-specific plugins on Mac. Add the optional [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md) and [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md) plugins under Oh My Zsh's custom plugins directory. Merge with an existing Oh My Zsh initialization so it loads once.

## Sign in on the machine

- Run `gh auth login`, `codex login`, `claude auth login`, and `heroku login` as needed. Check with `gh auth status`, `codex login status`, `claude auth status`, and `heroku auth:whoami`.
- Sign in to ChatGPT, Codex desktop, Claude, Edge, and 1Password through their apps. Use Edge Sync for your browser preferences. Enable the 1Password app's CLI integration if you use `op`. Grant any desktop automation permissions through macOS when prompted.
- Run `agent-browser install` for a fresh browser, or `agent-browser install --with-deps` when Linux browser libraries are also needed. Then run `agent-browser --session fleet-smoke open about:blank` followed by `agent-browser --session fleet-smoke close`. [Agent-browser installation](https://agent-browser.dev/installation)
- On arm64 Linux, use your distro's Chromium package. On Ubuntu, install it with `sudo snap install chromium`, then run the smoke check with `--executable-path /snap/bin/chromium` before `open`. Set `AGENT_BROWSER_EXECUTABLE_PATH` to the same path if you want it in every session.

Keep machine identities, private SSH keys, login tokens, browser profiles, agent history, and application secrets in their own account or machine storage. Track only reviewed, portable agent settings and skills here.

## Remote access

1. [Install Tailscale](https://tailscale.com/download) and join the same tailnet. Use the new machine's own account and enrollment.
2. On each Mac that will accept connections, enable **System Settings → General → Sharing → Remote Login** for the chosen user. On a Linux worker, install and enable OpenSSH Server. Check the tailnet access policy and the host firewall for the SSH port.
3. Authorize the connecting device's public key on the receiving host, or use your existing 1Password SSH key workflow. Verify the new host's fingerprint before accepting it. Add a local SSH alias using the tailnet hostname, short username, and port, then test `ssh <alias> 'hostname; whoami'` in both directions.
4. Enable macOS Screen Sharing separately if you want GUI access. Test remote access after sleep and restart on whichever machine will stay stationary.

## ResiDesk

Follow the [ResiDesk setup](RESIDESK.md) to clone the worktree and private submodule, supply the dev environment securely, start local PostgreSQL and Valkey, and verify the app. The bootstrap leaves repositories, databases, and background services alone unless you take those separate steps.

Installer references are [Codex CLI](https://github.com/openai/codex), [Claude Code](https://code.claude.com/docs/en/setup), [uv](https://docs.astral.sh/uv/reference/installer/), [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli), and [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile).

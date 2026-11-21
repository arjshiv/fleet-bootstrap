# ResiDesk development

Run the fleet bootstrap and activate its PATH first. Use a checkout with a dev-only environment and local database.

## Clone and bootstrap

Authenticate GitHub CLI with access to both private repositories. The clone uses HTTPS for both the main repo and the submodule.

```sh
gh auth setup-git
git clone --recurse-submodules https://github.com/BrgnTech/Server_Web_Outlook.git
cd Server_Web_Outlook
cat .node-version
node --version
pnpm --version
WORKTREE_SKIP_REBASE=1 WORKTREE_LOCKFILE_MODE=frozen pnpm bootstrap
```

For an existing checkout, use its branch and existing worktree workflow. Check the branch's `.node-version` and `packageManager` before running bootstrap. The current fleet pins match the verified Mac checkout. The optional SkillSpector native Python build can use `uv python install 3.12.8` and `uv venv --python 3.12.8` in its own project directory.

## Local services and dev environment

Reuse existing local PostgreSQL 14 and Valkey services if present. For a fresh machine with Docker Engine and Compose running, use [the local services file](residesk.compose.yaml) from the fleet checkout. The Compose project uses its own volumes and binds the two ports to localhost. Choose the role and database to match the intended dev configuration. Keep the database password in a private local file or secret manager. Before starting Compose, set `FLEET_PG_USER`, `FLEET_PG_DB`, and `FLEET_PG_PASSWORD` through a private env file.

```sh
# Run from the fleet checkout. The env file is outside it and has mode 600.
docker compose --env-file "$HOME/.config/fleet/residesk-db.env" -f residesk.compose.yaml up -d --wait
docker compose --env-file "$HOME/.config/fleet/residesk-db.env" -f residesk.compose.yaml ps
```

Populate the ResiDesk `.env` from the approved dev secret source or transfer it directly from a trusted device over SSH. Set mode 600 and verify `git check-ignore .env`. Point the database and Valkey configuration at the local services. Apply the repository's local database setup and seed steps if your workflow needs application data.

## Smoke check

For production investigation, the fleet's `cursor_prod` service connects to the existing read replica. Run `./bootstrap apply psql` and `./bootstrap doctor psql` from the fleet checkout if it is missing. Then run `bash Database/psql-check.sh` from this checkout before `psql service=cursor_prod`. Keep this access separate from the local development database and use SELECT queries only. The bootstrap does not change the project's `.env`.

From the ResiDesk checkout, start `READONLY_CONTAINER=true SKIP_PROCESS_QUEUE=true NODE_ENV=development pnpm dev`. Open the frontend URL printed by Portless and verify that the backend's `/api/internal/health` and `/mcp/health` return HTTP 200. Stop the dev process after the check. Run feature-specific tests from the repository as needed.

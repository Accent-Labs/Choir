# Choir

Persistent persona agents you can chat with from the ChatGPT app on your iPhone.
Each agent runs in an isolated Linux container with its own home and Codex sandbox.
These examples use [Apple container](https://github.com/apple/container) on macOS;
the image is runtime-agnostic.

## Build

Install Apple container on a supported Apple silicon Mac, clone Choir, and run:

```sh
container system start
container build --platform linux/arm64 --tag choir .
```

Override the Codex version with `--build-arg CODEX_VERSION=<version>`.

## Create and authenticate

Choose a name and instructions. Run in the same shell:

```sh
export CHOIR_HOME="$HOME/.choir"
AGENT=marketing
umask 077
mkdir -p "$CHOIR_HOME/agents/$AGENT"

container run --rm --name "choir-$AGENT" --interactive --tty --cap-drop ALL \
  --mount "type=bind,source=$CHOIR_HOME/agents/$AGENT,target=/home/worker" \
  --env 'CHOIR_INSTRUCTIONS=Help with marketing strategy and draft launch content for review.' \
  choir codex login --device-auth
```

Open the displayed URL and complete login. Device-code login may need enabling
in your [ChatGPT settings](https://learn.chatgpt.com/docs/auth). Configuration,
instructions, and a workspace are created automatically. For an existing agent,
reuse its directory and omit `CHOIR_INSTRUCTIONS`.

## Start, pair, and chat

After the login container exits, start the agent in the background:

```sh
container run --detach --name "choir-$AGENT" --cap-drop ALL \
  --mount "type=bind,source=$CHOIR_HOME/agents/$AGENT,target=/home/worker" \
  choir

container exec "choir-$AGENT" codex remote-control pair
```

The default command runs the Codex app-server in the foreground with remote
control enabled. Pairing connects through a local Unix socket.
If pairing cannot find the server, check `container logs "choir-$AGENT"`;
startup may still be in progress, or authentication may have failed.

In ChatGPT on your iPhone, open Codex/Remote and add a connection using the pairing
code. Use the same account and workspace as the agent. Choose
`/home/worker/workspace` for new tasks, or reopen a saved conversation.
You can now close the terminal or disconnect SSH. Keep the Mac awake and online;
no ports need publishing. Remote control is experimental.
The app-server’s `--remote-control` flag is internal; verify it when upgrading Codex.

To stop: `container stop "choir-$AGENT"`. To restart:
`container start "choir-$AGENT"`. After a Mac reboot, log in and run
`container system start`, then start the agent container. Automatic startup is
not configured. Use one container per agent.

## State and configuration

The agent’s host directory contains `.codex/` (credentials, instructions,
configuration, conversations, and memory) and `workspace/` (documents and task
progress). Memory is enabled per agent; external memory import is disabled.
Memory generation is asynchronous, so save important task progress in files too.

Edit `.codex/AGENTS.md` or `.codex/config.toml` between sessions and restart the
container. Existing files are preserved rather than replaced with image defaults.
Keep this directory and backups private and outside Git; keep secrets out of
`CHOIR_INSTRUCTIONS`.

For [MCPs](https://learn.chatgpt.com/docs/extend/mcp) or approved local plugins,
run the relevant `codex mcp` or `codex plugin` command through `container exec`.
Apps and plugins are disabled by default. Container paths start at `/home/worker`.

Before upgrades, finish work and stop the agent, back up its directory, then
rebuild the image and recreate the container using the same mount. Retain the
previous image and backup for rollback.

# Choir

Long-lived Codex agents with a persistent home per persona. The OCI image works with compatible
container runtimes; these commands use [Apple container](https://github.com/apple/container)
on a supported Apple silicon Mac.

## Setup

Install Apple container and run as your regular user. The image is private; log
in with a GitHub token that has `read:packages`:

```sh
container system start
container registry login ghcr.io
```

To build locally instead, clone this repository, run
`container build --platform linux/arm64 --tag choir .`, and use `choir` as the
image below. Override tool versions with `--build-arg CODEX_VERSION=<version>`
or `--build-arg UV_VERSION=0.13.5`. For an immutable uv image, use
`--build-arg UV_VERSION=0.13.5@sha256:<digest>`.
For a headless Mac mini, enable Remote Login and keep the Mac awake.

## Create and authenticate

Choose an agent name and instructions. Run in the same shell:

```sh
export CHOIR_HOME="$HOME/.choir"
AGENT=marketing
umask 077
mkdir -p "$CHOIR_HOME/agents/$AGENT"

container run --rm --name "choir-$AGENT" --interactive --tty --cap-drop ALL \
  --mount "type=bind,source=$CHOIR_HOME/agents/$AGENT,target=/home/worker" \
  --env 'CHOIR_INSTRUCTIONS=Help with marketing strategy and draft launch content for review.' \
  ghcr.io/accent-labs/choir codex login --device-auth
```

Open the displayed URL in your browser. You may need to enable device-code login
in your [ChatGPT settings](https://learn.chatgpt.com/docs/auth).
Configuration, instructions, and a workspace are created automatically.

## Run and resume

After authentication, start the agent in the background and request a pairing code:

```sh
container run --detach --name "choir-$AGENT" --cap-drop ALL \
  --mount "type=bind,source=$CHOIR_HOME/agents/$AGENT,target=/home/worker" \
  ghcr.io/accent-labs/choir

container exec "choir-$AGENT" codex remote-control pair
```

In ChatGPT on your iPhone, open Codex/Remote and enter the code using the same
account and workspace. Choose `/home/worker/workspace` for new tasks or reopen a
saved conversation. You can disconnect SSH; keep the Mac awake and online.
If pairing fails during startup, check `container logs "choir-$AGENT"` and retry.

Stop with `container stop "choir-$AGENT"`; restart with
`container start "choir-$AGENT"`. After a Mac reboot, log in, set `AGENT` again,
run `container system start`, then start the container. Automatic startup is not
implemented. Use one running container per agent.

Remote control is experimental; recheck the internal app-server
`--remote-control` flag when upgrading Codex.

## Persistent state

Everything lives under `$CHOIR_HOME/agents/$AGENT`:

- `.codex/`: configuration, persona instructions (`AGENTS.md`), credentials,
  conversations, and built-in memory.
- `workspace/`: documents, outputs, and saved task progress. Inside the container,
  this is `/home/worker/workspace`, the default working directory.

Memory generation and use are enabled per agent; external agent memory import
is disabled. Separate agent homes do not automatically share memory with each
other or your personal ChatGPT memory. [Memory generation](https://learn.chatgpt.com/docs/customization/memories)
is asynchronous; keep important task progress in workspace files too.

Keep agent directories and backups private and outside Git. Do not put secrets
in `CHOIR_INSTRUCTIONS`. Removing a container does not remove its mounted home.
Before upgrades, finish tasks, stop the agent, and back up its directory. Pull or
rebuild the image, then remove and recreate the container using the same mount;
restarting it alone does not update the image. Keep the previous image and backup
for rollback.

## Configuration

Edit the agent’s `.codex/config.toml` and `.codex/AGENTS.md` between sessions.
Existing files are never replaced by image defaults. For an existing agent,
enable `features.memories`, `memories.use_memories`, and
`memories.generate_memories` in its configuration; leave
`features.external_agent_memory_import = false`.

Account apps, plugins, and bundled skills are disabled by default. To configure
[MCP servers](https://learn.chatgpt.com/docs/extend/mcp) or reviewed
[local plugins](https://developers.openai.com/plugins/build/plugins), run the
appropriate command via `container exec "choir-$AGENT" codex mcp` or
`container exec "choir-$AGENT" codex plugin`.
Local plugins also require `features.plugins = true`. Use container paths when
configuring tools; the agent home is `/home/worker`.

Python, uv, and Node/npm are available for optional per-agent integrations.
See [Integrations](docs/integrations.md) for explicit installation, MCP
configuration, authentication, validation, and upgrade instructions.

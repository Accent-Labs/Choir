# Choir

Long-lived Codex agents with a persistent home per persona. The Linux image is
runtime-agnostic. The `choir` CLI uses [Apple container](https://github.com/apple/container)
on macOS and Docker on Linux. Set `CHOIR_RUNTIME=docker` to use Docker on a Mac.

## Setup

Install Apple container, clone this repository, and run as your regular user.
The image is private; log in with a GitHub token that has `read:packages`:

```sh
export PATH="$PWD/bin:$PATH"
container system start
container registry login ghcr.io
```

Run these commands from the repository root. Add its `bin/` directory to your
shell PATH to use `choir` elsewhere. Agent homes default to `$HOME/.choir/agents/`;
set `CHOIR_HOME` to an absolute path to use another location. Names are machine-wide;
use the same `CHOIR_HOME` for all commands.

To build locally, run `container build --platform linux/arm64 --tag choir .` and
`export CHOIR_IMAGE=choir`. Override the Codex pin with `--build-arg CODEX_VERSION=<version>`.
For Docker, start your Docker engine and use `docker login ghcr.io` instead.
The published image is ARM64-only. On x86, build with `docker build -t choir .`
and `export CHOIR_IMAGE=choir` before creating an agent. Docker runs containers
with your host UID/GID so the agent home stays writable; run Choir as a normal user.
For a headless Mac mini, enable Remote Login and keep the Mac awake.

## Create and authenticate

Choose a name and instructions:

```sh
choir create marketing --instructions "Help with marketing strategy and draft launch content for review."
choir login marketing
```

Open the displayed URL in your browser. You may need to enable device-code login
in your [ChatGPT settings](https://learn.chatgpt.com/docs/auth).
Configuration, instructions, and a workspace are created automatically.

## Run and resume

After authentication, start the agent in the background and request a pairing code:

```sh
choir start marketing
choir pair marketing
```

In ChatGPT on your iPhone, open Codex/Remote and enter the code using the same
account and workspace. Choose `/home/worker/workspace` for new tasks or reopen a
saved conversation. You can disconnect SSH; keep the Mac awake and online.
If pairing fails during startup, check `container logs choir-marketing` and retry.

Stop with `container stop choir-marketing`; restart with `choir start marketing`.
After a reboot, start Apple container or your Docker engine, then run
`choir start marketing`. Automatic startup is not implemented. With Docker,
substitute `docker` for the direct `container stop`, `logs`, and `exec` commands.
Use one running container per agent.

Remote control is experimental; recheck the internal app-server
`--remote-control` flag when upgrading Codex.

## Persistent state

Everything lives under `$HOME/.choir/agents/marketing` (or your `CHOIR_HOME`):

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
appropriate command via `container exec choir-marketing codex mcp` or
`container exec choir-marketing codex plugin`.
Local plugins also require `features.plugins = true`. Use container paths when
configuring tools; the agent home is `/home/worker`.

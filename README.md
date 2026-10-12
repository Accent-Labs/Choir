# Choir

Long-lived Codex agents with a persistent home per persona. The Linux image is
runtime-agnostic; these commands use [Apple container](https://github.com/apple/container)
on a supported Apple silicon Mac.

## Build

Install Apple container, clone this repository, and run as your regular user:

```sh
container system start
container build --platform linux/arm64 --tag choir .
```

Override the Dockerfile’s Codex pin with `--build-arg CODEX_VERSION=<version>`.
For a headless Mac mini, enable Remote Login and keep the Mac awake.

### Prebuilt image

Instead of building, pull the image that CI publishes to GitHub Container
Registry on every push to `main` (`latest`, `sha-<commit>`) and `v*` tag. The
package is private: log in with your GitHub username and a personal access token
with `read:packages`, then pull and tag it as `choir`:

```sh
container registry login ghcr.io
container image pull ghcr.io/accent-labs/choir:latest
container image tag ghcr.io/accent-labs/choir:latest choir
```

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
  choir codex login --device-auth
```

Open the displayed URL in your browser. You may need to enable device-code login
in your [ChatGPT settings](https://learn.chatgpt.com/docs/auth).
Configuration, instructions, and a workspace are created automatically.

## Run and resume

Start a conversation and enter your task:

```sh
container run --rm --name "choir-$AGENT" --interactive --tty --cap-drop ALL \
  --mount "type=bind,source=$CHOIR_HOME/agents/$AGENT,target=/home/worker" \
  choir
```

To continue a saved conversation, append `codex resume --strict-config` after
`choir`. After restarting the Mac, log in, set `CHOIR_HOME` and `AGENT` again,
start `container system start`, and resume. Automatic startup is not implemented.
Use one running container per agent.

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
Before upgrades, finish tasks and back up the agent directory; rebuild and reuse
the same mount. Keep the previous image and backup for rollback.

## Configuration

Edit the agent’s `.codex/config.toml` and `.codex/AGENTS.md` between sessions.
Existing files are never replaced by image defaults. For an existing agent,
enable `features.memories`, `memories.use_memories`, and
`memories.generate_memories` in its configuration; leave
`features.external_agent_memory_import = false`.

Account apps, plugins, and bundled skills are disabled by default. To configure
[MCP servers](https://learn.chatgpt.com/docs/extend/mcp) or reviewed
[local plugins](https://developers.openai.com/plugins/build/plugins), append the
appropriate `codex mcp` or `codex plugin` command to the same run invocation.
Local plugins also require `features.plugins = true`. Use container paths when
configuring tools; the agent home is `/home/worker`.

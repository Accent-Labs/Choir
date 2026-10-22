# Per-agent integrations

Choir includes Python, uv, and Node/npm. Provider packages are optional and
installed explicitly in each agent's mounted home. Startup never installs them.
Use existing Codex MCP configuration; no Choir-specific manifest is required.

## Install selected tools

First upgrade/recreate the agent with the current Choir image following the
[README](../README.md). Finish active tasks before changing tools or configuration.
Run installation commands on the host, targeting the intended agent:

```sh
AGENT=marketing
container exec "choir-$AGENT" uv tool install --python /usr/bin/python3 'analytics-mcp==0.7.0'
container exec "choir-$AGENT" uv tool install --python /usr/bin/python3 'google-ads-mcp==0.0.5'
container exec "choir-$AGENT" uv tool list
```

These Google versions are examples, not a claim of verified connectivity.
Review the upstream packages before installing. Installs require network access.
Each Python tool has a separate environment under
`/home/worker/.local/share/uv/tools`, with executables in
`/home/worker/.local/bin`. Both persist in the existing home mount.
The image disables automatic Python downloads; an incompatible Python
requirement should fail instead of silently introducing another interpreter.

The same approach works for other Python CLI-based MCP servers. Remote HTTP
servers need no local package installation. Node packages can use the existing
npm runtime with an explicit user-owned prefix and pinned version.

## Authenticate Google

Follow the official [Analytics](https://github.com/googleanalytics/google-analytics-mcp)
and [Ads](https://github.com/googleads/google-ads-mcp) setup instructions.
Enable the Analytics Admin API, Analytics Data API, and Google Ads API in your
Google Cloud project. Authenticate an identity with access to the intended
accounts. For ADC user login, use your own OAuth client and a dedicated host
gcloud configuration directory to avoid replacing unrelated credentials.
The documented scopes are `analytics.readonly`, `adwords`, and `cloud-platform`.

Provision the ADC file privately at
`/home/worker/.config/google/marketing-adc.json` inside the container
(host: `$CHOIR_HOME/agents/$AGENT/.config/google/marketing-adc.json`).
Use mode 0700 for its directory and 0600 for the file; verify the worker can read
it without printing its contents. Complete browser consent yourself.
If your Ads setup requires a developer token, supply
`GOOGLE_ADS_DEVELOPER_TOKEN` to the long-running container through private
environment provisioning when recreating it. Setting it only in a later
`container exec` process does not change the already-running Codex environment.
Keep secrets out of image layers, Git, command literals, and agent instructions.

The agent can read credentials in its home and environment. Separate Python
environments isolate dependencies, not secrets or OS access. Use account
permissions to restrict access; the Ads OAuth scope is broader than reporting.

## Configure MCP

Merge the following into the intended agent's existing
`/home/worker/.codex/config.toml`; do not replace existing settings.
Replace the project placeholder and set a manager ID only when needed:

```toml
[mcp_servers.google_analytics]
command = "/home/worker/.local/bin/analytics-mcp"

[mcp_servers.google_analytics.env]
GOOGLE_APPLICATION_CREDENTIALS = "/home/worker/.config/google/marketing-adc.json"
GOOGLE_PROJECT_ID = "YOUR_PROJECT_ID"

[mcp_servers.google_ads]
command = "/home/worker/.local/bin/google-ads-mcp"
env_vars = ["GOOGLE_ADS_DEVELOPER_TOKEN"]

[mcp_servers.google_ads.env]
GOOGLE_APPLICATION_CREDENTIALS = "/home/worker/.config/google/marketing-adc.json"
GOOGLE_PROJECT_ID = "YOUR_PROJECT_ID"
# GOOGLE_ADS_LOGIN_CUSTOMER_ID = "MANAGER_ID_WITHOUT_DASHES"
```

Restart the agent between sessions after updating configuration. Absolute
container paths avoid host PATH assumptions. These entries are local MCP
configuration; enabling account apps or plugins is unnecessary.
See [Codex MCP configuration](https://developers.openai.com/codex/mcp/).

## Validate before relying on reports

1. Check `container exec "choir-$AGENT" codex mcp list` for registration.
2. In a new agent session, verify both servers initialize and expose tools.
   Registration alone does not prove the MCP handshake or authentication.
3. Discover accessible Ads accounts and Analytics properties. Select the
   intended account/property explicitly and run one small report from each.
4. Record verified IDs, currency, timezone, and conversion definitions in
   the agent's instructions. Check that access still works after restarting
   and after recreating the container with its existing home.

Google Ads MCP documents reporting tools; campaign/budget mutation is not
provided by this example. Google Search Console can be added independently
for organic search; additional platforms do not require rebuilding Choir.

The repository CI checks generic runtimes and offline Codex startup. It does
not install these Google packages or validate personal accounts.

## Upgrade, remove, and roll back

Record `uv tool list`, the image reference, and configuration before changes.
Stop the agent and privately back up its home as described in the README.
Install an explicitly selected replacement version between sessions, then
repeat the validation above. Avoid unpinned installs or automatic upgrades.

Tool environments reference their Python interpreter. When changing the base
Python major/minor version or interpreter path, reinstall each pinned tool with
`uv tool install --reinstall --python /usr/bin/python3 'PACKAGE==VERSION'`.
A top-level version pin does not lock transitive dependencies. For exact
reproduction, retain the previous image and matching home backup, or use a
separately locked integration deployment. Restoring an old home backup also
reverts conversations and other changes made since that backup.

To remove an integration, first disable/remove its MCP entry between sessions,
then run `uv tool uninstall PACKAGE` in the agent. Handle credential revocation
separately, checking whether other integrations share those credentials.

## Shared hosting

For a future hosted deployment, run independently versioned integration
services over authenticated Streamable HTTP with separate credential contexts
per user/account. A shared server configured with one Google identity is not
multi-user isolation. Keep provider credentials in the service and give the
agent only scoped service access. This architecture is not implemented here;
no gateway, host container socket, or HTTP bridge is added.

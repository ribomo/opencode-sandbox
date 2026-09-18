# opencode-sandbox

`opencode-sandbox` launches `opencode` inside a small Bubblewrap sandbox for Linux.

It is a small Bash wrapper that:

- uses the current directory as the writable project root,
- stores sandbox state under `./.sandbox`,
- keeps host network access enabled,
- uses a private in-sandbox server for OpenCode V2 clients,
- and mounts Node automatically when the resolved `opencode` entrypoint is a Node launcher.

## Why Sandbox Opencode?

Running `opencode` in a sandbox gives it the files it needs for the current project without giving it unrestricted access to the rest of the machine.

This wrapper is useful when you want to:

- avoid accidental reads or writes outside the repo,
- keep generated state in `./.sandbox`,
- reduce the impact of bad commands, broken scripts, or prompt mistakes,
- and make the environment more predictable across Linux machines.

The goal is not perfect isolation. It is a practical safety boundary that keeps day-to-day usage pointed at the project directory instead of the whole host system.

## Requirements

- Linux only
- Bubblewrap must be installed; check with `command -v bwrap`
- OpenCode V1 or V2 required

Non-Linux platforms are out of scope for this version.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/ribomo/opencode-sandbox/main/install.sh | bash
```

Or with a custom install directory:

```bash
curl -fsSL https://raw.githubusercontent.com/ribomo/opencode-sandbox/main/install.sh | PREFIX=/usr/local/bin bash
```

Then run it from any project:

```bash
opencode-sandbox
```

## Quick Start

Run the wrapper from the project directory you want to expose inside the sandbox:

```bash
opencode-sandbox
```

Run a simple launch check:

```bash
opencode-sandbox --help
```

## Usage

Pass any normal Opencode arguments through the wrapper:

```bash
opencode-sandbox --help
opencode-sandbox run "summarize this repository"
opencode-sandbox api get /api/info
```

### OpenCode V2

V2 normally discovers or starts a detached background service. That service
owns tool execution, and its lifecycle does not fit the sandbox's PID namespace.
The wrapper automatically adds `--standalone` to supported client commands,
including the TUI, `run`, `mini`, and `api`, so their private server runs inside
the sandbox and exits with the client. The wrapper checks the installed version
and identifies supported V2 client commands directly. V1 arguments are passed
through unchanged. If the version cannot be identified, arguments are also
passed through unchanged.

Explicit `--standalone` or `--server` arguments are passed through. When using
`--server`, tools execute on that server; this wrapper only sandboxes the local
client. Service-management commands are passed through as well; a detached
service is not intended to persist after the sandbox exits.

## Behavior

- The current working directory is bind-mounted read-write.
- Sandbox state is written to `./.sandbox`.
- `/usr`, `/etc`, and common system library directories are mounted read-only.
- `/run` is mounted read-only so host runtime files such as DNS resolver state remain available.
- `/mnt/wsl` is mounted read-only when present so WSL's `/etc/resolv.conf` symlink can resolve to `/mnt/wsl/resolv.conf` for DNS.
- The wrapper always shares the host network namespace.
- If the resolved Opencode entrypoint starts with a Node shebang, the wrapper also exposes the matching Node install root.
- `XDG_CONFIG_HOME` is redirected to `./.sandbox/config`, so opencode reads its global config from `./.sandbox/config/opencode/` instead of `~/.config/opencode/`.

## Config behavior

If `~/.config/opencode/` (or `$XDG_CONFIG_HOME/opencode/`) exists, it is
bind-mounted **read-only** at `./.sandbox/config/opencode/`. OpenCode reads your
host configuration directly; the wrapper does not copy or migrate it. Settings
changes and V2 migration must be performed outside the sandbox.

If there is no host config directory, OpenCode uses the writable sandbox-local
config directory instead.

The host OpenCode **data** directory (`$XDG_DATA_HOME/opencode`, defaulting to
`~/.local/share/opencode`) is still mounted read-write when present, sharing
credentials and session history. Cache and state directories remain local to
`.sandbox`.

## Development checks

Run the wrapper regression checks with Python 3:

```bash
python3 -m unittest discover -s tests -v
bash -n opencode-sandbox install.sh
```

## SSH and Git behavior

The sandbox sets up SSH so that `git push`, `git fetch`, and other remote operations work from within the sandbox.

- `GIT_SSH_COMMAND` is set with absolute paths into `.sandbox/home/.ssh` for SSH config and host keys. The `-F` flag skips the host's system SSH config (`/etc/ssh/ssh_config`), which may have broken ownership or permissions in some container/sandbox environments.
- If `~/.ssh/config` exists on the host, it is **bind-mounted read-only** into the sandbox. Otherwise an empty config is created so `-F` has a file to read.
- If `~/.ssh/known_hosts` exists on the host, it is **bind-mounted read-only**, preserving host-key verification state across sandbox runs.
- If `SSH_AUTH_SOCK` is set and points to a valid socket with loaded identities, it is **forwarded** into the sandbox so existing SSH agent connections work.
- If no usable SSH agent is available, the wrapper starts a temporary host-side agent, runs `ssh-add` for the first default key it finds, forwards that agent socket into the sandbox, and stops the temporary agent when Opencode exits.
- Private keys such as `id_ed25519`, `id_ecdsa`, and `id_rsa` are **never mounted** into the sandbox. If no key can be loaded into an agent, SSH-based Git operations fail safely instead of exposing key material.

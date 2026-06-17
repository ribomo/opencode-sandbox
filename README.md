# opencode-sandbox

`opencode-sandbox` launches `opencode` inside a small Bubblewrap sandbox for Linux.

It is a small Bash wrapper that:

- uses the current directory as the writable project root,
- stores sandbox state under `./.sandbox`,
- keeps host network access enabled,
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
- `opencode` required

Non-Linux platforms are out of scope for this version.

## Install

```bash
git clone https://github.com/ribomo/opencode-sandbox.git
cd opencode-sandbox
chmod +x opencode-sandbox
mkdir -p "$HOME/.local/bin"
cp opencode-sandbox "$HOME/.local/bin/opencode-sandbox"
```

Make sure the install destination is on your `PATH` (or adjust the path above), then you can run it from any project:

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
```

## Behavior

- The current working directory is bind-mounted read-write.
- Sandbox state is written to `./.sandbox`.
- `/usr`, `/etc`, and common system library directories are mounted read-only.
- `/run` is mounted read-only so host runtime files such as DNS resolver state remain available.
- The wrapper always shares the host network namespace.
- If the resolved Opencode entrypoint starts with a Node shebang, the wrapper also exposes the matching Node install root.
- `XDG_CONFIG_HOME` is redirected to `./.sandbox/config`, so opencode reads its global config from `./.sandbox/config/opencode/` instead of `~/.config/opencode/`.

## Config behavior

The sandbox creates an isolated config directory at `./.sandbox/config/opencode/` with its own `opencode.jsonc`. This is the writable config that `opencode` sees as its global config (because `XDG_CONFIG_HOME` is set to `./.sandbox/config`).

If `~/.config/opencode/` also exists on the host, it is **bind-mounted read-only** into the sandbox on top of `./.sandbox/config/opencode/`. This means:

- Your real global config (agents, commands, MCP servers, themes, etc.) is visible inside the sandbox.
- You cannot accidentally modify your real config from within the sandbox — the mount is read-only.
- Any config files you write or edit inside the sandbox go to `./.sandbox/config/opencode/` and do not affect the host.

If `~/.config/opencode/` does **not** exist, only the `./.sandbox/config/opencode/` copy is used.

## SSH and Git behavior

The sandbox sets up SSH so that `git push`, `git fetch`, and other remote operations work from within the sandbox.

- `GIT_SSH_COMMAND` is set to `ssh -F ~/.ssh/config -o StrictHostKeyChecking=accept-new`. The `-F` flag skips the host's system SSH config (`/etc/ssh/ssh_config`), which may have broken ownership or permissions in some container/sandbox environments.
- If `~/.ssh/config` exists on the host, it is **bind-mounted read-only** into the sandbox. Otherwise an empty config is created so `-F` has a file to read.
- If `~/.ssh/known_hosts` exists on the host, it is **bind-mounted read-only**, preserving host-key verification state across sandbox runs.
- If `SSH_AUTH_SOCK` is set and points to a valid socket, it is **forwarded** into the sandbox so existing SSH agent connections work.
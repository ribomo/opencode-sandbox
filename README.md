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
cp opencode-sandbox "$HOME/.local/bin/opencode-sandbox"
```

Make sure the install destination is on your `PATH` (or adjust the path above), then you can run it from any project:

```bash
opencode-sandbox
```

## Quick Start

Run the wrapper from the project directory you want to expose inside the sandbox:

```bash
./opencode-sandbox
```

Run a simple launch check:

```bash
./opencode-sandbox --help
```

## Usage

Pass any normal Opencode arguments through the wrapper:

```bash
./opencode-sandbox --help
./opencode-sandbox run "summarize this repository"
```

## Behavior

- The current working directory is bind-mounted read-write.
- Sandbox state is written to `./.sandbox`.
- `/usr`, `/etc`, and common system library directories are mounted read-only.
- `/run` is mounted read-only so host runtime files such as DNS resolver state remain available.
- The wrapper always shares the host network namespace.
- If the resolved Opencode entrypoint starts with a Node shebang, the wrapper also exposes the matching Node install root.
# Claude Code Sandbox

A Docker-based sandbox environment for running Claude Code safely in YOLO mode.

## Prerequisites

- Docker installed and running
- macOS (or Linux/WSL2)

## Setup

### 1. Build the sandbox image

```bash
docker compose build
```

### 2. Add the shell alias

Add this to your `~/.zshrc`:

```bash
alias claude-sandbox="/path/to/claude-sandbox/run_sandbox.sh"
```

Replace `/path/to/claude-sandbox` with the actual path to this repository.

Then reload your shell:

```bash
source ~/.zshrc
```

### 3. Authenticate (first time only)

Run the sandbox once to authenticate with your Anthropic account:

```bash
claude-sandbox
```

## Usage

Navigate to any project directory and run:

```bash
# Normal mode
claude-sandbox

# YOLO mode (no permission prompts)
claude-sandbox --yolo

# Firewalled mode (restricted network access)
claude-sandbox --firewalled

# YOLO + firewalled
claude-sandbox --yolo --firewalled

# With a prompt
claude-sandbox --yolo -p "fix the tests"

# Pass any claude arguments
claude-sandbox --resume
```

## How it works

- Your current directory is mounted at `/workspaces/<project-name>` inside the container
- Session history is stored in the project's `.claude/sessions/` directory
- Claude Code settings persist between sessions via a Docker volume
- The container runs as non-root user `claude` for safety
- Full network access is available (for web searches, docs, git, etc.)
- Filesystem access is isolated to the mounted directory
- Host services are accessible via `host.docker.internal`
- A global context file (`~/.claude/CLAUDE.md`) informs the agent about the sandbox environment

## Persistence

### User data (Docker volume)

User-level data (credentials, settings, plugins) is stored in a Docker volume `claude-sandbox`,
mounted at `/home/claude/persist` inside the container.

```
claude-sandbox → /home/claude/persist/
├── .claude/            # Claude Code configuration (~/.claude)
│   ├── .credentials.json
│   ├── settings.json
│   ├── CLAUDE.md       # Global agent context
│   └── ...
├── .claude.json        # Onboarding state, theme, user ID
```

The Dockerfile creates symlinks so Claude Code finds its config in the expected locations:

- `~/.claude` → `~/persist/.claude`
- `~/.claude.json` → `~/persist/.claude.json`

This ensures authentication, settings, and onboarding state persist across container restarts and
image rebuilds.

### Session data (per-project)

Session data (conversation history, per-project state) is stored in the project directory at
`.claude/sessions/`. This is bind-mounted into the container so sessions persist and are tied to the
project, not the sandbox.

### Managing the volume

```bash
# Access volume's contents
docker run --rm -it -v claude-sandbox:/data -w /data alpine sh

# Backup the volume
docker run --rm -v claude-sandbox:/data -v $(pwd):/backup alpine tar -czf /backup/claude-sandbox-bkp.tgz -C /data .

# Restore from backup
docker run --rm -v claude-sandbox:/data -v $(pwd):/backup alpine tar -xzf /backup/claude-sandbox-bkp.tgz -C /data

# Remove the volume
docker volume rm claude-sandbox
```

## Network restrictions

Use the `--firewalled` flag to restrict network access to essential domains only:

- Anthropic API (api.anthropic.com, claude.ai)
- JavaScript/TypeScript (npm, Yarn, nodejs.org)
- Rust (crates.io, docs.rs, rust-lang.org)
- GitHub

This reduces the risk of data exfiltration to unauthorized servers while still allowing Claude to
fetch docs and install packages.

## Project structure

```
claude-sandbox/
├── README.md
├── docker-compose.yml
├── run_sandbox.sh              # Main entry point script
└── sandbox/
    ├── agent-context.md        # Global context for the sandboxed agent
    ├── Dockerfile
    ├── entrypoint.sh
    └── init-firewall.sh
```

# Copilot LLM Council

A Python-based orchestration system that leverages GitHub Copilot CLI to create multi-agent "councils" where different LLM personas deliberate on tasks together.

## Motivation (non-AI)

My motivation behind this was (Andrej Karpathy's LLM Council)[https://github.com/karpathy/llm-council], I figured I might as well do something from vibe coding and everything I need to using CLI, I don't want to go anywhere I just want to be able to do this from my CLI, and simple Copilot. I am too used to using GitHub Copilot and thus found it to be the most easy path to build for me. This is almost completely vibecoded around 4am. I've written the scaffold of the specs that I wanted in terms of what I want it to do with what functionality, but for the rest of the part I let it follow best practices, which I personally never bothered with for hobby projects like ruff / type checking (especially this being Python). This has been a fun exercise and I may use it for more things in my project, especially with the scope of this being in line with controlling data access in terms of MCP Servers / Tool usage etc.

## Overview

Copilot LLM Council allows you to:

- **Assemble councils** of AI agents with different roles (critic, principal engineer, security expert, etc.)
- **Choose deliberation strategies**: parallel, sequential, or multi-round debate
- **Use multiple models**: GPT-5, Claude Sonnet 4, Gemini, and more via Copilot CLI
- **Control tool access**: Fine-grained permissions for each council member
- **Get structured output**: JSON logs with full prompts, responses, and metadata

## Architecture

### How It Works

Each council member is queried via independent `copilot` CLI subprocess calls:

```
copilot --model <model> -p <prompt> --no-color --stream off [tool options]
```

**Important**: Copilot CLI calls are **stateless** - there's no persistent conversation memory between calls. Context is managed by:

1. **System prompts**: Define each member's role and persona (re-sent with every call)
2. **Prompt injection**: For debate/sequential strategies, previous responses are included in the prompt
3. **Session tracking**: All responses are collected and can be referenced in subsequent rounds

This design allows mixing different models (GPT-5, Claude, Gemini) in the same council while maintaining role consistency through explicit context management.

## Installation

### Prerequisites

- Python 3.12+
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line) installed and authenticated
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/copilot-llm-council.git
cd copilot-llm-council

# Install dependencies
uv sync --extra dev

# Verify Copilot CLI is working
copilot --version
```

## Quick Start

```bash
# Run a code review council
uv run council run \
  -c examples/code-review-council.yaml \
  --task "Review this function: def add(a, b): return a + b" \
  --log-file logs/review.log \
  -v

# Run a debate council
uv run council run \
  -c examples/debate-council.yaml \
  --task "Should we migrate from REST to GraphQL?" \
  --log-file logs/debate.log \
  -v
```

## CLI Commands

```bash
# Run a council deliberation
uv run council run -c <config.yaml> --task "Your task here"

# List available predefined roles
uv run council roles

# Create a new council config template
uv run council init -o my-council.yaml

# Validate a council config
uv run council validate -c my-council.yaml
```

### Options

| Flag | Description |
|------|-------------|
| `-c, --config` | Path to council YAML config file (required) |
| `-t, --task` | Task/prompt for the council (required) |
| `-o, --output` | Output file for results (markdown) |
| `-l, --log-file` | Path to log file (also via `COUNCIL_LOG_FILE` env var) |
| `-v, --verbose` | Enable verbose/debug output |

## Configuration

### Council Config File

```yaml
name: code-review-council
description: A council for reviewing code changes
strategy: parallel  # parallel, sequential, or debate
max_rounds: 3       # For debate strategy

members:
  - name: architect
    role: principal_engineer
    model: gpt-5

  - name: security-reviewer
    role: security_expert
    model: claude-sonnet-4
    denied_tools:
      - shell(*)

  - name: critic
    role: critic
    model: gpt-5

logging:
  level: INFO
  format: json
```

### Strategies

| Strategy | Description |
|----------|-------------|
| `parallel` | All members respond simultaneously to the task |
| `sequential` | Members respond one after another, each seeing previous responses |
| `debate` | Multiple rounds where members respond to each other's arguments |

### Predefined Roles

| Role | Description |
|------|-------------|
| `critic` | Identifies flaws, bugs, and edge cases |
| `principal_engineer` | Provides architectural guidance and best practices |
| `security_expert` | Identifies vulnerabilities and recommends hardening |
| `data_scientist` | Focuses on data, ML, and statistical approaches |
| `product_manager` | Considers user needs and business requirements |
| `devil_advocate` | Challenges assumptions and presents counterarguments |
| `synthesizer` | Combines and reconciles different perspectives |
| `researcher` | Gathers context and explores alternatives |

### Available Models

Via Copilot CLI:
- `gpt-5`, `gpt-5.1`
- `claude-sonnet-4`, `claude-sonnet-4.5`, `claude-haiku-4.5`
- `gemini-3-pro-preview`

## Logging

Logs are written in JSON format with full request/response details:

```bash
# Enable verbose logging to a file
uv run council run -c config.yaml --task "..." --log-file logs/council.log -v
```

Log files include:
- Timestamps and session IDs
- Full prompts and system prompts sent to each member
- Complete responses with content and raw output
- **Raw CLI commands and responses** for debugging
- Token counts and timing information
- Validation status and errors

### Log Fields

| Field | Description |
|-------|-------------|
| `session_id` | Unique session identifier |
| `member_name` | Council member name |
| `role` | Member's role (critic, principal_engineer, etc.) |
| `model` | LLM model used |
| `prompt` | Full prompt sent to the member |
| `system_prompt` | System prompt defining the role |
| `content` | Parsed response content |
| `raw_output` | Complete raw response |
| `cli_command` | Copilot CLI command (abbreviated) |
| `cli_command_full` | Complete CLI command with full prompt |
| `cli_raw_output` | Raw stdout from Copilot CLI |
| `cli_stderr` | Stderr output (includes usage stats) |
| `cli_returncode` | CLI exit code (0 = success) |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `COUNCIL_LOG_FILE` | Default log file path |
| `COUNCIL_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `COPILOT_MODEL` | Default model for council members |

## Examples

### Code Review Council

```yaml
# examples/code-review-council.yaml
name: code-review-council
strategy: parallel
members:
  - name: architect
    role: principal_engineer
    model: gpt-5
  - name: security-reviewer
    role: security_expert
    model: claude-sonnet-4
  - name: critic
    role: critic
    model: gpt-5
```

### Debate Council

```yaml
# examples/debate-council.yaml
name: debate-council
strategy: debate
max_rounds: 3
members:
  - name: problem-solver
    role: principal_engineer
    model: gpt-5
  - name: devils-advocate
    role: devil_advocate
    model: claude-sonnet-4
  - name: synthesizer
    role: synthesizer
    model: gpt-5
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/unit -v

# Run with coverage
uv run pytest tests/unit --cov=copilot_council

# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy src/

# Install pre-commit hooks
uv run pre-commit install
```

## Project Structure

```
copilot-llm-council/
├── src/copilot_council/
│   ├── adapters/
│   │   └── copilot.py       # Copilot CLI subprocess adapter
│   ├── config/
│   │   ├── loader.py        # YAML config loading
│   │   └── schema.py        # Pydantic config models
│   ├── models/
│   │   ├── member.py        # CouncilMember dataclass
│   │   ├── response.py      # Response models
│   │   ├── role.py          # Role definition
│   │   └── session.py       # Session tracking
│   ├── roles/
│   │   └── predefined.py    # Built-in role definitions
│   ├── strategies/
│   │   ├── base.py          # Abstract strategy class
│   │   ├── debate.py        # Multi-round debate
│   │   ├── parallel.py      # Parallel execution
│   │   └── sequential.py    # Sequential with context
│   ├── cli.py               # Click CLI
│   ├── council.py           # Main Council orchestrator
│   ├── exceptions.py        # Custom exceptions
│   └── logging.py           # JSON logging with session tracking
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── examples/                # Sample council configs
├── logs/                    # Log output directory
├── pyproject.toml           # Project configuration
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and linting
4. Submit a pull request

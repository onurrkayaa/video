# Claude Code Configuration Reference – Late 2026
**From official documentation: code.claude.com + docs.anthropic.com**
**Last verified:** October 2026

---

## 1. SAVED WORKFLOWS

### File Locations
```
Project-level:  .claude/workflows/<name>.js
User-level:     ~/.claude/workflows/<name>.js
Plugin:         <plugin-root>/workflows/<name>.js (namespaced as /plugin:name)
```

- Project workflows load from every `.claude/workflows/` along the path to repo root
- In monorepo, saves to closest existing `.claude/workflows/`, or creates one at repo root
- User workflows available in every project on this machine
- Plugin workflows namespaced by plugin name

### File Format & Structure

**Required:** `export const meta = { ... }` as first statement

```javascript
export const meta = {
  name: 'audit-routes',                          // kebab-case, required
  description: 'Audit route handlers for auth',  // shown in /workflows view
}

// Optional: declare phases for progress display
export const meta = {
  name: 'release-audit',
  description: '...',
  phases: ['discovery', 'audit', 'verification']  // must match phase() calls
}

// Body: plain JavaScript with top-level await
const files = await agent('List all .ts files under src/routes/', {
  schema: {
    type: 'object',
    required: ['files'],
    properties: { files: { type: 'array', items: { type: 'string' } } }
  }
})

const audits = await pipeline(files.files, file =>
  agent(`Audit ${file} for missing auth.`, { label: file })
)

// Optional: group agents under a named phase
phase('verification')
const verified = await parallel([...])

// Return final result
return audits.filter(Boolean)
```

### Invocation
- **Manual:** `/<name>` at Claude prompt, or `/plugin-name:name` for plugin workflows
- **With arguments:** `/name arg1 arg2` → script reads `args` global as structured data
- **Programmatic:** `agent()`, `pipeline()`, `parallel()`, `phase()`, `log()` (in script body)

### Key Runtime Functions
```javascript
agent(prompt, { schema, label })     // Spawn 1 subagent, returns result or null
pipeline(items, fn)                  // Run fn per item sequentially, returns array
parallel(tasks)                       // Run all tasks concurrently
phase(name)                           // Label following agents in progress view
log(message)                          // Print above phases
```

### Schema Validation
- Schemas are JSON Schema, validated before subagent spawns
- Up to 5 retries on validation failure; set `MAX_STRUCTURED_OUTPUT_RETRIES` to change
- Exit with error on contradiction found or 5 failures

### Sharing & Distribution
- **Direct file:** send `.js` file or `--plugin-url https://...`
- **In plugin:** place under `workflows/` or `experimental.evals` path, include in manifest
- **With project:** commit to `.claude/workflows/`, loads automatically

**Docs:** https://code.claude.com/docs/en/workflows.md

---

## 2. CUSTOM SUBAGENTS

### File Locations & Precedence
```
1. Managed settings (organization-wide, highest priority)
2. CLI flag:         --agent name (current session only)
3. Project:         .claude/agents/*.md
4. User:            ~/.claude/agents/*.md
5. Plugin agents:   <plugin>/agents/*.md
```

- Within each location, all `.md` files load as separate agents
- No precedence order within a location; names must be unique
- Subfolders become part of the agent name

### YAML Frontmatter – Complete Schema

```yaml
---
# REQUIRED
name: code-reviewer              # kebab-case identifier
description: |                   # When to delegate; <1,536 chars (with when_to_use)
  Reviews code for quality and security issues.
  Invoke when user asks for code review or references a PR.

# OPTIONAL: Tool Control
tools: Read, Grep, Glob, Bash   # Comma-separated string OR YAML list
# OR
tools:
  - Read
  - Bash
  - Agent(worker, researcher)    # Restrict spawnable subagents

disallowedTools: Write, Edit     # Tools to deny (all others allowed if omitted)

# OPTIONAL: Context & Model
model: sonnet                    # sonnet, opus, haiku, fable, inherit, inherit-effort
permissionMode: default          # default, acceptEdits, auto, dontAsk, plan
effort: high                     # low, medium, high, xhigh, max (in-process teams only)
omitClaudeMd: false              # Skip loading CLAUDE.md; default false

# OPTIONAL: Memory & Scope
memory: project                  # user, project, or local
isolation: worktree              # Run in isolated git worktree
background: true                 # Default to background; requires v2.1.186+

# OPTIONAL: Skills & MCP
skills:
  - api-conventions
  - error-handling               # Preload skill content
mcpServers:
  - playwright                   # Reference existing server by name
  - deploy-api:                  # OR inline config
      type: stdio
      command: npx
      args: ["-y", "@my/server"]

# OPTIONAL: Execution Limits
maxTurns: 5                      # Max conversation turns before auto-stop

# OPTIONAL: Hooks (run during subagent execution)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"

# OPTIONAL: Advanced
memory: project                  # Cross-session learning in .claude/agent-memory/
---

Your task-specific instructions here. Markdown body, any length.
For context: fork subagents, set context: fork instead.
```

### Frontmatter Field Details

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string | (required) | kebab-case; no spaces, @, :, path separators |
| `description` | string | (required) | Used to decide when to delegate; ≤1,536 chars (combined with `when_to_use`) |
| `when_to_use` | string | "" | Appended to description; use for trigger patterns |
| `tools` | string or list | (all) | Comma-sep string `"Read, Bash"` or YAML list; omit = inherit all tools |
| `disallowedTools` | string or list | (none) | Tools to deny; takes precedence over `tools` |
| `model` | string | (session's model) | sonnet, opus, haiku, fable; `inherit` uses session model |
| `permissionMode` | string | default | default, acceptEdits, auto, dontAsk, plan |
| `effort` | string | (session's effort) | low, medium, high, xhigh, max |
| `maxTurns` | number | 10 | Max turns before auto-stop |
| `memory` | string | local | user, project, or local. Stored in `.claude/agent-memory/<name>/` |
| `omitClaudeMd` | boolean | false | Skip CLAUDE.md load |
| `isolation` | string | (none) | worktree for isolated workspace |
| `background` | boolean | false | Default behavior; subagent runs in foreground unless this is true |
| `skills` | list | [] | Skills to preload (list of skill names) |
| `mcpServers` | list/object | [] | MCP servers for the subagent |
| `hooks` | object | {} | PreToolUse/PostToolUse hooks |

### Tool Control Examples

**Allowlist (only specified tools):**
```yaml
tools: Read, Grep, Glob, Bash
```

**Denylist (all except specified):**
```yaml
disallowedTools: Write, Edit
```

**Restrict spawnable subagents:**
```yaml
tools: Agent(worker, researcher), Read, Bash
# Allows spawning only 'worker' and 'researcher' agents; can't spawn others
```

**MCP tool patterns:**
```yaml
disallowedTools: mcp__github      # Remove all tools from github MCP server
disallowedTools: mcp__github__.*  # Regex: all tools matching pattern
```

### Visibility in Main Session
- **Not in subagent's session:** conversation history, output styles, auto-memory
- **Loads at startup:** custom system prompt, CLAUDE.md, git status snapshot, preloaded skills, sibling roster

### Can Subagents...?
- **Use skills?** Yes – preload via `skills` field or implicitly in project/user scope
- **Spawn subagents?** Yes – declare with `tools: Agent(name)` to restrict which they can spawn
- **See CLAUDE.md?** Yes, unless `omitClaudeMd: true`
- **Have hooks?** Yes – frontmatter `hooks` field, active only during subagent run

### Delegation Hints
- Keep description <200 chars, lead with use case ("Fix code issues" not "Code reviewer")
- Include keywords users would say ("deploy", "review PR", "fix issue #123")
- Set `disable-model-invocation: false` for auto-invoke capability

**Docs:** https://code.claude.com/docs/en/sub-agents.md

---

## 3. HOOKS

### Settings.json Hook Schema

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",              // Tool name or regex; "*" matches all
        "if": "Bash(git *)",            // Optional: permission rule filter
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "args": [],                 // Exec form: args as array
            "timeout": 600,             // Seconds before timeout
            "statusMessage": "Validating...",
            "async": false              // Run without blocking
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint:fix",
            "if": "Write(src/**)"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "node",
            "args": ["${CLAUDE_PROJECT_DIR}/scripts/startup.js"]
          }
        ]
      }
    ]
  },
  "env": {
    "DEBUG": "true",                  // Environment variables for all sessions
    "LOG_LEVEL": "debug"
  }
}
```

### Hook Events

| Event | Fires | Can Block? | Notes |
|-------|-------|-----------|-------|
| `PreToolUse` | Before tool executes | Yes (exit 2) | Can modify input, approve/deny, ask |
| `PostToolUse` | After tool succeeds | No | Can modify output, add context |
| `SessionStart` | At session begin/resume | No | Can inject context, reload skills |
| `SessionEnd` | At session close | No | Cleanup, final logging |
| `UserPromptSubmit` | Before processing input | No | E.g., logging, prep |
| `Stop` | When session stops | No | Cleanup |
| `StopFailure` | On stop failure | No | Logging |
| `TeammateIdle` | Teammate about to idle | Yes (exit 2) | Send feedback, keep working |
| `TaskCreated` | Task being created (teams) | Yes (exit 2) | Validate, prevent creation |
| `TaskCompleted` | Task marked complete (teams) | Yes (exit 2) | Validate completion |

### Hook Input (stdin JSON)

```json
{
  "session_id": "abc123",
  "prompt_id": "uuid-string",
  "transcript_path": "/Users/name/.claude/projects/...",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|auto|dontAsk|bypassPermissions",
  "hook_event_name": "PreToolUse",

  // For PreToolUse/PostToolUse only:
  "tool_name": "Bash",
  "tool_input": {
    "command": "git push"
  },

  // For PostToolUse only:
  "tool_output": "...",

  // For SessionStart only:
  "new_session": true,
  "resumed_session": false
}
```

### Hook Output (stdout JSON)

```json
{
  "continue": true,                          // Or false to prevent action
  "systemMessage": "⚠ Warning text",
  "additionalContext": "Info for Claude",
  "terminalSequence": "\033]777;notify;Title;Body\007",
  
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    
    // For PreToolUse:
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "Why this decision",
    "updatedInput": { "command": "modified command" },
    
    // For PostToolUse:
    "updatedToolOutput": "Modified output text",
    "additionalContext": "Context for Claude",
    
    // For SessionStart:
    "sessionTitle": "custom-title",
    "additionalContext": "Env info",
    "watchPaths": ["/path/to/watch"],
    "reloadSkills": true
  }
}
```

### Exit Codes

| Code | Behavior |
|------|----------|
| `0` | Success – reads JSON from stdout |
| `2` | Blocking error – prevents action (PreToolUse, TeammateIdle, TaskCreated, TaskCompleted) |
| Other | Non-blocking error (varies by event) |

### PreToolUse Block Example

```bash
#!/bin/bash
# Block rm -rf and report decision as JSON

COMMAND=$(jq -r '.tool_input.command' < /dev/stdin)

if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Destructive command blocked by policy"
    }
  }'
  exit 2  # Blocking exit
else
  exit 0  # Allow
fi
```

### Matcher Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `"*"` or omitted | All occurrences | Fires on every event |
| Letters, digits, `_`, `-`, spaces, `\|` | Exact match or list | `Bash` or `Edit\|Write` |
| Other characters | Unanchored regex | `^Notebook`, `mcp__.*__write.*` |

**MCP tool naming:** `mcp__<server>__<tool>`
- `mcp__memory__create_entities` – specific tool
- `mcp__memory__.*` – all tools from server
- `mcp__.*__write.*` – any write tool from any server

### Bash Command `if` Matching

```yaml
if: "Bash(git *)"      # Matches: FOO=bar git push, npm && git push
if: "Bash(rm *)"       # Matches: rm -rf, echo $(rm -rf /), NOT echo $(date)
```

Assignments stripped; subcommands checked; variable expansions checked.

### Environment Variables in Hooks

**In settings.json (apply to all sessions):**
```json
{
  "env": {
    "DEBUG": "true",
    "LOG_LEVEL": "warn"
  }
}
```

**In hooks (passed to hook process):**
```json
{
  "type": "command",
  "command": "my-script.sh",
  "args": ["arg"],
  "env": {
    "HOOK_VAR": "value"  // Hook-specific env vars
  }
}
```

### SessionStart Hook with Context Injection

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "node",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/session-init.js"],
            "env": {
              "SESSION_NAME": "media-production"
            }
          }
        ]
      }
    ]
  }
}
```

**Script writes env vars:**
```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export API_KEY=...' >> "$CLAUDE_ENV_FILE"
fi
```

### PostToolUse Hook Example

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier",
            "args": [
              "--write",
              "${tool_input.file_path}"
            ]
          }
        ]
      }
    ]
  }
}
```

### Hook Applicability

- **Subagents:** Hooks in skills/agents' YAML frontmatter are active **only** while subagent runs
- **Workflow agents:** Inherit all hooks from settings (user + project + plugin)
- **Subagent-spawned hooks:** Removed when subagent completes
- **Global hooks:** `~/.claude/settings.json` hooks apply everywhere
- **Project hooks:** `.claude/settings.json` hooks apply to that project

**Docs:** https://code.claude.com/docs/en/hooks-guide.md  
**Full Reference:** https://code.claude.com/docs/en/hooks.md

---

## 4. SKILLS

### File Locations

```
User-level:    ~/.claude/skills/<name>/SKILL.md
Project-level: .claude/skills/<name>/SKILL.md
```

- User skills available in every project on this machine
- Project skills shared via version control with team
- No org-level default location; use plugins for org-wide sharing

### SKILL.md Frontmatter

```yaml
---
# REQUIRED
name: my-skill
description: |
  Use when analyzing API design patterns or validating endpoint structure.
  Invoke for architecture reviews.

# OPTIONAL
when_to_use: |
  Supplement to description; use for additional trigger patterns.
  Append to description; combined max 1,536 chars.

# OPTIONAL: Tool & Model Control
allowed-tools: Read, Grep, WebFetch
model: haiku
disable-model-invocation: true    # Prevent Claude from auto-invoking
user-invocable: true              # Show in / menu; default true

# OPTIONAL: Progressive Disclosure
context:
  fork: false                      # Run in isolated subagent if true
  agent: Explore                   # Use specific subagent type

# OPTIONAL: Arguments
argument-hint: "[endpoint]"        # Shown as /skill [endpoint]

# OPTIONAL: Hooks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./validate.sh"
---

# Skill Content

Your instructions here. Reference external files for details:

For complete API design guidelines, see [api-reference.md](api-reference.md).
For real-time examples, see [examples.md](examples.md).
```

### Frontmatter Field Reference

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string | (required) | Command name; defaults to directory name |
| `description` | string | (required) | When Claude should invoke; ≤1,536 chars (combined with `when_to_use`) |
| `when_to_use` | string | "" | Appended; use for trigger patterns |
| `allowed-tools` | string | (none) | Comma-sep tools pre-approved without prompts |
| `model` | string | (session's) | haiku, sonnet, opus, fable |
| `disable-model-invocation` | boolean | false | Prevent Claude from running it automatically |
| `user-invocable` | boolean | true | Hide from `/` menu if false (Claude-only) |
| `argument-hint` | string | "" | Shown as `/skill [hint]` |
| `context.fork` | boolean | false | Run in isolated subagent context |
| `context.agent` | string | "" | Subagent type to use (e.g., "Explore") |
| `hooks` | object | {} | PreToolUse/PostToolUse hooks active during skill run |

### Progressive Disclosure Pattern

```markdown
---
name: api-guide
description: API design patterns for this codebase
---

# API Guidelines

Follow these patterns:
- Use RESTful naming
- Return consistent error formats

For details, see [api-reference.md](api-reference.md)
For examples, see [examples.md](examples.md)
```

- Keep SKILL.md concise (~500 words)
- Reference external files: `api-reference.md`, `examples.md`, `references/`
- Detailed docs load only when needed
- `/skill-doctor` command reports unused skills and context costs

### How Skills Appear

**In `/skills` listing:**
- Name (command)
- Description (used for delegation)
- Source (user, project, plugin, claude.ai)
- Visibility (Claude can see it, you can invoke it)

**In model's available-skills list:**
- Description used for auto-invoke decision
- Combined length (description + when_to_use) ≤1,536 chars

### Writing Effective Descriptions

```yaml
# Good: leads with use case, keywords
description: |
  Fix a GitHub issue by its number. Use when:
  - User asks to fix issue #123 or "resolve issue 456"
  - PR title references an issue
  - You need to implement a specific issue

# Poor: vague, no trigger words
description: GitHub issue helper
```

**Docs:** https://code.claude.com/docs/en/skills.md

---

## 5. PLUGINS

### When to Package as a Plugin

**Keep standalone (.claude/) when:**
- Single project, single person
- Changes frequently
- Experimental

**Package as plugin when:**
- Sharing with teammates
- Installing across multiple projects
- Versioning releases
- Publishing to marketplace

### Minimal Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                 # Manifest (required if components exist)
├── skills/
│   └── hello/
│       └── SKILL.md
├── agents/
│   └── reviewer.md
├── hooks/
│   └── hooks.json
└── .mcp.json
```

### Plugin Manifest (plugin.json)

```json
{
  "name": "my-tools",                        // Required: kebab-case
  "displayName": "My Tools",                 // Optional: shown in UI
  "version": "1.0.0",                        // Optional: pins version
  "description": "Deployment and review tools",
  "author": {
    "name": "Team Name",
    "email": "team@example.com",
    "url": "https://example.com"
  },
  "homepage": "https://docs.example.com/my-tools",
  "repository": "https://github.com/example/my-tools",
  "license": "MIT",
  "keywords": ["deployment", "review"],
  "defaultEnabled": true,
  
  // Component paths (default locations if omitted)
  "skills": ["./extra-skills/"],             // Adds to default skills/
  "commands": "./commands/",                 // Replaces default
  "agents": ["./agents/"],
  "hooks": "./config/hooks.json",            // Merges with hooks/hooks.json
  "mcpServers": "./mcp/config.json",         // Merges with .mcp.json
  "lspServers": "./.lsp.json",
  "workflows": "./workflows/",
  "outputStyles": "./output-styles/",
  
  // User configuration
  "userConfig": {
    "api_token": {
      "type": "string",
      "title": "API Token",
      "description": "Your API token",
      "sensitive": true                      // Masked, stored securely
    },
    "environment": {
      "type": "string",
      "title": "Environment",
      "options": ["dev", "staging", "prod"],
      "default": "staging"
    }
  }
}
```

### Hook Configuration (hooks/hooks.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

### MCP Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "my-api": {
      "type": "stdio",
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
      "env": {
        "API_TOKEN": "${user_config.api_token}"
      }
    }
  }
}
```

### Environment Variables in Plugins

| Variable | Value | Use for |
|----------|-------|---------|
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install dir | Scripts, binaries bundled with plugin |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/<id>/` | Persistent state, node_modules, caches |
| `${CLAUDE_PROJECT_DIR}` | Project root | Project-local scripts |
| `${user_config.KEY}` | User config value | MCP servers, LSP servers, exec-form hooks |

### Local Marketplace (.claude-plugin/marketplace.json)

For sharing multiple plugins from one directory:

```json
{
  "plugins": [
    {
      "name": "plugin-one",
      "source": "https://github.com/example/plugin-one",
      "displayName": "Plugin One",
      "description": "..."
    },
    {
      "name": "plugin-two",
      "source": "file:///path/to/plugin-two"
    }
  ]
}
```

Then install with: `claude plugin add-marketplace ./my-marketplace`

### Installing a Local Plugin

**For one session:**
```bash
claude --plugin-dir ./my-plugin
```

**For every session (personal):**
```bash
claude plugin init my-plugin --with skills
# Creates ~/.claude/skills/my-plugin/ as a plugin
```

**For a repository (shared with team):**
```bash
# Create .claude/skills/my-plugin/.claude-plugin/plugin.json manually
# Or copy plugin into .claude/skills/my-plugin/
```

### Component Namespacing

- **Skill:** `/plugin-name:skill-name`
- **Agent:** `plugin-name:agent-name` (reference in spawn)
- **MCP server:** `mcp__plugin_name__server_name__tool_name`
- **Hooks:** No namespace; all match globally

### Commands for Plugin Development

```bash
# Validate manifest and components
claude plugin validate ./my-plugin

# List installed plugins
claude plugin list

# Load plugins from a folder (v2.1.265+)
claude --plugin-dir ./plugins/

# Enable/disable by name
claude plugin enable my-plugin@marketplace
claude plugin disable my-plugin@marketplace

# Watch for changes (reload with /reload-plugins in session)
/reload-plugins
```

**Docs:**
- Plugin creation: https://code.claude.com/docs/en/plugins/create.md
- Manifest reference: https://code.claude.com/docs/en/plugins/manifest-reference.md
- Component layout: https://code.claude.com/docs/en/plugins/components.md

---

## 6. NEW FEATURES: AGENT TEAMS & ADVANCED ORCHESTRATION

### Agent Teams (Experimental, Late 2026)

**Status:** Experimental, disabled by default

**Enable:**
```json
// ~/.claude/settings.json or .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**What they are:**
- Multiple independent Claude Code instances (teammates) working in parallel
- One lead session coordinates work, assigns tasks, synthesizes findings
- Teammates run in separate context windows, communicate via messages and shared task list
- Better than subagents for exploratory work (research, review, competing hypotheses)

**When to use:**
- Research with parallel investigation (competing theories)
- Parallel code review (security, performance, tests → different reviewers)
- Feature development (each teammate owns a module)
- Debugging with hypothesis teams
- Token cost is higher than subagents (each teammate = separate session)

**Display modes:**
```json
{
  "teammateMode": "in-process"  // All in terminal (default)
  // OR
  "teammateMode": "auto"        // Split panes if tmux/iTerm2 available
  // OR
  "teammateMode": "tmux"        // Force tmux split panes
  // OR
  "teammateMode": "iterm2"      // Force iTerm2 (needs it2 CLI)
}
```

**Starting a team:**
```
I'm designing a CLI tool. Spawn three teammates: one on UX, one on 
architecture, one as devil's advocate to challenge ideas.
```

**Configuration as subagent:**
```yaml
---
name: security-reviewer
description: Reviews code for security issues
tools: Read, Grep
model: sonnet
---

Review code focusing on:
- Authentication & authorization
- Input validation
- Cryptography & secrets handling
```

Then spawn: `Spawn a teammate using the security-reviewer agent type to review auth.md`

**Task list & messaging:**
- Lead creates tasks; teammates claim work
- Direct teammate-to-teammate messaging
- Task dependencies enforced automatically
- Hooks: `TeammateIdle`, `TaskCreated`, `TaskCompleted` (can block with exit 2)

**Limitations (v2.1.287+):**
- No resume with in-process teammates (`/resume` doesn't restore them)
- One team per session; no nested teams
- Background subagents can't run from teammates
- Shutdown can be slow
- Task status can lag in rare cases

**Docs:** https://code.claude.com/docs/en/agent-teams.md

---

## 7. SETTINGS.JSON – Key Configuration Blocks

```json
{
  // Model & Effort
  "model": "claude-sonnet-5",
  "effortLevel": "xhigh",
  "ultracode": false,                  // Automatic workflow orchestration

  // Workflow & Agent Sizing
  "workflowSizeGuideline": "medium",   // small, medium, large, unrestricted
  "subagentPromptCacheTtl": "5m",      // 5m default, 1h for subscription

  // Subagent Memory
  "subagentStatusLine": true,          // Show subagent status in prompt

  // Environment Variables (all sessions, all tools)
  "env": {
    "NODE_ENV": "production",
    "DEBUG": "false"
  },

  // Permission Settings
  "permissions": {
    "allow": [
      "Read",
      "Bash(git *)",
      "WebSearch",
      "Workflow(deep-research)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Agent(untrusted)"
    ]
  },

  // Hooks (PreToolUse, PostToolUse, SessionStart, etc.)
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/validate.sh"
          }
        ]
      }
    ]
  },

  // Plugins & Skills
  "enabledPlugins": ["my-tools", "code-review@official"],
  "skillOverrides": {
    "my-skill": "off"
  },
  "pluginConfigs": {
    "my-tools": {
      "api_token": "...",
      "environment": "prod"
    }
  },

  // Workflows
  "disableWorkflows": false,

  // Prompt Cache
  "promptCachingBudgetPercentage": 50
}
```

**Docs:** https://code.claude.com/docs/en/settings-reference.md

---

## 8. CONTEXT & BEST PRACTICES FOR MEDIA PRODUCTION

### Recommended Multi-Agent Setup

```yaml
# .claude/agents/video-architect.md
---
name: video-architect
description: Plans video composition architecture and storyboarding
tools: Read, WebFetch, Agent(design-reviewer)
model: sonnet
when_to_use: >
  Ask to design a video structure, plan shot sequences, or validate composition layouts.
---

# Video Architect System Prompt
You specialize in HyperFrames composition architecture...
For complete spec: [spec.md](spec.md)
For patterns: [patterns.md](patterns.md)

---
# .claude/agents/render-specialist.md
---
name: render-specialist
description: Handles HyperFrames rendering, optimization, and output
tools: Bash, Read, Write, Edit
model: haiku
when_to_use: >
  Optimize render settings, debug build failures, batch export.
---

---
# .claude/skills/media-project-setup/SKILL.md
---
name: media-project-setup
description: Initialize media production workspace with CLAUDE.md, configs, and directory structure
user-invocable: true
---

When setting up a new media project...
For template: [template.md](template.md)
```

### Workflow Example for Media Review

```javascript
// .claude/workflows/video-review.js
export const meta = {
  name: 'video-review',
  description: 'Multi-perspective video review: narrative, tech, design',
  phases: ['review', 'synthesis']
}

phase('review')
const narrative = await agent(
  `Review this video for narrative clarity, pacing, and emotional impact.`,
  { label: 'narrative' }
)
const technical = await agent(
  `Review for audio mixing, color grading, sync, artifacts, compression.`,
  { label: 'technical' }
)
const design = await agent(
  `Review typography, graphics, brand consistency, visual hierarchy.`,
  { label: 'design' }
)

phase('synthesis')
const synthesis = await agent(
  `Synthesize findings from narrative, technical, and design reviews.
   Prioritize issues by severity and impact on final deliverable.`,
  {
    schema: {
      type: 'object',
      properties: {
        critical: { type: 'array', items: { type: 'string' } },
        recommendations: { type: 'array', items: { type: 'string' } },
        timeline: { type: 'string' }
      }
    }
  }
)

return synthesis
```

### Hook for Media Validation

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "if": "Write(src/**/*.json)",
        "hooks": [
          {
            "type": "command",
            "command": "node",
            "args": [
              "${CLAUDE_PROJECT_DIR}/.claude/hooks/validate-composition.js"
            ]
          }
        ]
      }
    ]
  }
}
```

---

## 9. DOCUMENTATION LINKS

| Topic | URL |
|-------|-----|
| Workflows | https://code.claude.com/docs/en/workflows.md |
| Subagents | https://code.claude.com/docs/en/sub-agents.md |
| Agent Teams | https://code.claude.com/docs/en/agent-teams.md |
| Hooks Guide | https://code.claude.com/docs/en/hooks-guide.md |
| Hooks Reference | https://code.claude.com/docs/en/hooks.md |
| Skills | https://code.claude.com/docs/en/skills.md |
| Plugin Creation | https://code.claude.com/docs/en/plugins/create.md |
| Plugin Manifest | https://code.claude.com/docs/en/plugins/manifest-reference.md |
| Plugin Components | https://code.claude.com/docs/en/plugins/components.md |
| Settings Reference | https://code.claude.com/docs/en/settings-reference.md |
| Plugin Eval | https://code.claude.com/docs/en/plugin-evals.md |
| MCP Servers | https://code.claude.com/docs/en/mcp.md |

---

**Model:** Claude Haiku 4.5  
**Version:** Claude Code v2.1.287+ (late 2026)  
**Status:** All features documented, hooks/workflows/agent-teams fully supported

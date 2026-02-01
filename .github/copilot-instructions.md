# Copilot / AI Agent Instructions for PZ Admin Tool

Short, focused guidance to help an AI contributor be productive in this repo.

## Big Picture
- Purpose: GUI-based admin tool for Project Zomboid dedicated servers using RCON.
- Main entry: `pz_admin_tool.py` — single-file Tk GUI + `RCONClient` implementation.
- Docs: `README.md`, `docs/COMMANDS.md`, `docs/INSTALL.md` contain authoritative instructions and examples.

## Key Components & Boundaries
- `pz_admin_tool.py` — UI (Tkinter), connection management, file-based mod/log readers, and RCON logic.
  - `RCONClient` class handles socket, auth, and command packets.
  - `PZServerAdmin` handles the GUI and uses `RCONClient` for all server ops.
- No external Python packages — target environment is Python 3.7+ standard library only.

## Important Project-Specific Patterns
- RCON packet and auth: packets are built with two null terminators. See `RCONClient.connect()` and `execute_command()`.
  - Auth sequence: server may send an empty RESPONSE_VALUE packet first; code reads an extra packet before checking auth ID.
- Password handling: the UI intentionally does NOT strip the password string (do not trim or modify password input when authenticating).
- Server path auto-detection: `auto_detect_path()` searches common Linux paths; prefer using that for tests instead of hardcoding paths.
- Config file: `pz_admin_config.json` stores host/port/server_path but NOT password. Avoid changing that behavior without clear security rationale.

## How to run & debug locally
- Run the app from repo root:

  python3 pz_admin_tool.py

- Run from terminal to see debug prints from `RCONClient` (connect/auth debug messages are printed to stdout).
- To test RCON behavior without the GUI, instantiate `RCONClient(host, port, password)` in a short script and call `connect()` / `execute_command()`.

## Command & quoting conventions
- Commands often require quoted usernames and underscores for server messages: `servermsg "Hello_world"` (UI replaces spaces with underscores).
- Use `docs/COMMANDS.md` as the source of truth for available RCON commands and examples.

## Development constraints & style
- Keep compatibility with Python 3.7+: avoid modern-only stdlib APIs unless backported.
- No new external dependencies unless explicitly justified and approved.
- Keep edits minimal and respectful of the single-file GUI structure — the repo intentionally bundles UI and protocol logic together.

## Useful files to inspect when changing behavior
- `pz_admin_tool.py` — primary implementation and most important to read.
- `docs/COMMANDS.md` — canonical command examples.
- `docs/INSTALL.md` & `README.md` — environment, install, and runtime expectations.
- `setup_github.sh` — shows expected repo initialization and release steps.

## Examples to copy/use in PRs
- Reproduce the RCON auth sequence using the two-null-terminator packet construction as in `RCONClient.connect()`.
- When adding new UI features, use existing `ttk` patterns from `create_widgets()` and other tab creators for consistent look-and-feel.

## Safety notes for agents
- Do not log or persist plaintext passwords. The app intentionally does not save passwords.
- Avoid changing the password handling lines that intentionally avoid trimming. See `connect_to_server()` for `password = self.password_entry.get()`.

If anything here is unclear or you want more examples (tests, small runnable snippets, or a refactor plan), tell me which area to expand.

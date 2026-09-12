# Canvas-to-Code Bridge — Opencode Build Instructions

## Purpose of this document

This file is a complete, sequential build instruction set for Opencode to execute inside the `canvas-cli` project directory. Follow the steps in order. Do not skip ahead to a later step until the file(s) in the current step exist exactly as specified. Do not add functionality, files, or dependencies that are not named below — if something seems missing, stop and flag it rather than improvising.

No code is written out in this document. Each step names the exact file, its exact path, and the exact behavior that file's contents must implement, described in words. Where a step references "the function starting `def x(...)`" it is only naming an anchor point for that logic — write the full implementation yourself under that definition.

**Assumption**: a Miro Developer App has already been created with `board:read` and `board:write` scopes, and a valid access token plus the target board ID are available to be pasted into a config file. If these do not exist yet, stop before Step 3 and obtain them first — no code in this plan should hold a placeholder secret.

---

## Step 1 — Create the project folder structure

Inside the existing `canvas-cli` directory, create the following empty files and one empty subfolder, with these exact names and this exact nesting. Do not create any additional files at this stage.

```
canvas-cli/
├── bridge.py
├── miro_client.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── expertise.md
└── plans/
    └── current_plan.json
```

Leave every file empty for now except `plans/current_plan.json`, which should contain a single empty JSON object and nothing else.

---

## Step 2 — Populate `requirements.txt`

List exactly three dependencies, one per line, with no version pins: `requests`, `python-dotenv`. Do not add `anthropic` or `openai` — this build has no LLM API dependency; Opencode itself performs the planning step outside this codebase, so the CLI only ever does data movement.

---

## Step 3 — Populate `.env.example` and `.env`

In `.env.example`, write two lines defining the required environment variable names with empty or placeholder values: `MIRO_API_KEY` and `MIRO_BOARD_ID`. This file exists purely as a template that gets committed to version control.

In `.env`, write the same two variable names, but with the real Miro access token and the real board ID as their values. This file must never be committed — if a `.gitignore` file does not already exist in `canvas-cli`, create one and add a single line: `.env`.

---

## Step 4 — Build `config.py`

This file's only job is to load environment variables and expose them to the rest of the codebase as plain Python values, so no other file ever calls `os.environ` or `dotenv` directly.

Write one top-level statement that loads the `.env` file into the process environment.

Then define two module-level constants, named exactly `MIRO_API_KEY` and `MIRO_BOARD_ID`, each read from the corresponding environment variable.

Immediately after both are defined, add a validation check: if either value is missing or empty, raise a `RuntimeError` whose message names which variable is missing and instructs the user to check `.env`. This check must run at import time, not inside a function, so any command that imports `config.py` fails fast and loud rather than failing later with a confusing API error.

---

## Step 5 — Build `miro_client.py`: the read function

This file wraps all direct HTTP communication with the Miro REST API. No other file should construct a Miro API URL or call `requests` directly.

At the top of the file, import `requests` and import the two constants from `config.py`.

Define a module-level constant for the Miro API base URL: `https://api.miro.com/v2`.

Define a function starting `def get_board_items(board_id=None):`. Its job:

- If `board_id` is not passed in, default to the `MIRO_BOARD_ID` constant from config.
- Build the request URL as the base URL plus `/boards/{board_id}/items`, and set the request headers to include an `Authorization` header with the value `Bearer` followed by `MIRO_API_KEY`.
- The Miro items endpoint is paginated (it returns a `cursor` field when more pages exist). Implement a loop that keeps requesting pages, passing the returned cursor as a query parameter on the next request, and stops when no cursor is returned.
- Accumulate every item from every page into a single list.
- For each raw item returned by the API, extract only these fields into a smaller dictionary before adding it to the result list: item id, item type, the text content (this lives in different places in the raw payload depending on item type — sticky notes and text items keep it under a `data` key, shapes may keep it under `data` as well; handle both), and position, meaning the `x` and `y` values found under the item's `position` key.
- If the raw item is a `connector` type, additionally extract the `start_item` id and `end_item` id — connectors don't have a position but do have these linkage fields, and that linkage is important context for planning.
- Return the accumulated list of simplified item dictionaries.
- Wrap the network calls in error handling: if a request returns a non-200 status code, raise a `RuntimeError` that includes the status code and response body text, rather than letting a raw `requests` exception propagate.

---

## Step 6 — Build `miro_client.py`: the write function

In the same file, below the read function, define a function starting `def create_sticky_note(text, x, y, board_id=None):`. Its job:

- Default `board_id` the same way as the read function.
- Build the request URL as the base URL plus `/boards/{board_id}/sticky_notes`.
- Construct the JSON request body according to Miro's sticky note creation schema: a `data` object containing the note's text content, and a `position` object containing the given `x` and `y` coordinates.
- Send the request as a POST with the same `Authorization` header pattern as the read function.
- Apply the same non-200 error handling pattern as the read function.
- Return the JSON response body so the caller can see the newly created item's id.

Below that, define a second function starting `def create_text_item(text, x, y, board_id=None):` that follows the identical pattern but targets the `/boards/{board_id}/texts` endpoint instead, for plain text items rather than sticky notes.

---

## Step 7 — Build `bridge.py`: the CLI entry point

This is the only file that gets executed directly from the command line. It should contain no Miro API logic of its own — it only parses arguments and calls into `miro_client.py`.

At the top, import `argparse`, `json`, and the two functions from `miro_client.py`.

Set up an argument parser with a subcommand structure (`bridge.py <command> [options]`), with exactly two subcommands at this stage: `read` and `write`.

For the `read` subcommand: it should accept an optional `--output` argument (defaulting to `board_content.json`) naming where to save the result. When invoked, it should call the read function from `miro_client.py`, wrap the returned list under a top-level key such as `items`, and write the result as formatted JSON (indented, human-readable) to the output path. After writing, it should print a one-line confirmation to the terminal stating how many items were read and which file they were written to.

For the `write` subcommand: it should accept one required argument, `--plan`, naming a JSON file to read a plan from (defaulting to `plans/current_plan.json` if not given). The expected shape of that plan file is a list of step objects, where each step object has at minimum a title or description field and, optionally, `x` and `y` coordinates. When invoked, it should load that JSON file, iterate over each step in the plan, and call the sticky-note creation function once per step — if a step doesn't specify `x`/`y` coordinates, lay steps out automatically by incrementing the `x` position by a fixed spacing (for example 300 units) for each successive step, keeping `y` constant, so the steps appear left-to-right on the board in order. After all steps are created, print a one-line confirmation stating how many stickies were written to the board.

At the bottom of the file, add the standard `if __name__ == "__main__":` guard that parses arguments and dispatches to the appropriate subcommand's logic.

---

## Step 8 — Populate `expertise.md`

Do not write planning content into this file yet — its content is authored separately by the project owner, not generated by Opencode. Instead, create it with only these section headings and no body text under any of them, so it exists as a fillable template:

- A top-level heading titled "Planning Expertise Profile"
- A second-level heading titled "Role"
- A second-level heading titled "Priorities"
- A second-level heading titled "Anti-Patterns to Avoid"
- A second-level heading titled "Handling Ambiguity"

Leave every section body empty.

---

## Step 9 — Verify the build

Run these checks in order and confirm each one before moving to the next:

1. Install dependencies from `requirements.txt`.
2. Run `bridge.py read` with no arguments and confirm `board_content.json` is created in the project root, is valid JSON, and contains at least one item under its `items` key.
3. Open `board_content.json` and manually confirm that at least one sticky note or text item from the real board appears with readable text content and numeric `x`/`y` position values.
4. Create a two-step test file at `plans/test_plan.json` containing a JSON list of two step objects, each with only a title field, no coordinates.
5. Run `bridge.py write --plan plans/test_plan.json` and confirm the terminal reports two stickies written.
6. Open the actual Miro board and visually confirm two new sticky notes appear, positioned left-to-right.
7. Delete the two test stickies from the board manually, and delete `plans/test_plan.json` — this was a verification-only file, not part of the shipped tool.

Do not consider the build complete until all seven checks pass. If any step fails, fix the responsible file before re-running verification from step 1 of this section — do not patch around a failure by changing the verification steps themselves.

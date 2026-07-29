#!/usr/bin/env node

// Cross-platform Claude Code hook launcher.
// Claude Code documents the `node` + script path exec form as portable across
// platforms. This shim locates Python without passing hook input through a shell.

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const argumentsList = process.argv.slice(2);
const sourceIndex = argumentsList.indexOf("--source");
const source =
  sourceIndex >= 0 && argumentsList[sourceIndex + 1]
    ? argumentsList[sourceIndex + 1]
    : "claude";

let input = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) {
  input += chunk;
}

const pythonScript = fileURLToPath(new URL("./session_alarm.py", import.meta.url));
const candidates =
  process.platform === "win32"
    ? [
        ["py", "-3"],
        ["python", ""],
        ["python3", ""],
      ]
    : [
        ["python3", ""],
        ["python", ""],
      ];

for (const [command, prefix] of candidates) {
  const args = [];
  if (prefix) args.push(prefix);
  args.push(pythonScript, "hook", "--source", source);
  const result = spawnSync(command, args, {
    input,
    encoding: "utf8",
    timeout: 2500,
    windowsHide: true,
  });
  if (result.error?.code === "ENOENT") continue;
  if (result.status === 0 && result.stdout.trim().startsWith("{")) {
    process.stdout.write(result.stdout);
  } else {
    process.stdout.write("{}\n");
  }
  process.exit(0);
}

process.stdout.write("{}\n");


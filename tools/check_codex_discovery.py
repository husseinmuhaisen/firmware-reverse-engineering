#!/usr/bin/env python3
"""Check real Codex plugin discovery without installation or a model request."""

import argparse
import json
from pathlib import Path
import queue
import subprocess
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default="codex", help="Codex executable (tested with 0.153.4)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [args.cli, "app-server", "--stdio"], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    messages = queue.Queue()

    def read_messages():
        for line in process.stdout:
            messages.put(json.loads(line))
        messages.put(None)

    threading.Thread(target=read_messages, daemon=True).start()

    def send(message):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def request(identifier, method, params):
        send({"id": identifier, "method": method, "params": params})
        while True:
            message = messages.get(timeout=30)
            if message is None:
                raise RuntimeError("Codex exited before returning a response")
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message["result"]

    try:
        request(1, "initialize", {
            "clientInfo": {"name": "firmware-packaging-check", "version": "1.0.0"},
            "capabilities": {"experimentalApi": True},
        })
        send({"method": "initialized"})
        plugin = request(2, "plugin/read", {
            "marketplacePath": str(root / ".agents/plugins/marketplace.json"),
            "pluginName": "firmware-reverse-engineering",
        })["plugin"]
        names = {s["name"] for s in plugin["skills"]}
        expected = {
            "firmware-reverse-engineering:" + p.parent.name
            for p in (root / "plugins/firmware-reverse-engineering/skills").glob("*/SKILL.md")
        }
        if len(expected) != 5 or names != expected:
            raise RuntimeError(f"Unexpected skill discovery: {sorted(names)}")
        print("Codex discovered all five plugin skills:")
        print("\n".join(sorted(names)))
        print("No plugin installation or model request was made.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()

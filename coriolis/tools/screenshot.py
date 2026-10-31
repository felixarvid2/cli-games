#!/usr/bin/env python3
"""Render a CORIOLIS curses screen to plain text, for testing and docs.

Runs the real game in a pty, types a key script, and replays the terminal
output through a tiny ANSI parser (CUP / ED / EL / SGR) to reconstruct what
the player would see.

Usage: python3 tools/screenshot.py --keys '\n\n' --wait 0.4 [--size 80x24]
"""
import argparse
import fcntl
import os
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time

CSI = re.compile(r"\x1b\[([0-9;?]*)([@-~])")


class Screen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[" "] * w for _ in range(h)]
        self.x = self.y = 0

    def clear(self):
        self.grid = [[" "] * self.w for _ in range(self.h)]

    def put(self, ch):
        if 0 <= self.y < self.h and 0 <= self.x < self.w:
            self.grid[self.y][self.x] = ch
        self.x += 1
        if self.x >= self.w:
            self.x = 0
            self.y = min(self.h - 1, self.y + 1)

    def feed(self, data):
        i = 0
        text = data.decode("utf-8", "replace")
        while i < len(text):
            ch = text[i]
            if ch == "\x1b":
                m = CSI.match(text, i)
                if m:
                    params, final = m.group(1), m.group(2)
                    self.csi(params, final)
                    i = m.end()
                    continue
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if nxt in "()#%" and i + 2 < len(text):
                    i += 3
                else:
                    i += 2
                continue
            if ch == "\r":
                self.x = 0
            elif ch == "\n":
                self.y = min(self.h - 1, self.y + 1)
            elif ch == "\b":
                self.x = max(0, self.x - 1)
            elif ch >= " ":
                self.put(ch)
            i += 1

    def csi(self, params, final):
        nums = [int(p) for p in params.split(";") if p.isdigit()]
        if final == "H" or final == "f":
            row = nums[0] if nums else 1
            col = nums[1] if len(nums) > 1 else 1
            self.y, self.x = row - 1, col - 1
        elif final == "J":
            mode = nums[0] if nums else 0
            if mode == 2:
                self.clear()
            elif mode == 0:
                for x in range(self.x, self.w):
                    self.grid[self.y][x] = " "
                for y in range(self.y + 1, self.h):
                    self.grid[y] = [" "] * self.w
        elif final == "K":
            mode = nums[0] if nums else 0
            if mode == 2:
                self.grid[self.y] = [" "] * self.w
            else:
                for x in range(self.x, self.w):
                    self.grid[self.y][x] = " "
        elif final == "A":
            self.y = max(0, self.y - (nums[0] if nums else 1))
        elif final == "B":
            self.y = min(self.h - 1, self.y + (nums[0] if nums else 1))
        elif final == "C":
            self.x = min(self.w - 1, self.x + (nums[0] if nums else 1))
        elif final == "D":
            self.x = max(0, self.x - (nums[0] if nums else 1))
        elif final == "X":
            n = nums[0] if nums else 1
            for x in range(self.x, min(self.w, self.x + n)):
                self.grid[self.y][x] = " "
        elif final == "P":
            n = nums[0] if nums else 1
            row = self.grid[self.y]
            del row[self.x:self.x + n]
            self.grid[self.y] = row + [" "] * (self.w - len(row))
        elif final == "@":
            n = nums[0] if nums else 1
            row = self.grid[self.y]
            for _ in range(n):
                row.insert(self.x, " ")
            self.grid[self.y] = row[:self.w]
        elif final == "L":
            n = nums[0] if nums else 1
            for _ in range(n):
                self.grid.insert(self.y, [" "] * self.w)
                self.grid.pop()
        elif final == "M":
            n = nums[0] if nums else 1
            for _ in range(n):
                self.grid.pop(self.y)
                self.grid.append([" "] * self.w)

    def text(self):
        return "\n".join("".join(row).rstrip() for row in self.grid)


def run(keys, wait, size, args):
    w, h = size
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", h, w, 0, 0))
    env = dict(os.environ, TERM="xterm-256color", LINES=str(h), COLUMNS=str(w))
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.Popen([sys.executable, os.path.join(here, "play_coriolis.py")] + args,
                            stdin=slave, stdout=slave, stderr=subprocess.PIPE,
                            env=env, cwd=here)
    os.close(slave)
    screen = Screen(w, h)
    buf = b""

    def drain(seconds):
        nonlocal buf
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    return False
                if not chunk:
                    return False
                buf += chunk
        return True

    drain(1.0)
    for ch in keys:
        try:
            os.write(master, ch.encode())
        except OSError:
            break
        drain(wait)
    drain(0.4)
    screen.feed(buf)
    try:
        os.write(master, b"\x1b")
    except OSError:
        pass
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    os.close(master)
    return screen.text(), err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="")
    ap.add_argument("--wait", type=float, default=0.35)
    ap.add_argument("--size", default="80x24")
    ap.add_argument("args", nargs="*")
    ns = ap.parse_args()
    w, h = (int(v) for v in ns.size.lower().split("x"))
    keys = ns.keys.encode().decode("unicode_escape")
    text, err = run(keys, ns.wait, (w, h), ns.args)
    print(text)
    if err.strip():
        print("--- stderr ---")
        print(err[-2000:])


if __name__ == "__main__":
    main()

#!/bin/python3
# A local copy of buddhist-uni.github.io/scripts/strutils.py
# minus the obu-specific stuff at the end of the file

import random
import sys
import termios
import tty
import os
import re
import string
import readline
from pathlib import Path
from functools import reduce
try:
    from titlecase import titlecase
except BaseException:
    print("pip install titlecase")
    quit(1)

ANSI_COLOR_DIM = "\033[2m"
ANSI_COLOR_RESET = "\033[0m"
ANSI_SAVE_POSITION = "\033[s"
ANSI_RESTORE_POSITION = "\033[u"
ANSI_ERASE_HERE_TO_END = "\033[0J"
ANSI_ERASE_HERE_TO_LINE_END = "\033[0K"


def ANSI_RETURN_N_UP(n):
    return f"\033[{n}F"
def ANSI_RETURN_N_DOWN(n):
    return f"\033[{n}E"
def ANSI_MOVE_LEFT(n):
    return f"\033[{n}D"
def ANSI_MOVE_RIGHT(n):
    return f"\033[{n}C"
def ANSI_MOVE_DOWN(n):
    return f"\033[{n}B"
def ANSI_MOVE_UP(n):
    return f"\033[{n}A"
# For more, see https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797


whitespace = re.compile('\\s+')
digits = re.compile('(\\d+)')
italics = re.compile('</?(([iI])|(em))[^<>nm]*>')

git_root_folder = Path(
    os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "../")))


def sanitize_string(text):
    return abnormalchars.sub('', whitespace.sub(' ', text)).strip()


def atoi(text):
    return int(text) if text.isdigit() else text


def cumsum(vec):
    return reduce(lambda a, x: a + [a[-1] + x] if a else [x], vec, [])


def natural_key(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    '''
    return [atoi(c) for c in digits.split(text)]


def naturally_sorted(alist):
    return sorted(alist, key=natural_key)


def cout(*args):
    print(*args, flush=True, end="")


def get_cursor_position():
    """Returns (row, col)"""  # á la termios.tcgetwinsize
    # code courtesy of https://stackoverflow.com/a/69582478/1229747
    stdinMode = termios.tcgetattr(sys.stdin)
    _ = termios.tcgetattr(sys.stdin)
    _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
    termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, _)
    try:
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()
        _ = ""
        while not (_ := _ + sys.stdin.read(1)).endswith('R'):
            pass
        res = re.match(r".*\[(?P<y>\d*);(?P<x>\d*)R", _)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, stdinMode)
    if (res):
        return (atoi(res.group("y")), atoi(res.group("x")))
    return (-1, -1)


def stdout_make_room(lines: int):
    """Saves the current cursor position and ensures n lines are free below it

    returns the number of lines the terminal actually shifted up by"""
    cout(ANSI_SAVE_POSITION)
    if lines <= 0:
        return 0
    br, bc = get_cursor_position()
    nr, nc = termios.tcgetwinsize(sys.stdout)
    diff = lines + br - nr
    cout(''.join(["\n"] * lines))
    cout(ANSI_RESTORE_POSITION)
    if diff > 0:
        cout(ANSI_MOVE_UP(diff))
        cout(ANSI_SAVE_POSITION)
        return diff
    return 0


def checklist_prompt(options: list[str], default=False):
    selections = []
    if isinstance(default, list):
        selections = default[:len(options)] + [False] * \
            max(0, len(options) - len(default))
    else:
        selections = [default for i in options]
    tsize = os.get_terminal_size()
    length = len(options)
    i = 0
    room = min(tsize.lines - 2, length) + 1
    r = (0, room - 1)
    space = tsize.columns - 6
    options = [trunc(t, space) for t in options]
    stdin = sys.stdin.fileno()
    stdout_make_room(room)
    old_settings = termios.tcgetattr(stdin)
    tty.setraw(stdin)
    try:
        while True:
            cout(
                f"{ANSI_RESTORE_POSITION}{ANSI_ERASE_HERE_TO_END}{ANSI_RESTORE_POSITION}")
            for j in range(r[0], r[1]):
                if j == i:
                    cout(">")
                else:
                    cout(" ")
                cout("[")
                if selections[j]:
                    cout("X")
                else:
                    cout(" ")
                cout(f"] {options[j]}")
                cout(ANSI_RETURN_N_DOWN(1))
            if i == length:
                cout("> ")
            else:
                cout("  ")
            cout("Accept")
            ch = sys.stdin.read(1)
            if ch == '\x03':
                raise KeyboardInterrupt()
            elif ch in ['\r', '\x04', '\n', ' ', 'x', 'X', '-']:
                if i == length:
                    break
                else:
                    selections[i] = not selections[i]
            elif ch == '\x1b':  # ESC
                ch = sys.stdin.read(1)
                if ch == '[':  # we're getting a control char (e.g. arrow keys)
                    ch = sys.stdin.read(1)
                    # A=up, B=down, C=right, D=left, H=home, F=end
                    if i > 0 and (ch == 'A' or ch == 'D'):
                        i -= 1
                        if i < r[0]:
                            r = (r[0] - 1, r[1] - 1)
                    if (ch == 'B' or ch == 'C') and (length > i):
                        i += 1
                        if i > r[1]:
                            r = (r[0] + 1, r[1] + 1)
                    if ch == "F":
                        i = length
                        r = (length - room + 1, length)
                    if ch == 'H':
                        i = 0
                        r = (0, room - 1)
    finally:
        cout(f"{ANSI_RESTORE_POSITION}{ANSI_RETURN_N_DOWN(room)}\n")
        termios.tcsetattr(stdin, termios.TCSADRAIN, old_settings)
    return selections


def radio_dial(options):
    SEARCH_ROOM = 3
    i = 0
    length = len(options)
    stdout_make_room(SEARCH_ROOM)
    space = os.get_terminal_size().columns - 10
    options = [trunc(t, space) for t in options]
    stdin = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin)
    tty.setraw(stdin)
    try:
        while True:
            cout(
                f"{ANSI_RESTORE_POSITION}{ANSI_ERASE_HERE_TO_END}{ANSI_RESTORE_POSITION}")
            if i > 0:
                cout(
                    f"{ANSI_COLOR_DIM}   {i}/{length}: {options[i-1]}{ANSI_COLOR_RESET}")
            cout(ANSI_RETURN_N_DOWN(1))
            cout(f" > {i+1}/{length}: {options[i]}")
            if length > i + 1:
                cout(ANSI_RETURN_N_DOWN(1))
                cout(
                    f"{ANSI_COLOR_DIM}   {i+2}/{length}: {options[i+1]}{ANSI_COLOR_RESET}")
            ch = sys.stdin.read(1)
            if ch == '\x03':
                raise KeyboardInterrupt()
            elif ch in ['\r', '\x04', '\n']:
                break
            elif ch == '\x1b':  # ESC
                ch = sys.stdin.read(1)
                if ch == '[':  # we're getting a control char (e.g. arrow keys)
                    ch = sys.stdin.read(1)
                    # A=up, B=down, C=right, D=left, H=home, F=end
                    if i > 0 and (ch == 'A' or ch == 'D'):
                        i -= 1
                    if (ch == 'B' or ch == 'C') and (length > i + 1):
                        i += 1
                    if ch == "F":
                        i = length - 1
                    if ch == 'H':
                        i = 0
            else:
                pass
    finally:
        cout(f"{ANSI_RESTORE_POSITION}{ANSI_RETURN_N_DOWN(SEARCH_ROOM)}\n")
        termios.tcsetattr(stdin, termios.TCSADRAIN, old_settings)
    return i


def input_list(prompt):
    print(prompt)
    ret = []
    while True:
        item = input(" - ")
        if not item:
            break
        ret.append(item)
    return ret


def input_with_prefill(prompt, text, validator=None):
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    while True:
        result = input(prompt)
        if not validator:
            break
        try:
            if validator(result):
                break
            else:
                continue
        except BaseException:
            continue
    readline.set_pre_input_hook()
    return result


def input_with_tab_complete(prompt, typeahead_suggestions):
    readline.set_completer(lambda text, state: (
        [s for s in typeahead_suggestions if s.startswith(text)][state]
    ))
    readline.parse_and_bind('tab: complete')
    ret = input(prompt)
    readline.set_completer(None)
    return ret


def trunc(longstr, maxlen=12) -> str:
    return longstr if len(longstr) <= maxlen else (longstr[:maxlen - 1] + '…')


def random_letters(length):
    return ''.join(random.choice(string.ascii_lowercase)
                   for i in range(length))


def uppercase_ratio(s: str) -> float:
    if not s:
        return 0
    alph = list(filter(str.isalpha, s))
    return sum(map(str.isupper, alph)) / len(alph)

# leaves a string unmolested if the ratio looks reasonable
# could be smarter but this is good enough™️


def title_case(s: str) -> str:
    if not s:
        return ''
    p = uppercase_ratio(s)
    # 11% with high confidence!
    if p < 0.11 or p > 0.20:
        return titlecase(s)
    # If the ratio looks good, trust
    return s


def prompt(question: str, default=None) -> bool:
    reply = None
    hint = "(y/n)"
    if default == "y":
        hint = "[y]/n"
    if default == "n":
        hint = "y/[n]"
    while reply not in ("y", "n"):
        reply = input(f"{question} {hint}: ").casefold()
        if not reply:
            reply = default
    return (reply == "y")


def system_open(filepath):
    os.system(
        f"open '{filepath}' || termux-open '{filepath}' || vim '{filepath}'")


class FileSyncedSet:
    def __init__(self, fname, normalizer=None):
        self.fname = fname
        self.items = set()
        # normalizer must return a string with no newlines
        self.norm = normalizer or (lambda a: str(a).replace("\n", " "))
        if os.path.exists(fname):
            with open(fname) as fd:
                for l in fd:
                    l = l[:-1]
                    self.items.add(l) if l else None

    def add(self, item):
        item = self.norm(item)
        if item not in self.items:
            self.items.add(item)
            with open(self.fname, "a") as fd:
                fd.write(f"{item}\n")

    def remove(self, item):
        item = self.norm(item)
        if item not in self.items:
            return
        self.items.remove(item)
        self._rewrite_file()

    def _rewrite_file(self):
        with open(self.fname, "w") as fd:
            for item in self.items:
                fd.write(f"{item}\n") if item else None

    def delete_file(self):
        os.remove(self.fname)
        self.items = set()

    def peak(self):
        ret = self.items.pop()
        self.items.add(ret)
        return ret

    def pop(self):
        ret = self.items.pop()
        self._rewrite_file()
        return ret

    def __len__(self):
        return len(self.items)

    def __contains__(self, item):
        return self.norm(item) in self.items

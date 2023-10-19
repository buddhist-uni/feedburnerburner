import os


def system_open(filepath):
    os.system(f"open '{filepath}' || termux-open '{filepath}' || vim '{filepath}'")


def prompt(question: str, default = None) -> bool:
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


class FileSyncedSet:
    def __init__(self, file_name, normalizer=None):
        self.file_name = file_name
        self.items = set()
        # normalizer must return a string with no newlines
        self.norm = normalizer or (lambda a: str(a).replace("/n", " "))
        if os.path.exists(file_name):
            with open(file_name) as fd:
                for item in fd:
                    item = item[:-1]
                    self.items.add(item) if item else None

    def add(self, item):
        item = self.norm(item)
        if item not in self.items:
            self.items.add(item)
            with open(self.file_name, "a") as fd:
                fd.write(f"{item}\n")

    def remove(self, item):
        item = self.norm(item)
        if item not in self.items:
            return
        self.items.remove(item)
        with open(self.file_name, "w") as fd:
            for item in self.items:
                fd.write(f"{item}\n") if item else None

    def delete_file(self):
        os.remove(self.file_name)
        self.items = set()

    def __contains__(self, item):
        return self.norm(item) in self.items

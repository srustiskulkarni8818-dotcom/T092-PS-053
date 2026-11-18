def read_commands(path):
    """Read commands.txt and return a list of commands.
    Each command is a list: ['COMMAND_NAME', 'arg1', 'arg2', ...]"""
    commands = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue  # skip blank lines and comments
            commands.append(line.split("|"))
    return commands


if __name__ == "__main__":
    commands = read_commands("data/commands.txt")
    print("Number of commands:", len(commands))
    print("First command:", commands[0])
    print("Fourth command:", commands[3])
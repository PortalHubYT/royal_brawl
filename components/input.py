def sanitize_very_strict(str):
    if "NAKED" in str:
        return "notnakedbot"
    return "".join(
        c
        for c in str
        if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    )


def sanitize_less_strict(str):
    if "NAKED" in str:
        return "notnakedbot"
    return "".join(
        c
        for c in str
        if c in " []ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    )


def multi_split(string: str, split: list) -> str:

    for instruction in split:
        if instruction[0] in string:
            if instruction[1] == ">":
                string = string[string.find(instruction[0]) + len(instruction[0]) :]
            elif instruction[1] == "<":
                string = string[: string.find(instruction[0]) - len(instruction[0])]

    return string

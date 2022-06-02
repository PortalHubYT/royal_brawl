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
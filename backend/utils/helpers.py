def print_debug(debug: bool, msg: str, label: str = "DEBUG", *args, **kwargs) -> None:
    if debug:
        print_log(msg, label, *args, **kwargs)


def print_log(msg: str, label: str = "DEBUG", *args, **kwargs) -> None:
    num_spaces = 1 if 9 - len(label) < 0 else 9 - len(label)
    print(f"{label}:{' '*num_spaces}", end="")
    print(msg, *args, **kwargs)

def print_debug(debug: bool, msg: str, label: str = "DEBUG", *args, **kwargs) -> None:
    if debug:
        print_log(msg, label, *args, **kwargs)


def print_log(msg: str, label: str = "DEBUG", *args, **kwargs) -> None:
    print(f"[{label}] ", end="")
    print(msg, *args, **kwargs)



def print_debug(
    debug: bool,
    msg: str,
    debug_title: str = "DEBUG",
    *args,
    **kwargs,
):
    if debug:
        print(f"[{debug_title}]", end="")
        print(msg, *args, **kwargs)

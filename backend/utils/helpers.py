import datetime

from settings import *


def print_debug(
    msg: str,
    label: str = debug_debug,
    log_to_file: bool = False,
    *args,
    **kwargs,
) -> None:

    if DEBUG or log_to_file or label == debug_error:
        print_log(msg, label, log_to_file, *args, **kwargs)


def print_log(
    msg: str,
    label: str = "DEBUG",
    log_to_file: bool = False,
    *args,
    **kwargs,
) -> None:

    num_spaces = max(1, 9 - len(label))
    formatted_label = f"{label}:{' ' * num_spaces}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # print in terminal
    print(f"{formatted_label}{msg}", *args, **kwargs)

    # add to log file
    if log_to_file:
        with open(LOGS_FILENAME, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {formatted_label}{msg}\n")

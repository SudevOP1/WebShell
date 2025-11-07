import winpty, re, threading, sys


def clean_output(data):
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", data)


def read_output(pty):
    while True:
        try:
            data = pty.read()
            if data:
                print(clean_output(data), end="", flush=True)
        except EOFError:
            break
        except Exception as e:
            print(f"\nError reading: {e}")
            break


def create_terminal():
    print("loading...")

    # create a new pseudo terminal
    pty = winpty.PtyProcess.spawn("cmd.exe")

    # start a thread to continuously read output
    reader_thread = threading.Thread(target=read_output, args=(pty,), daemon=True)
    reader_thread.start()

    # __main__ thread handles input
    try:
        while True:
            user_input = input()
            pty.write(user_input + "\r\n")  # \r\n = enter (for windows)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    create_terminal()

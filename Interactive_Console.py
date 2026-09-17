__version__ = "1.3"


CALCULATIONS = {
    "ratios": ("financial ratios", ("ratio", "r", "financial")),
    "tvm": ("time value of money", ("t", "time", "time value")),
}

QUIT = ("q", "quit", "exit")


def menu(options=CALCULATIONS, question="Which calculation?"):
    print(f"\n{question}")
    for key, (description, _aliases) in options.items():
        print(f"  {key:<8} {description}")
    print(f"  {'q':<8} quit")


def match(raw, options=CALCULATIONS):
    for key, (_description, aliases) in options.items():
        if raw == key or raw in aliases:
            return key
    return None


def ask_calculation():
    menu()
    while True:
        try:
            raw = input("> ").strip().lower()
        except EOFError:
            print("(no input available)")
            return None
        if raw in QUIT:
            return None
        chosen = match(raw)
        if chosen is not None:
            return chosen
        print("  Please pick one of " + ", ".join(CALCULATIONS) + ", or 'q'.")


def main():
    chosen = ask_calculation()
    if chosen is None:
        print("Nothing selected.")
    else:
        print(f"Selected: {CALCULATIONS[chosen][0]}")
    return chosen


if __name__ == "__main__":
    main()

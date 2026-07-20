"""Entry point for the ghascii CLI."""

from ghascii.app import GhasciiApp


def main() -> None:
    app = GhasciiApp()
    app.run()


if __name__ == "__main__":
    main()

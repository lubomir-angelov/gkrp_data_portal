from __future__ import annotations

from dotenv import load_dotenv

from gkrp_data_portal.core.logging import configure_logging
from gkrp_data_portal.ui.app import run


def main() -> None:
    """Main entry point for running the NiceGUI app."""
    load_dotenv(".env", override=False)

    configure_logging()
    run()


if __name__ == "__main__":
    main()

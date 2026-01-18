from __future__ import annotations

from gkrp_data_portal.core.logging import configure_logging
from gkrp_data_portal.ui.app import run


def main() -> None:
    configure_logging()
    run()


if __name__ == "__main__":
    main()

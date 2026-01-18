"""ORM model package.

Importing this package registers all models on the SQLAlchemy metadata, which is
required for Alembic autogeneration.
"""

from gkrp_data_portal.models.archaeology import (  # noqa: F401
    Tblfind,
    Tblfragment,
    Tbllayer,
    Tbllayerinclude,
    Tblornament,
    Tblpok,
)
from gkrp_data_portal.models.auth import User  # noqa: F401

"""
ate-neva-obst
Python SDK for Domainesia / Neva Objects (S3-compatible storage).

Author:
    Azzam (AzzTE)

Credits:
    This SDK uses several open-source libraries:
    - binaryornot (created by Audrey Roy Greenfeld)
    - boto3 (AWS SDK for Python)

Thank you for Neva Cloud.
Thank you to the open-source community.
"""

"""
neva_obst - Unofficial Python SDK + CLI for Neva Object Storage (S3-compatible).
"""

from .client import NevaObjectsClient, NevaObjectsConfig
from .exceptions import DownloadError, ListError, NevaObjectsError, UploadError

__version__ = "2.0.3"
__all__ = [
    "NevaObjectsClient",
    "NevaObjectsConfig",
    "NevaObjectsError",
    "UploadError",
    "DownloadError",
    "ListError",
]


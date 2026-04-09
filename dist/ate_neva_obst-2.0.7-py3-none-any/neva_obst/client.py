"""
NevaObjectsClient - High-level S3-compatible client for Neva Objects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from .exceptions import DownloadError, ListError, NevaObjectsError, UploadError

DEFAULT_ENDPOINT = "https://s3.nevaobjects.id"


@dataclass
class ObjectInfo:
    """Metadata for a single object in a bucket."""

    key: str
    size: int
    last_modified: str
    etag: str = ""

    def __repr__(self) -> str:
        return f"ObjectInfo(key={self.key!r}, size={self.size}, last_modified={self.last_modified!r})"


@dataclass
class NevaObjectsConfig:
    """Configuration for NevaObjectsClient."""

    access_key: str
    secret_key: str
    bucket: str
    endpoint: str = DEFAULT_ENDPOINT
    default_expiry: int = 86400  # seconds (24h)
    extra_boto_config: dict = field(default_factory=dict)


class NevaObjectsClient:
    """
    High-level client for Neva Objects S3-compatible storage.

    Example usage::

        from neva_obst import NevaObjectsClient
        from neva_obst.client import NevaObjectsConfig

        config = NevaObjectsConfig(
            access_key="YOUR_ACCESS_KEY",
            secret_key="YOUR_SECRET_KEY",
            bucket="my-bucket",
        )
        client = NevaObjectsClient(config)

        # Upload
        client.upload("./photo.jpg")

        # List files
        for obj in client.list():
            print(obj.key, obj.size)

        # Get download URL (valid 24 hours)
        url = client.get_download_url("photo.jpg")

        # Delete
        client.delete("photo.jpg")
    """

    def __init__(self, config: NevaObjectsConfig) -> None:
        self.config = config
        self._s3 = self._build_client()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_client(self):
        boto_config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            **self.config.extra_boto_config,
        )
        return boto3.client(
            "s3",
            endpoint_url=self.config.endpoint,
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key,
            config=boto_config,
        )

    @staticmethod
    def _parse_client_error(error: ClientError) -> tuple[str, str]:
        resp = error.response.get("Error", {})
        return resp.get("Code", "Unknown"), resp.get("Message", "(no message)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload(
        self,
        local_path: str,
        object_key: Optional[str] = None,
        extra_args: Optional[dict] = None,
    ) -> str:
        """
        Upload a local file to the bucket.

        Args:
            local_path: Path to the local file.
            object_key: Destination key in the bucket. Defaults to the filename.
            extra_args: Extra arguments forwarded to boto3's ``upload_file``
                        (e.g. ``{"ContentType": "image/jpeg"}``).

        Returns:
            The object key that was uploaded.

        Raises:
            FileNotFoundError: If ``local_path`` does not exist.
            UploadError: If the upload fails.
        """
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        key = object_key or os.path.basename(local_path)

        try:
            self._s3.upload_file(
                Filename=local_path,
                Bucket=self.config.bucket,
                Key=key,
                ExtraArgs=extra_args or {},
            )
        except ClientError as exc:
            code, msg = self._parse_client_error(exc)
            raise UploadError(f"Upload failed for '{local_path}': {msg}", code=code, original=exc) from exc

        return key

    def list(self, prefix: str = "", max_keys: int = 1000) -> List[ObjectInfo]:
        """
        List objects in the bucket, optionally filtered by prefix.

        Args:
            prefix: Key prefix to filter objects.
            max_keys: Maximum number of objects to return.

        Returns:
            List of :class:`ObjectInfo` objects.

        Raises:
            ListError: If the listing request fails.
        """
        try:
            response = self._s3.list_objects_v2(
                Bucket=self.config.bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
        except ClientError as exc:
            code, msg = self._parse_client_error(exc)
            raise ListError(f"Failed to list objects: {msg}", code=code, original=exc) from exc

        contents = response.get("Contents", [])
        return [
            ObjectInfo(
                key=obj["Key"],
                size=obj["Size"],
                last_modified=str(obj["LastModified"]),
                etag=obj.get("ETag", "").strip('"'),
            )
            for obj in contents
        ]

    def list_keys(self, prefix: str = "") -> List[str]:
        """
        Convenience method that returns only object keys.

        Returns:
            List of string keys.
        """
        return [obj.key for obj in self.list(prefix=prefix)]

    def get_download_url(
        self,
        object_key: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generate a pre-signed download URL for an object.

        Args:
            object_key: Key of the object in the bucket.
            expires_in: URL validity in seconds. Defaults to ``config.default_expiry``.

        Returns:
            Pre-signed URL string.

        Raises:
            DownloadError: If URL generation fails.
        """
        expiry = expires_in if expires_in is not None else self.config.default_expiry

        try:
            url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.config.bucket, "Key": object_key},
                ExpiresIn=expiry,
            )
        except ClientError as exc:
            code, msg = self._parse_client_error(exc)
            raise DownloadError(
                f"Failed to generate URL for '{object_key}': {msg}",
                code=code,
                original=exc,
            ) from exc

        return url

    def delete(self, object_key: str) -> None:
        """
        Delete an object from the bucket.

        Args:
            object_key: Key of the object to delete.

        Raises:
            NevaObjectsError: If deletion fails.
        """
        try:
            self._s3.delete_object(Bucket=self.config.bucket, Key=object_key)
        except ClientError as exc:
            code, msg = self._parse_client_error(exc)
            raise NevaObjectsError(
                f"Failed to delete '{object_key}': {msg}",
                code=code,
                original=exc,
            ) from exc

    def object_exists(self, object_key: str) -> bool:
        """
        Check whether an object exists in the bucket.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.
        """
        try:
            self._s3.head_object(Bucket=self.config.bucket, Key=object_key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            code, msg = self._parse_client_error(exc)
            raise NevaObjectsError(
                f"Failed to check existence of '{object_key}': {msg}",
                code=code,
                original=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "NevaObjectsClient":
        return self

    def __exit__(self, *_) -> None:
        pass  # boto3 client is stateless; nothing to close

    def __repr__(self) -> str:
        return (
            f"NevaObjectsClient(bucket={self.config.bucket!r}, "
            f"endpoint={self.config.endpoint!r})"
        )
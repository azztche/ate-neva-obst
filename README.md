# ate-neva-obst

![PyPI](https://img.shields.io/pypi/v/ate-neva-obst)
![Python](https://img.shields.io/pypi/pyversions/ate-neva-obst)
![License](https://img.shields.io/pypi/l/ate-neva-obst)

Unofficial Python SDK for **Neva Object Storage** (S3-compatible).

---

## Installation

```bash
pip install ate-neva-obst
```

---

## Usage

```python
from neva_obst import ObjectsClient
from neva_obst.client import ObjectsConfig

config = ObjectsConfig(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
)

with ObjectsClient(config) as client:

    # Upload file
    key = client.upload("./photo.jpg")
    print(f"Uploaded: {key}")

    # Upload with custom object key
    client.upload("./document.pdf", object_key="reports/2024/document.pdf")

    # Check if object exists
    if client.object_exists("photo.jpg"):
        print("Object exists!")

    # List all objects
    for obj in client.list():
        print(f"{obj.key}  {obj.size} bytes  {obj.last_modified}")

    # Get only object keys
    keys = client.list_keys(prefix="reports/")

    # Download object
    client.download(object_key="photo.jpg", local_path="./photo.jpg")

    # Generate download URL (default expiry)
    url = client.get_download_url("photo.jpg")

    # Generate download URL with custom expiry (1 hour)
    url = client.get_download_url("photo.jpg", expires_in=3600)

    # Delete object
    client.delete("photo.jpg")
```

## Error Handling

```python
from neva_obst import (
    ObjectsClient,
    UploadError,
    ListError,
    DownloadError,
    ObjectsError
)

try:
    client.upload("./file.txt")

except FileNotFoundError as e:
    print(f"File not found: {e}")

except UploadError as e:
    print(f"Upload failed [{e.code}]: {e}")

except ObjectsError as e:
    print(f"General error: {e}")
```

---

## Full Configuration

```python
config = ObjectsConfig(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
    endpoint="https://s3.nevaobjects.id",  # default endpoint
    default_expiry=3600,                   # default URL expiry (seconds)
)
```

---

## Changelog

**2026-02-28**  
Initial release of **ate-neva-obst** SDK.

**2026-03-07**  
Project renamed from **ate-dme-obst** → **ate-neva-obst**.

**2026-03-09**  
- Improved error handling (better 404 detection)  
- Added automatic **Content-Type detection** during upload


## Disclaimer

- This package is **not officially affiliated with Neva Cloud or Domainesia**.
- The SDK is **stateless** and does not transmit user data to third-party servers (except the target storage endpoint).
- The official project website is currently under development and will include guides and full documentation.

---

## About

**ate-neva-obst** is an open-source project built by **AzzTE**.

Made with passion for developers who want a simple and clean Python SDK for Neva Object Storage.
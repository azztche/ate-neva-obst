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

## SDK Usage

### Basic Setup

```python
from neva_obst import NevaObjectsClient
from neva_obst.client import NevaObjectsConfig

config = NevaObjectsConfig(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
)

client = NevaObjectsClient(config)
```

Supports context manager:

```python
with NevaObjectsClient(config) as client:
    ...
```

### Full Configuration

```python
config = NevaObjectsConfig(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
    endpoint="https://s3.nevaobjects.id",  # default
    default_expiry=86400,                  # pre-signed URL expiry in seconds (default: 24h)
    extra_boto_config={},                  # extra kwargs forwarded to botocore.client.Config
)
```

---

### Upload

```python
# Upload with auto key (uses filename)
key = client.upload("./photo.jpg")
print(f"Uploaded: {key}")

# Upload with custom object key
client.upload("./document.pdf", object_key="reports/2024/document.pdf")

# Upload with extra boto3 args (e.g. set Content-Type manually)
client.upload("./photo.jpg", extra_args={"ContentType": "image/jpeg"})
```

Returns the object key as a string. Raises `FileNotFoundError` if the local file does not exist.

---

### List Objects

```python
# List all objects
for obj in client.list():
    print(obj.key, obj.size, obj.last_modified, obj.etag)

# Filter by prefix
for obj in client.list(prefix="reports/"):
    print(obj.key)

# Limit results
objects = client.list(max_keys=100)

# Get keys only
keys = client.list_keys()
keys = client.list_keys(prefix="uploads/")
```

`list()` returns a list of `ObjectInfo`:

```python
@dataclass
class ObjectInfo:
    key: str
    size: int          # bytes
    last_modified: str
    etag: str
```

---

### Pre-signed Download URL

```python
# Default expiry (from config.default_expiry, default 24h)
url = client.get_download_url("photo.jpg")

# Custom expiry in seconds
url = client.get_download_url("photo.jpg", expires_in=3600)
```

---

### Check Object Existence

```python
if client.object_exists("photo.jpg"):
    print("exists")
```

Returns `True` or `False`. Only raises on non-404 errors.

---

### Delete

```python
client.delete("photo.jpg")
```

---

### Error Handling

```python
from neva_obst.exceptions import NevaObjectsError, UploadError, DownloadError, ListError

try:
    client.upload("./file.txt")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except UploadError as e:
    print(f"Upload failed [{e.code}]: {e}")
except NevaObjectsError as e:
    print(f"General error [{e.code}]: {e}")
```

All custom exceptions expose `.code` (S3 error code string) and `.original` (original `ClientError`).
Exception hierarchy:

```
NevaObjectsError
├── UploadError
├── DownloadError
└── ListError
```

---

## CLI Usage

### Configure Credentials

```bash
nevaobst configure
```

Credentials are resolved in this priority order: **flags → env vars → config file**

| Source | Variables |
|---|---|
| Environment | `NEVA_ACCESS_KEY`, `NEVA_SECRET_KEY`, `NEVA_BUCKET`, `NEVA_ENDPOINT` |
| Flags | `--access-key`, `--secret-key`, `--bucket`, `--endpoint` |
| Config file | `~/.azzte/neva-obst.conf` |

---

### Commands

#### `upload`
```bash
nevaobst upload photo.jpg
nevaobst upload "images/*" --prefix uploads/2024/
nevaobst upload report.pdf --key docs/report-q1.pdf
```

#### `list`
```bash
nevaobst list
nevaobst list -fs                # show size + last modified
nevaobst list --prefix uploads/
nevaobst list --json
```

Output is displayed as a file tree:
```
📄 text.txt
📄 readme.md
📁 reports/
   📄 q1.pdf
   📄 q2.pdf
📁 uploads/
   📁 2024/
      📄 photo.jpg
```

#### `info`
```bash
nevaobst info photo.jpg
nevaobst info photo.jpg --json
```

#### `get-url`
```bash
nevaobst get-url photo.jpg
nevaobst get-url report.pdf --expires 3600
```

#### `delete`
```bash
nevaobst delete photo.jpg
nevaobst delete a.jpg b.jpg c.jpg --force
```

### Global Flags

| Flag | Description |
|---|---|
| `--json` | Output as JSON |
| `--profile` | Use a named config profile (default: `default`) |
| `--help` | Show help for the command |

---

## Changelog

**2026-03-09**
- Improved error handling (better 404 detection)
- Added automatic Content-Type detection during upload
- Added CLI (`nevaobst`)

**2026-03-07**
- Project renamed from `ate-dme-obst` → `ate-neva-obst`

**2026-02-28**
- Initial release

---

## Disclaimer

This package is **not officially affiliated with Neva Cloud or Domainesia**.
The SDK is stateless and does not transmit user data to third-party servers outside the target storage endpoint.

---

## About

**ate-neva-obst** is an open-source project by [**AzzTE**](https://azzte.com).
Licensed under the **BSD-3-Clause License**.
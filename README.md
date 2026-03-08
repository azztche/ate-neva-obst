# ate-neva-obst

Unofficial Python SDK for Neva Object or Domainesia Object Storage.

## Instalasi

```bash
pip install ate-neva-obst
```

## Penggunaan

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
    key = client.upload("./foto.jpg")
    print(f"Uploaded: {key}")

    # Upload dengan key kustom
    client.upload("./dokumen.pdf", object_key="reports/2024/dokumen.pdf")

    # Cek apakah object ada
    if client.object_exists("foto.jpg"):
        print("Ada!")

    # List semua file
    for obj in client.list():
        print(f"{obj.key}  {obj.size} bytes  {obj.last_modified}")

    # List hanya keys
    keys = client.list_keys(prefix="reports/")

    # Generate URL download (valid 24 jam)
    url = client.get_download_url("foto.jpg")

    # Generate URL dengan durasi kustom (1 jam)
    url = client.get_download_url("foto.jpg", expires_in=3600)

    # Hapus file
    client.delete("foto.jpg")
```

## Error Handling

```python
from neva_obst import ObjectsClient, UploadError, ListError, DownloadError, ObjectsError

try:
    client.upload("./file.txt")
except FileNotFoundError as e:
    print(f"File tidak ditemukan: {e}")
except UploadError as e:
    print(f"Upload gagal [{e.code}]: {e}")
except ObjectsError as e:
    print(f"Error: {e}")
```

## Konfigurasi Lengkap

```python
config = ObjectsConfig(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
    endpoint="https://s3.nevaobjects.id",  # default
    default_expiry=3600,                   # URL expiry default (detik)
)
```

## About

ate-neva-obst is Open Source project.
Make by AzzTE SDK.
Build by Love.
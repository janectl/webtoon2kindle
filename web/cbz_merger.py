import re
import shutil
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_STORED

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def natural_key(value):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", value)
    ]


def episode_number(filename):
    match = re.search(
        r"(?:episode|ep)[\s._-]*(\d+)",
        filename,
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def sort_episodes(files):
    return sorted(
        files,
        key=lambda file: (
            episode_number(file.filename) is None,
            episode_number(file.filename) or 0,
            natural_key(file.filename),
        ),
    )


def merge_cbz(files, output_path):
    """
    Merge CBZ files into a single ordered CBZ.

    Files are processed in the order provided.
    Images are copied without decoding or recompression.
    """
    total_pages = 0

    with ZipFile(
        output_path,
        "w",
        compression=ZIP_STORED,
        allowZip64=True,
    ) as output:

        for episode_index, uploaded_file in enumerate(files, start=1):
            uploaded_file.stream.seek(0)

            with ZipFile(uploaded_file.stream, "r") as source:
                images = sorted(
                    [
                        item
                        for item in source.infolist()
                        if not item.is_dir()
                        and PurePosixPath(item.filename).suffix.lower()
                        in IMAGE_EXTENSIONS
                        and "__MACOSX" not in item.filename.split("/")
                    ],
                    key=lambda item: natural_key(item.filename),
                )

                if not images:
                    raise ValueError(
                        f"No images found in {uploaded_file.filename}"
                    )

                print(
                    f"[Webtoon2Kindle] Merging "
                    f"{uploaded_file.filename}: {len(images)} images",
                    flush=True,
                )

                for item in images:
                    total_pages += 1

                    extension = PurePosixPath(
                        item.filename
                    ).suffix.lower()

                    destination = f"{total_pages:06d}{extension}"

                    with source.open(item) as src:
                        with output.open(destination, "w") as dst:
                            shutil.copyfileobj(
                                src,
                                dst,
                                length=1024 * 1024,
                            )

    return total_pages
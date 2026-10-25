import shutil
from pathlib import PurePosixPath
from zipfile import ZipFile, ZIP_STORED


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def merge_cbz(files, output_path):
    """
    Merge CBZ files into one archive.

    Each source CBZ becomes a separate episode folder.
    Images are copied without decoding or recompression.
    """

    with ZipFile(
        output_path,
        "w",
        compression=ZIP_STORED,
        allowZip64=True
    ) as output:

        for episode_number, uploaded_file in enumerate(files, start=1):
            uploaded_file.stream.seek(0)

            with ZipFile(uploaded_file.stream, "r") as source:

                images = sorted(
                    [
                        item for item in source.infolist()
                        if not item.is_dir()
                        and PurePosixPath(item.filename).suffix.lower()
                        in IMAGE_EXTENSIONS
                    ],
                    key=lambda item: item.filename
                )

                if not images:
                    raise ValueError(
                        f"Episode {episode_number} contains no images"
                    )

                for page_number, item in enumerate(images, start=1):
                    extension = PurePosixPath(
                        item.filename
                    ).suffix.lower()

                    filename = (
                        f"Episode_{episode_number:03d}/"
                        f"{page_number:04d}{extension}"
                    )

                    with source.open(item) as src:
                        with output.open(filename, "w") as dst:
                            shutil.copyfileobj(
                                src,
                                dst,
                                length=1024 * 1024
                            )

    return output_path
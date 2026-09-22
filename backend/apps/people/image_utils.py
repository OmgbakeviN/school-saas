from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_INPUT_BYTES = 15 * 1024 * 1024
MAX_INPUT_PIXELS = 40_000_000
MAX_DIMENSION = 900
TARGET_BYTES = 500 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


class StudentPhotoError(ValueError):
    pass


def _rgb_image(image):
    image = ImageOps.exif_transpose(image)

    if image.width * image.height > MAX_INPUT_PIXELS:
        raise StudentPhotoError(
            "L'image est trop grande. Utilisez une photo de moins de 40 mégapixels."
        )

    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    return image.convert("RGB")


def compress_student_photo(uploaded_file):
    if not uploaded_file:
        raise StudentPhotoError("Aucune photo n'a été fournie.")

    if uploaded_file.size and uploaded_file.size > MAX_INPUT_BYTES:
        raise StudentPhotoError(
            "La photo originale dépasse 15 Mo. Choisissez une image plus légère."
        )

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise StudentPhotoError(
            "Format non pris en charge. Utilisez JPG, PNG ou WEBP."
        )

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise StudentPhotoError("Le fichier fourni n'est pas une image valide.") from exc

    image = _rgb_image(image)
    image.thumbnail(
        (MAX_DIMENSION, MAX_DIMENSION),
        Image.Resampling.LANCZOS,
    )

    output = BytesIO()
    selected_quality = 82

    for quality in (82, 76, 70):
        output = BytesIO()
        image.save(
            output,
            format="WEBP",
            quality=quality,
            method=6,
        )
        selected_quality = quality
        if output.tell() <= TARGET_BYTES:
            break

    if output.tell() > TARGET_BYTES and max(image.size) > 720:
        image.thumbnail((720, 720), Image.Resampling.LANCZOS)
        output = BytesIO()
        selected_quality = 70
        image.save(
            output,
            format="WEBP",
            quality=selected_quality,
            method=6,
        )

    content = ContentFile(output.getvalue())
    return content, {
        "width": image.width,
        "height": image.height,
        "size_bytes": output.tell(),
        "format": "WEBP",
        "quality": selected_quality,
    }

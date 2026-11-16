"""Image derivatives and upload normalisation (issue #22).

Pages used to embed the file exactly as uploaded. A 6000 px photo shown in a
96 px avatar or a 256 px news thumbnail is downsampled by the browser, which
aliases badly, and the visitor downloads all of it.

Two measures:

* `spec()` builds an imagekit ImageSpecField: a resized WebP copy, generated
  on first use with Lanczos resampling and cached under MEDIA_ROOT/CACHE/.
  Templates reach it through the `derivative_url` tag (image_tags.py), which
  falls back to the original when the copy cannot be produced.
* `normalise_upload()` caps what is stored in the first place.
"""
from io import BytesIO

from django.core.files.base import ContentFile
from imagekit.models import ImageSpecField
from PIL import Image, ImageOps
from pilkit.processors import ResizeToFill, ResizeToFit, Transpose

# Longest side kept for an uploaded original. Larger than any derivative,
# small enough that a phone photo does not sit on disk at 12 MB.
MAX_UPLOAD_SIDE = 2560

WEBP = {'quality': 82, 'method': 4}


def spec(source, width, height=None, crop=False):
    """A WebP derivative of `source`.

    crop=False  fit inside width x height, keeping the aspect ratio
    crop=True   fill width x height exactly, cropping around the centre
    Never upscales; EXIF orientation is applied first.
    """
    if crop:
        resize = ResizeToFill(width, height or width, upscale=False)
    else:
        resize = ResizeToFit(width, height, upscale=False)
    return ImageSpecField(
        source=source,
        processors=[Transpose(), resize],
        format='WEBP',
        options=WEBP,
    )


def normalise_upload(uploaded, max_side=MAX_UPLOAD_SIDE):
    """Return an uploaded image with EXIF rotation applied and its longest
    side capped at `max_side`, as a ContentFile carrying the original name.

    Files that are already small enough and need no rotation are returned
    untouched, so nothing is re-encoded without a reason. Anything Pillow
    cannot read is also returned as-is: validation is the form's/model's job.
    """
    try:
        uploaded.seek(0)
        img = Image.open(uploaded)
        img.load()
    except Exception:
        uploaded.seek(0)
        return uploaded

    fmt = img.format or 'JPEG'
    animated = getattr(img, 'is_animated', False)
    # EXIF tag 0x0112 is Orientation; 1 means "already upright".
    needs_rotation = img.getexif().get(0x0112, 1) not in (None, 1)
    too_big = max(img.size) > max_side

    if animated or not (needs_rotation or too_big):
        uploaded.seek(0)
        return uploaded

    img = ImageOps.exif_transpose(img)
    if too_big:
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    save_kwargs = {}
    if fmt == 'JPEG':
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        save_kwargs = {'quality': 90, 'optimize': True}
    elif fmt == 'WEBP':
        save_kwargs = {'quality': 90}
    elif fmt == 'PNG':
        save_kwargs = {'optimize': True}

    out = BytesIO()
    img.save(out, format=fmt, **save_kwargs)
    return ContentFile(out.getvalue(), name=uploaded.name)

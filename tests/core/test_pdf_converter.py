import os
import pytest
from PIL import Image
from contratos.core.pdf_converter import (
    is_allowed_file,
    is_cedula,
    collect_images,
    separate_images,
    convert_image_to_pdf,
    merge_images_to_pdf,
    process_client,
)


def test_is_allowed_file_accepts_jpg():
    assert is_allowed_file("foto.jpg") is True


def test_is_allowed_file_accepts_jpeg_uppercase():
    assert is_allowed_file("foto.JPEG") is True


def test_is_allowed_file_accepts_png():
    assert is_allowed_file("imagen.PNG") is True


def test_is_allowed_file_rejects_pdf():
    assert is_allowed_file("doc.pdf") is False


def test_is_allowed_file_rejects_txt():
    assert is_allowed_file("file.txt") is False


def test_is_cedula_detects_cc1():
    assert is_cedula("CC1_foto.jpg") is True


def test_is_cedula_detects_cc2_lowercase():
    assert is_cedula("cc2_foto.jpg") is True


def test_is_cedula_rejects_non_cedula():
    assert is_cedula("contrato.jpg") is False


def test_collect_images_from_dir(tmp_path):
    (tmp_path / "foto.jpg").write_bytes(b"fake")
    (tmp_path / "imagen.PNG").write_bytes(b"fake")
    (tmp_path / "doc.pdf").write_bytes(b"fake")

    result = collect_images([str(tmp_path)])
    basenames = [os.path.basename(p) for p in result]
    assert "foto.jpg" in basenames
    assert "imagen.PNG" in basenames
    assert "doc.pdf" not in basenames


def test_collect_images_from_file(tmp_path):
    img = tmp_path / "foto.jpg"
    img.write_bytes(b"fake")
    result = collect_images([str(img)])
    assert len(result) == 1


def test_collect_images_skips_nonexistent():
    result = collect_images(["/ruta/que/no/existe.jpg"])
    assert result == []


def test_separate_images_splits_cedulas(tmp_path):
    (tmp_path / "CC1_foto.jpg").write_bytes(b"fake")
    (tmp_path / "CC2_foto.jpg").write_bytes(b"fake")
    (tmp_path / "contrato.jpg").write_bytes(b"fake")

    cedulas, others = separate_images(str(tmp_path))
    cedula_names = [os.path.basename(p) for p in cedulas]
    other_names = [os.path.basename(p) for p in others]

    assert "CC1_foto.jpg" in cedula_names
    assert "CC2_foto.jpg" in cedula_names
    assert "contrato.jpg" in other_names
    assert "contrato.jpg" not in cedula_names


def _make_jpg(path) -> str:
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(str(path), "JPEG")
    return str(path)


def test_convert_image_to_pdf_success(tmp_path):
    img = _make_jpg(tmp_path / "foto.jpg")
    ok, out = convert_image_to_pdf(img, str(tmp_path))
    assert ok is True
    assert out is not None and os.path.isfile(out)
    assert out.endswith(".pdf")


def test_convert_image_to_pdf_invalid_image(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    ok, out = convert_image_to_pdf(str(bad), str(tmp_path))
    assert ok is False
    assert out is None


def test_merge_images_to_pdf_empty_list(tmp_path):
    ok, out = merge_images_to_pdf([], str(tmp_path), "merged")
    assert ok is False
    assert out is None


def test_merge_images_to_pdf_success(tmp_path):
    imgs = [_make_jpg(tmp_path / f"foto{i}.jpg") for i in range(2)]
    ok, out = merge_images_to_pdf(imgs, str(tmp_path), "combined")
    assert ok is True
    assert out is not None and os.path.isfile(out)


def test_process_client_creates_pdf_subdir(tmp_path):
    client_dir = tmp_path / "Cliente ABC"
    client_dir.mkdir()
    _make_jpg(client_dir / "contrato.jpg")
    pdfs = process_client(str(client_dir))
    assert (client_dir / "_pdfs").is_dir()
    assert len(pdfs) >= 1

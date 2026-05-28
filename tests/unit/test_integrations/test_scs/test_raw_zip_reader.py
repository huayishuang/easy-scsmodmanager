from __future__ import annotations

import struct
import zipfile
from pathlib import Path

import pytest

from easy_scsmodmanager.integrations.scs.raw_zip_reader import RawZipReader


def _make_fake_lock_zip(
    path: Path,
    entries: dict[str, bytes],
    compression: int = zipfile.ZIP_DEFLATED,
) -> Path:
    # Build a normal zip, then mangle it the way SCS map mods do: flip the
    # central-directory encryption bit (so stdlib zipfile refuses to read)
    # and relabel every local compression method as 1 (Shrunk), while the
    # deflate payload itself stays untouched plaintext.
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    raw = bytearray(path.read_bytes())
    pos = 0
    while (i := raw.find(b"PK\x03\x04", pos)) != -1:
        struct.pack_into("<H", raw, i + 8, 1)
        pos = i + 4
    pos = 0
    while (i := raw.find(b"PK\x01\x02", pos)) != -1:
        raw[i + 8] |= 0x01
        pos = i + 4
    path.write_bytes(bytes(raw))
    return path


def test_reads_fake_locked_manifest_stdlib_cannot(tmp_path: Path) -> None:
    text = b'SiiNunit\n{\nmod_package : .p {\ndisplay_name: "Map X"\n}\n}\n'
    scs = _make_fake_lock_zip(tmp_path / "map.scs", {"manifest.sii": text})

    # stdlib chokes on the (fake) encryption bit
    with zipfile.ZipFile(scs) as zf, pytest.raises(RuntimeError):
        zf.read("manifest.sii")

    # raw reader ignores the bit and the bogus method label
    with RawZipReader(scs) as reader:
        assert reader.read_bytes("manifest.sii") == text


def test_read_text_decodes_utf8(tmp_path: Path) -> None:
    scs = _make_fake_lock_zip(tmp_path / "m.scs", {"manifest.sii": b"SiiNunit\n{}\n"})

    with RawZipReader(scs) as reader:
        assert reader.read_text("manifest.sii") == "SiiNunit\n{}\n"


def test_has_finds_entry_and_misses_unknown(tmp_path: Path) -> None:
    scs = _make_fake_lock_zip(tmp_path / "m.scs", {"manifest.sii": b"SiiNunit\n{}\n"})

    with RawZipReader(scs) as reader:
        assert reader.has("manifest.sii") is True
        assert reader.has("does-not-exist") is False


def test_reads_stored_entry_relabeled(tmp_path: Path) -> None:
    # icons are usually stored (already-compressed jpg); a relabeled stored
    # entry must still round-trip even though raw-inflate can't touch it.
    jpg = b"\xff\xd8\xff\xe0" + b"not really compressed" * 4 + b"\xff\xd9"
    scs = _make_fake_lock_zip(
        tmp_path / "m.scs",
        {"manifest.sii": b"SiiNunit\n{}\n", "icon.jpg": jpg},
        compression=zipfile.ZIP_STORED,
    )

    with RawZipReader(scs) as reader:
        assert reader.read_bytes("icon.jpg") == jpg


def test_works_on_plain_deflate_zip_too(tmp_path: Path) -> None:
    # the reader is also used as a generic fallback, so an ordinary,
    # unmangled deflate zip must read cleanly as well.
    plain = tmp_path / "plain.scs"
    with zipfile.ZipFile(plain, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.sii", b"SiiNunit\n{plain}\n")

    with RawZipReader(plain) as reader:
        assert reader.read_text("manifest.sii") == "SiiNunit\n{plain}\n"


def test_read_bytes_raises_keyerror_for_missing(tmp_path: Path) -> None:
    scs = _make_fake_lock_zip(tmp_path / "m.scs", {"manifest.sii": b"x"})

    with RawZipReader(scs) as reader, pytest.raises(KeyError):
        reader.read_bytes("nope.sii")

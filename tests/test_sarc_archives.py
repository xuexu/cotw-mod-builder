import io
import sys
import tempfile
import types
import unittest
from pathlib import Path

from deca.ff_aaf import AAF_MAGIC, compress_aaf_bytes, extract_aaf
from deca.ff_sarc import EntrySarc, FileSarc
from deca.file import ArchiveFile


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods


def create_sarc(files: dict[str, bytes]) -> bytes:
  sarc = FileSarc()
  sarc.version = 4
  sarc.magic = b"SARC"
  sarc.ver2 = 2
  sarc.entries = []
  for index, (filename, data) in enumerate(files.items()):
    entry = EntrySarc(index=index, v_path=filename.encode("utf-8"))
    entry.length = len(data)
    entry.is_symlink = False
    sarc.entries.append(entry)

  output = io.BytesIO()
  sarc.header_serialize(ArchiveFile(output))
  for entry in sarc.entries:
    output.seek(entry.offset)
    output.write(files[entry.v_path.decode("utf-8")])
  return output.getvalue()


def read_sarc_contents(path: Path) -> tuple[bytes, bool, dict[str, bytes]]:
  sarc_data, is_aaf = mods.read_sarc_file(path)
  sarc = FileSarc()
  sarc.header_deserialize(io.BytesIO(sarc_data))
  contents = {
    entry.v_path.decode("utf-8"): sarc_data[entry.offset:entry.offset+entry.length]
    for entry in sarc.entries
    if not entry.is_symlink
  }
  return sarc_data, is_aaf, contents


class SarcArchiveTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_org_path = mods.ORG_DIR_PATH
    self.original_mod_path = mods.MOD_PATH
    self.temp_dir = tempfile.TemporaryDirectory()
    root = Path(self.temp_dir.name)
    mods.ORG_DIR_PATH = root / "org"
    mods.MOD_PATH = root / "mod"

  def tearDown(self) -> None:
    mods.ORG_DIR_PATH = self.original_org_path
    mods.MOD_PATH = self.original_mod_path
    self.temp_dir.cleanup()

  def write_original_archive(self, files: dict[str, bytes], use_aaf: bool = True) -> Path:
    sarc_data = create_sarc(files)
    archive_path = mods.ORG_DIR_PATH / "archives/test.ee"
    archive_path.parent.mkdir(parents=True)
    archive_path.write_bytes(compress_aaf_bytes(sarc_data) if use_aaf else sarc_data)
    return archive_path

  def write_mod_file(self, filename: str, data: bytes) -> None:
    path = mods.MOD_PATH / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

  def test_read_and_write_sarc_file_preserve_wrapper_format(self) -> None:
    sarc_data = create_sarc({"one.bin": b"one"})
    for use_aaf in (False, True):
      with self.subTest(use_aaf=use_aaf):
        path = mods.ORG_DIR_PATH / f"archive-{use_aaf}.ee"
        mods.write_sarc_file(path, sarc_data, use_aaf)
        decoded, detected_aaf = mods.read_sarc_file(path)

        self.assertEqual(decoded, sarc_data)
        self.assertEqual(detected_aaf, use_aaf)
        self.assertEqual(path.read_bytes().startswith(AAF_MAGIC), use_aaf)

  def test_get_sarc_file_info_returns_inner_sarc_offsets_for_aaf(self) -> None:
    archive_path = self.write_original_archive({"one.bin": b"one", "two.bin": b"two"})
    sarc_data, _, _ = read_sarc_contents(archive_path)

    archive_info = mods.get_sarc_file_info(archive_path, include_details=True)

    self.assertEqual(sarc_data[archive_info["one.bin"].offset:archive_info["one.bin"].offset+3], b"one")
    self.assertEqual(sarc_data[archive_info["two.bin"].offset:archive_info["two.bin"].offset+3], b"two")

  def test_merge_into_archive_modifies_inner_sarc_then_recompresses(self) -> None:
    archive_path = self.write_original_archive({"one.bin": b"one", "two.bin": b"two"})
    self.write_mod_file("one.bin", b"ONE")
    lookup = mods.get_sarc_file_info(archive_path)

    mods.merge_into_archive("one.bin", "archives/test.ee", lookup)

    output_path = mods.MOD_PATH / "archives/test.ee"
    _, is_aaf, contents = read_sarc_contents(output_path)
    self.assertTrue(is_aaf)
    self.assertEqual(contents, {"one.bin": b"ONE", "two.bin": b"two"})

  def test_expand_into_archive_updates_inner_offsets_then_recompresses(self) -> None:
    self.write_original_archive({"one.bin": b"one", "two.bin": b"two"})
    self.write_mod_file("one.bin", b"expanded")

    mods.expand_into_archive("one.bin", "archives/test.ee")

    output_path = mods.MOD_PATH / "archives/test.ee"
    _, is_aaf, contents = read_sarc_contents(output_path)
    self.assertTrue(is_aaf)
    self.assertEqual(contents, {"one.bin": b"expanded", "two.bin": b"two"})

  def test_recreate_archive_rebuilds_inner_sarc_then_recompresses(self) -> None:
    self.write_original_archive({"one.bin": b"one", "two.bin": b"two"})
    self.write_mod_file("one.bin", b"a longer replacement")

    mods.recreate_archive(["one.bin"], "archives/test.ee")

    output_path = mods.MOD_PATH / "archives/test.ee"
    wrapped_data = output_path.read_bytes()
    _, is_aaf, contents = read_sarc_contents(output_path)
    self.assertTrue(is_aaf)
    self.assertEqual(contents, {"one.bin": b"a longer replacement", "two.bin": b"two"})
    self.assertEqual(extract_aaf(ArchiveFile(io.BytesIO(wrapped_data)))[:8], b"\x04\x00\x00\x00SARC")


if __name__ == "__main__":
  unittest.main()

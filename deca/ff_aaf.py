import io
import struct
import zlib
from deca.file import ArchiveFile
from deca.util import align_to


AAF_MAGIC = b'AAF\x00'
AAF_VERSION = 1
AAF_ID = b'AVALANCHEARCHIVEFORMATISCOOL'
AAF_SECTION_SIZE = 32 * 1024 * 1024
AAF_SECTION_MAGIC = b'EWAM'
AAF_ALIGNMENT = 16
AAF_PADDING_BYTE = b'0'


class AafHeader:
    def __init__(self):
        self.magic = None
        self.version = None
        self.aic = None
        self.size_u = None
        self.section_max_size_u = None
        self.section_count = None


def load_aaf_header(fin):
    with ArchiveFile(fin) as f:
        aafh = AafHeader()
        aafh.magic = f.read(4)
        aafh.version = f.read_u32()
        aafh.aic = f.read(8 + 16 + 4)
        aafh.size_u = f.read_u32()  # uncompressed length, whole file
        aafh.section_size = f.read_u32()  # uncompress length, max any section?
        aafh.section_count = f.read_u32()  # section count? Normally 1 (2-5 found), number of 32MiB blocks?
    return aafh


def extract_aaf(src):
    f = src
    magic = f.read(4)
    version = f.read_u32()
    aic = f.read(8 + 16 + 4)
    uncompressed_length = f.read_u32()  # uncompressed length, whole file
    section_size = f.read_u32()  # uncompress length, max any section?
    section_count = f.read_u32()  # section count? Normally 1 (2-5 found), number of 32MiB blocks?

    if not magic.upper().startswith(b'AAF'):
        raise ValueError('Not an AAF file: {!r}'.format(magic))
    if version != AAF_VERSION:
        raise ValueError('Unsupported AAF version: {}'.format(version))

    sections = []
    for i in range(section_count):
        section_start = f.tell()
        section_compressed_length = f.read_u32()  # compressed length no including padding
        section_uncompressed_length = f.read_u32()  # full length?
        section_length_with_header = f.read_u32()  # padded length + 16
        magic_ewam = f.read(4)  # 'EWAM'
        buf_in = f.read(section_compressed_length)
        buf_out = zlib.decompress(buf_in, -15)
        if magic_ewam != AAF_SECTION_MAGIC:
            raise ValueError('Invalid AAF section magic: {!r}'.format(magic_ewam))
        sections.append(buf_out)

        if len(buf_out) != section_uncompressed_length:
            # raise Exception(
            print('WARNING: Uncompress Failed Section {}/{}: scs:{}, sus:{}, bl:{}, m:{}'.format(
                i, section_count, section_compressed_length, section_uncompressed_length, len(buf_out),
                magic_ewam,
            ))

            if len(buf_out) > section_uncompressed_length:
                raise Exception("len(buf_out) > section_uncompressed_length")

            # buffer_out += b'\x00' * (section_compressed_length - len(buf_out))

        f.seek(section_length_with_header + section_start)
        # print(section_compressed_length, section_uncompressed_length, section_length_with_header, magic_ewam)

    buffer_out = b''.join(sections)
    if len(buffer_out) != uncompressed_length:
        raise ValueError(
            'AAF size mismatch: header says {}, extracted {}'.format(uncompressed_length, len(buffer_out)))
    return buffer_out


def compress_aaf(src, dst, section_size=AAF_SECTION_SIZE, compression_level=6):
    """Write *src* to *dst* in the AAF container format used by the game.

    ``src`` and ``dst`` are seekable binary file objects.  Level 6 raw DEFLATE
    reproduces the game's/Luke's encoding for identical input.
    """
    src_start = src.tell()
    src.seek(0, io.SEEK_END)
    uncompressed_length = src.tell() - src_start
    src.seek(src_start)

    if uncompressed_length > 0xffffffff:
        raise ValueError('AAF files larger than 4 GiB are not supported')
    if section_size <= 0 or section_size > 0xffffffff:
        raise ValueError('Invalid AAF section size: {}'.format(section_size))

    section_count = (uncompressed_length + section_size - 1) // section_size
    dst.write(AAF_MAGIC)
    dst.write(struct.pack('<I', AAF_VERSION))
    dst.write(AAF_ID)
    dst.write(struct.pack('<III', uncompressed_length, section_size, section_count))

    for _ in range(section_count):
        section = src.read(section_size)
        compressor = zlib.compressobj(compression_level, zlib.DEFLATED, -15)
        compressed = compressor.compress(section) + compressor.flush()
        section_length = align_to(16 + len(compressed), AAF_ALIGNMENT)

        dst.write(struct.pack(
            '<III4s', len(compressed), len(section), section_length, AAF_SECTION_MAGIC))
        dst.write(compressed)
        # The engine's encoder pads sections with ASCII '0', not NUL bytes.
        dst.write(AAF_PADDING_BYTE * (section_length - 16 - len(compressed)))


def compress_aaf_bytes(data, section_size=AAF_SECTION_SIZE, compression_level=6):
    """Return *data* encoded as an AAF container."""
    dst = io.BytesIO()
    compress_aaf(io.BytesIO(data), dst, section_size, compression_level)
    return dst.getvalue()

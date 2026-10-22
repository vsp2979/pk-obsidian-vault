"""
Google Spatial Media 360 Metadata Injector.
Injects Spherical Video v2 / Google Spatial Media XML metadata into MP4 files.
Enables native 360 playback on YouTube, Facebook, VLC, and media players without re-encoding.
"""

import os
import struct
from pathlib import Path

# Google Spherical Video UUID: ffcc8263-f855-4a93-8814-58a48e632a95
SPHERICAL_UUID = bytes.fromhex("ffcc8263f8554a93881458a48e632a95")

SPHERICAL_XML = (
    '<?xml version="1.0"?>'
    '<rdf:SphericalVideo'
    ' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
    ' xmlns:GSpherical="http://ns.google.com/videos/1.0/spherical/">'
    '<GSpherical:Spherical>true</GSpherical:Spherical>'
    '<GSpherical:Stitched>true</GSpherical:Stitched>'
    '<GSpherical:StitchingSoftware>OmniView360</GSpherical:StitchingSoftware>'
    '<GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>'
    '</rdf:SphericalVideo>'
).encode("utf-8")


class SpatialMetadataInjector:
    def __init__(self):
        pass

    def build_uuid_atom(self):
        """
        Builds the custom UUID atom containing Google Spherical Video XML.
        Format: [4 bytes size] [4 bytes 'uuid'] [16 bytes UUID] [XML content]
        """
        content = SPHERICAL_UUID + SPHERICAL_XML
        total_size = 4 + 4 + len(content)
        return struct.pack(">I4s", total_size, b"uuid") + content

    def inject(self, input_file, output_file):
        """
        Parses MP4 top-level atoms and injects the spherical UUID atom into the 'moov' atom.
        Writes out the resulting MP4.
        """
        in_path = Path(input_file)
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        uuid_box = self.build_uuid_atom()

        with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
            file_size = in_path.stat().st_size
            while fin.tell() < file_size:
                header = fin.read(8)
                if len(header) < 8:
                    break
                atom_size, atom_type = struct.unpack(">I4s", header)
                
                # Extended size (64-bit)
                if atom_size == 1:
                    ext_size = struct.unpack(">Q", fin.read(8))[0]
                    payload_size = ext_size - 16
                elif atom_size == 0:
                    payload_size = file_size - fin.tell()
                else:
                    payload_size = atom_size - 8

                if atom_type == b"moov":
                    # Read entire moov atom payload
                    moov_payload = fin.read(payload_size)
                    
                    # Check if UUID already present
                    if SPHERICAL_UUID not in moov_payload:
                        # Append uuid box to moov
                        new_moov_payload = moov_payload + uuid_box
                        new_moov_size = 8 + len(new_moov_payload)
                        fout.write(struct.pack(">I4s", new_moov_size, b"moov"))
                        fout.write(new_moov_payload)
                    else:
                        # Already has spherical metadata
                        fout.write(header)
                        fout.write(moov_payload)
                else:
                    # Write atom header and copy payload in chunks
                    fout.write(header)
                    remaining = payload_size
                    chunk_size = 4 * 1024 * 1024
                    while remaining > 0:
                        take = min(remaining, chunk_size)
                        buf = fin.read(take)
                        if not buf:
                            break
                        fout.write(buf)
                        remaining -= len(buf)

        return str(out_path)

    def verify(self, file_path):
        """
        Quick check whether an MP4 contains 360 Spherical metadata.
        """
        with open(file_path, "rb") as f:
            chunk = f.read(64 * 1024 * 1024) # Scan first 64MB
            return (b"SphericalVideo" in chunk or SPHERICAL_UUID in chunk)

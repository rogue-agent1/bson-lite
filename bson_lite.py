#!/usr/bin/env python3
"""Minimal BSON encoder/decoder."""
import struct

def encode(doc: dict) -> bytes:
    body = b""
    for key, val in doc.items():
        k = key.encode() + b"\x00"
        if isinstance(val, bool):
            body += b"\x08" + k + (b"\x01" if val else b"\x00")
        elif isinstance(val, int):
            if -2**31 <= val < 2**31:
                body += b"\x10" + k + struct.pack("<i", val)
            else:
                body += b"\x12" + k + struct.pack("<q", val)
        elif isinstance(val, float):
            body += b"\x01" + k + struct.pack("<d", val)
        elif isinstance(val, str):
            b = val.encode()
            body += b"\x02" + k + struct.pack("<i", len(b)+1) + b + b"\x00"
        elif isinstance(val, bytes):
            body += b"\x05" + k + struct.pack("<i", len(val)) + b"\x00" + val
        elif isinstance(val, list):
            arr_doc = {str(i): v for i, v in enumerate(val)}
            body += b"\x04" + k + encode(arr_doc)
        elif isinstance(val, dict):
            body += b"\x03" + k + encode(val)
        elif val is None:
            body += b"\x0a" + k
        else:
            raise TypeError(f"Cannot BSON encode {type(val)}")
    body += b"\x00"
    return struct.pack("<i", len(body) + 4) + body

def decode(data: bytes) -> dict:
    doc, _ = _decode_doc(data, 0)
    return doc

def _decode_doc(data, pos):
    size = struct.unpack("<i", data[pos:pos+4])[0]
    end = pos + size
    pos += 4
    doc = {}
    while pos < end - 1:
        elem_type = data[pos]; pos += 1
        null = data.index(b"\x00", pos)
        key = data[pos:null].decode(); pos = null + 1
        if elem_type == 0x01:
            doc[key] = struct.unpack("<d", data[pos:pos+8])[0]; pos += 8
        elif elem_type == 0x02:
            slen = struct.unpack("<i", data[pos:pos+4])[0]; pos += 4
            doc[key] = data[pos:pos+slen-1].decode(); pos += slen
        elif elem_type == 0x03:
            subdoc, pos = _decode_doc(data, pos)
            doc[key] = subdoc
        elif elem_type == 0x04:
            subdoc, pos = _decode_doc(data, pos)
            doc[key] = [subdoc[str(i)] for i in range(len(subdoc))]
        elif elem_type == 0x05:
            blen = struct.unpack("<i", data[pos:pos+4])[0]; pos += 4
            pos += 1  # subtype
            doc[key] = data[pos:pos+blen]; pos += blen
        elif elem_type == 0x08:
            doc[key] = data[pos] != 0; pos += 1
        elif elem_type == 0x0a:
            doc[key] = None
        elif elem_type == 0x10:
            doc[key] = struct.unpack("<i", data[pos:pos+4])[0]; pos += 4
        elif elem_type == 0x12:
            doc[key] = struct.unpack("<q", data[pos:pos+8])[0]; pos += 8
    return doc, end

if __name__ == "__main__":
    doc = {"name": "test", "age": 30, "active": True}
    data = encode(doc)
    print(f"Encoded ({len(data)} bytes): {data.hex()}")
    print(f"Decoded: {decode(data)}")

def test():
    doc = {"str": "hello", "int": 42, "float": 3.14, "bool": True, "none": None,
           "list": [1, 2, 3], "nested": {"a": 1}, "bytes": b"\x00\x01", "big": 2**40}
    result = decode(encode(doc))
    assert result["str"] == "hello"
    assert result["int"] == 42
    assert abs(result["float"] - 3.14) < 1e-10
    assert result["bool"] is True
    assert result["none"] is None
    assert result["list"] == [1, 2, 3]
    assert result["nested"] == {"a": 1}
    assert result["bytes"] == b"\x00\x01"
    assert result["big"] == 2**40
    print("  bson_lite: ALL TESTS PASSED")

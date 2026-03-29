#!/usr/bin/env python3
"""BSON encoder/decoder (subset). Zero dependencies."""
import struct, sys, time

def encode(doc):
    body = bytearray()
    for key, value in doc.items():
        key_bytes = key.encode() + b"\x00"
        if isinstance(value, float):
            body.append(0x01); body.extend(key_bytes); body.extend(struct.pack("<d", value))
        elif isinstance(value, str):
            body.append(0x02); body.extend(key_bytes)
            vb = value.encode() + b"\x00"
            body.extend(struct.pack("<i", len(vb))); body.extend(vb)
        elif isinstance(value, dict):
            body.append(0x03); body.extend(key_bytes); body.extend(encode(value))
        elif isinstance(value, list):
            body.append(0x04); body.extend(key_bytes)
            arr_doc = {str(i): v for i, v in enumerate(value)}
            body.extend(encode(arr_doc))
        elif isinstance(value, bytes):
            body.append(0x05); body.extend(key_bytes)
            body.extend(struct.pack("<i", len(value))); body.append(0x00); body.extend(value)
        elif isinstance(value, bool):
            body.append(0x08); body.extend(key_bytes); body.append(1 if value else 0)
        elif value is None:
            body.append(0x0A); body.extend(key_bytes)
        elif isinstance(value, int):
            if -2147483648 <= value <= 2147483647:
                body.append(0x10); body.extend(key_bytes); body.extend(struct.pack("<i", value))
            else:
                body.append(0x12); body.extend(key_bytes); body.extend(struct.pack("<q", value))
    body.append(0x00)
    return struct.pack("<i", len(body)+4) + bytes(body)

def decode(data, offset=0):
    doc_len = struct.unpack_from("<i", data, offset)[0]
    pos = offset + 4; result = {}
    while pos < offset + doc_len - 1:
        elem_type = data[pos]; pos += 1
        key_end = data.index(b"\x00"[0], pos)
        key = data[pos:key_end].decode(); pos = key_end + 1
        if elem_type == 0x01:
            result[key] = struct.unpack_from("<d", data, pos)[0]; pos += 8
        elif elem_type == 0x02:
            slen = struct.unpack_from("<i", data, pos)[0]; pos += 4
            result[key] = data[pos:pos+slen-1].decode(); pos += slen
        elif elem_type == 0x03:
            sub, sub_len = _decode_with_len(data, pos)
            result[key] = sub; pos += sub_len
        elif elem_type == 0x04:
            sub, sub_len = _decode_with_len(data, pos)
            result[key] = [sub[str(i)] for i in range(len(sub))]
            pos += sub_len
        elif elem_type == 0x05:
            blen = struct.unpack_from("<i", data, pos)[0]; pos += 5
            result[key] = data[pos:pos+blen]; pos += blen
        elif elem_type == 0x08:
            result[key] = bool(data[pos]); pos += 1
        elif elem_type == 0x0A:
            result[key] = None
        elif elem_type == 0x10:
            result[key] = struct.unpack_from("<i", data, pos)[0]; pos += 4
        elif elem_type == 0x12:
            result[key] = struct.unpack_from("<q", data, pos)[0]; pos += 8
        else: break
    return result

def _decode_with_len(data, offset):
    doc_len = struct.unpack_from("<i", data, offset)[0]
    return decode(data, offset), doc_len

def dumps(doc): return encode(doc)
def loads(data): return decode(data)

if __name__ == "__main__":
    doc = {"name": "Alice", "age": 30, "scores": [95, 87, 92], "active": True}
    enc = dumps(doc)
    print(f"BSON: {len(enc)} bytes")
    dec = loads(enc)
    print(f"Decoded: {dec}")

from bson_lite import dumps, loads
doc = {"name": "Alice", "age": 30, "active": True, "score": 3.14, "tags": ["a", "b"], "data": None}
enc = dumps(doc)
dec = loads(enc)
assert dec["name"] == "Alice"
assert dec["age"] == 30
assert dec["active"] == True
assert abs(dec["score"] - 3.14) < 0.01
assert dec["tags"] == ["a", "b"]
assert dec["data"] is None
print("BSON tests passed")
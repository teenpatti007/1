# -*- coding: utf-8 -*-
"""Verify the device-locked passcode logic with a mocked Firebase."""
import sys, os, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugin.video.moviehub"))
import main

FB = "https://example.firebaseio.com"

# In-memory fake Firebase passcodes store
STORE = {}

def fake_get(code, fb):
    if code in STORE:
        return dict(STORE[code])
    return None

patched_patch = {"calls": []}
def fake_patch(code, fb, payload):
    patched_patch["calls"].append((code, payload))
    STORE.setdefault(code, {})
    STORE[code].update(payload)

main._fb_get = fake_get
main._fb_patch = fake_patch

mac_a = "AA:BB:CC:DD:EE:FF"
mac_b = "11:22:33:44:55:66"

def check(name, got, exp):
    ok = got == exp
    print(("[PASS] " if ok else "[FAIL] ") + name + " -> got=%s exp=%s" % (got, exp))
    return ok

# 1) fresh code on device A -> ok, registers mac
STORE.clear(); patched_patch["calls"] = []
STORE["1234"] = {"active": True}  # admin issued this code
r = main.validate_passcode("1234", mac_a, FB)
check("fresh code registers", r, "ok")
check("mac written", STORE.get("1234", {}).get("mac"), mac_a)

# 2) same device A again -> ok, no new patch
patched_patch["calls"] = []
r = main.validate_passcode("1234", mac_a, FB)
check("same device re-validate", r, "ok")
check("no re-registration", len(patched_patch["calls"]), 0)

# 3) different device B -> used_elsewhere
r = main.validate_passcode("1234", mac_b, FB)
check("different device rejected", r, "used_elsewhere")

# 4) unknown code -> invalid
r = main.validate_passcode("0000", mac_a, FB)
check("unknown code invalid", r, "invalid")

# 5) inactive code -> invalid
STORE["9999"] = {"active": False, "mac": mac_a}
r = main.validate_passcode("9999", mac_a, FB)
check("inactive code invalid", r, "invalid")

# 6) device mac format
m = main.get_device_mac()
print("device mac:", m, "(len %d)" % len(m))
check("mac has 5 colons", m.count(":"), 5)

print("\nALL PASSCODE TESTS DONE")

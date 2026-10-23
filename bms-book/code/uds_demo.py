#!/usr/bin/env python3
"""Mini UDS ECU (dict service table) + mini tester: sessions, 0x27 seed-key,
DID read, routine control. Teaching demo - run: python code/uds_demo.py
"""

DEFAULT, PROGRAMMING, EXTENDED = 0x01, 0x02, 0x03

NRC_LENGTH = 0x13      # incorrect message length or invalid format
NRC_RANGE = 0x31       # request out of range
NRC_SECURITY = 0x33    # security access denied (locked / wrong level)
NRC_KEY = 0x35         # invalid key
NRC_ATTEMPTS = 0x36    # exceeded number of attempts
NRC_DELAY = 0x37       # required time delay not expired
NRC_SESSION = 0x7F     # service not supported in active session

MAX_FAILS = 3
LOCKOUT_MS = 10_000    # teaching value; production ECUs use minutes


def key_from_seed(seed: int) -> int:
    return (((seed << 3) | 0x5A) & 0xFFFF) ^ 0xA5A5


SEEDS = {1: 0x1234, 2: 0xBEEF}


class MiniUDS:
    """Tiny ECU. Requests/responses are simplified single-byte streams."""

    DIDS = {
        0xF100: ((DEFAULT, EXTENDED, PROGRAMMING), b"\x0D\x75"),  # 3445 mV, max cell
        0xF101: ((DEFAULT, EXTENDED, PROGRAMMING), b"\x00\x62"),  # 98 %, SOH
        0xF102: ((PROGRAMMING,), b"1.0.0"),                      # firmware version
    }
    ROUTINES = {0x0203: "insulation self-check"}

    def __init__(self) -> None:
        self.session = DEFAULT
        self.level = 0              # unlocked security level, 0 = locked
        self.pending_level = 0
        self.seed = 0
        self.fails = 0
        self.clock_ms = 0
        self.locked_until_ms = 0
        self.handlers = {
            0x10: self._session_ctrl,
            0x22: self._read_did,
            0x27: self._security_access,
            0x31: self._routine_ctrl,
        }

    def tick(self, ms: int) -> None:
        self.clock_ms += ms

    @staticmethod
    def _neg(svc: int, nrc: int) -> bytes:
        return bytes([0x7F, svc, nrc])

    def request(self, req: bytes) -> bytes:
        handler = self.handlers.get(req[0])
        if handler is None:
            return self._neg(req[0], NRC_SESSION)
        return handler(req)

    # -- services ---------------------------------------------------
    def _session_ctrl(self, req: bytes) -> bytes:
        if len(req) != 2:
            return self._neg(0x10, NRC_LENGTH)
        target = req[1]
        if target not in (DEFAULT, EXTENDED, PROGRAMMING):
            return self._neg(0x10, NRC_RANGE)
        if target == PROGRAMMING:
            if self.session != EXTENDED:
                return self._neg(0x10, NRC_SESSION)
            if self.level < 2:
                return self._neg(0x10, NRC_SECURITY)
        self.session = target
        self.level = 0              # every session change resets security
        return bytes([0x50, target])

    def _security_access(self, req: bytes) -> bytes:
        if self.session == DEFAULT:
            return self._neg(0x27, NRC_SESSION)
        if self.clock_ms < self.locked_until_ms:
            return self._neg(0x27, NRC_DELAY)
        sub = req[1]
        if sub % 2 == 1:                                # request seed
            level = (sub + 1) // 2
            if level not in SEEDS:
                return self._neg(0x27, NRC_RANGE)
            if self.level >= level:
                return bytes([0x67, sub, 0x00, 0x00])   # already unlocked
            self.pending_level = level
            self.seed = SEEDS[level]
            return bytes([0x67, sub]) + self.seed.to_bytes(2, "big")
        if len(req) != 4:                               # send key
            return self._neg(0x27, NRC_LENGTH)
        level = sub // 2
        if level != self.pending_level:
            return self._neg(0x27, NRC_RANGE)
        key = int.from_bytes(req[2:4], "big")
        if key != key_from_seed(self.seed):
            self.fails += 1
            if self.fails >= MAX_FAILS:
                self.locked_until_ms = self.clock_ms + LOCKOUT_MS
                self.fails = 0
                return self._neg(0x27, NRC_ATTEMPTS)
            return self._neg(0x27, NRC_KEY)
        self.level = level
        self.fails = 0
        return bytes([0x67, sub])

    def _read_did(self, req: bytes) -> bytes:
        if len(req) != 3:
            return self._neg(0x22, NRC_LENGTH)
        did = (req[1] << 8) | req[2]
        if did not in self.DIDS:
            return self._neg(0x22, NRC_RANGE)
        sessions, data = self.DIDS[did]
        if self.session not in sessions:
            return self._neg(0x22, NRC_SECURITY)
        return bytes([0x62, req[1], req[2]]) + data

    def _routine_ctrl(self, req: bytes) -> bytes:
        if len(req) != 4 or req[1] != 0x01:
            return self._neg(0x31, NRC_LENGTH)
        rid = (req[2] << 8) | req[3]
        if rid not in self.ROUTINES:
            return self._neg(0x31, NRC_RANGE)
        if self.session == DEFAULT:
            return self._neg(0x31, NRC_SESSION)
        return bytes([0x71, 0x01, req[2], req[3], 0x00])


def show(req: bytes, resp: bytes) -> None:
    print("-->", req.hex(" ").upper())
    print("<--", resp.hex(" ").upper())


def main() -> None:
    assert key_from_seed(0x1234) == 0x345F
    assert key_from_seed(0xBEEF) == 0x52DF

    ecu = MiniUDS()

    def xchg(req: bytes, expect: bytes) -> None:
        resp = ecu.request(req)
        show(req, resp)
        assert resp == expect, f"want {expect.hex()} got {resp.hex()}"

    print("== scenario: tester connects to BMS ==")
    xchg(b"\x10\x03", b"\x50\x03")                    # enter extended session
    xchg(b"\x27\x01", b"\x67\x01\x12\x34")             # seed, security level 1
    xchg(b"\x27\x02\x00\x00", b"\x7F\x27\x35")         # wrong key (fail 1/3)
    xchg(b"\x27\x02\x34\x5F", b"\x67\x02")             # right key, level 1 open
    xchg(b"\x22\xF1\x00", b"\x62\xF1\x00\x0D\x75")     # max cell voltage 3445 mV
    xchg(b"\x22\xF1\x01", b"\x62\xF1\x01\x00\x62")     # SOH 98 %
    xchg(b"\x22\xF1", b"\x7F\x22\x13")                 # bad length
    xchg(b"\x22\xF1\x99", b"\x7F\x22\x31")             # unknown DID
    xchg(b"\x31\x01\x02\x03", b"\x71\x01\x02\x03\x00") # insulation self-check
    xchg(b"\x22\xF1\x02", b"\x7F\x22\x33")             # firmware DID: programming only
    xchg(b"\x10\x02", b"\x7F\x10\x33")                 # level 1 cannot open programming
    xchg(b"\x27\x03", b"\x67\x03\xBE\xEF")             # seed, security level 2
    xchg(b"\x27\x04\x52\xDF", b"\x67\x04")             # key for 0xBEEF
    xchg(b"\x10\x02", b"\x50\x02")                     # enter programming session
    assert ecu.level == 0, "security resets on session change"
    xchg(b"\x22\xF1\x02", b"\x62\xF1\x02\x31\x2E\x30\x2E\x30")  # "1.0.0"

    print(f"== lockout after {MAX_FAILS} wrong keys ==")
    ecu2 = MiniUDS()
    ecu2.request(b"\x10\x03")
    for _ in range(MAX_FAILS - 1):
        ecu2.request(b"\x27\x01")
        assert ecu2.request(b"\x27\x02\x00\x00") == b"\x7F\x27\x35"
    ecu2.request(b"\x27\x01")
    resp = ecu2.request(b"\x27\x02\x00\x00")
    show(b"\x27\x02\x00\x00", resp)
    assert resp == b"\x7F\x27\x36"                     # attempts exceeded, locked
    resp = ecu2.request(b"\x27\x01")
    show(b"\x27\x01", resp)
    assert resp == b"\x7F\x27\x37"                     # 10 s delay not expired
    ecu2.tick(LOCKOUT_MS)
    resp = ecu2.request(b"\x27\x01")
    show(b"\x27\x01", resp)
    assert resp == b"\x67\x01\x12\x34"                 # seed served again

    print("[PASS] sessions gate 0x10; 0x27 seed-key + lockout; "
          "session-aware DIDs; 0x31 routine; NRC table exercised")


if __name__ == "__main__":
    main()

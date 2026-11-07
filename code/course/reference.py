"""Reference arithmetic and data rules for a virtual 4S training pack.

Teaching values only. This module does not drive hardware.
"""
from __future__ import annotations

import binascii
import math
import struct


def pack_voltage(cells):
    return sum(cells)


def calibrate(raw_v, offset_v):
    return raw_v - offset_v


def sample_ok(cells, sampled_s, now_s, max_age_s):
    return (len(cells) == 4 and all(math.isfinite(v) and 0 <= v <= 5 for v in cells)
            and all(math.isfinite(v) for v in (sampled_s, now_s, max_age_s))
            and max_age_s >= 0 and 0 <= now_s - sampled_s <= max_age_s + 1e-9)


def violations(cells, low_v, high_v):
    return min(cells) <= low_v or max(cells) >= high_v


def trip_at(times, unsafe, delay_s):
    """Time of a continuously unsafe sample span, or None; valid ordered samples."""
    since = None
    for t, bad in zip(times, unsafe, strict=True):
        since = t if bad and since is None else since if bad else None
        if since is not None and t - since >= delay_s - 1e-9:
            return t
    return None


def can_reset(manual, safe, feedback_open):
    return bool(manual and safe and feedback_open)


def soc_step(soc, current_a, dt_s, capacity_ah):
    if capacity_ah <= 0 or dt_s < 0 or not all(math.isfinite(x) for x in (soc, current_a, dt_s, capacity_ah)):
        raise ValueError("finite inputs, positive capacity and nonnegative dt required")
    return max(0.0, min(1.0, soc - current_a * dt_s / (3600 * capacity_ah)))


def drift(offset_a, hours, capacity_ah):
    return offset_a * hours / capacity_ah  # fraction, not percentage points


def ocv_soc(voltage, low_v, high_v):
    """Linear toy lookup, only meaningful for the stated rested-cell exercise."""
    return max(0.0, min(1.0, (voltage - low_v) / (high_v - low_v)))


def charge_allowed(temp_c, sample_valid, requested):
    return bool(sample_valid and requested and 0 <= temp_c <= 45)


def balance_hours(delta_ah, current_a):
    if not all(math.isfinite(x) for x in (delta_ah, current_a)) or delta_ah < 0 or current_a <= 0:
        raise ValueError("nonnegative charge and positive bleed current required")
    return delta_ah / current_a


def remaining_ah(capacities, socs):
    return min(q * s for q, s in zip(capacities, socs, strict=True))


def encode(voltage_v, current_a, sequence, quality=1):
    payload = struct.pack('<HhBB', round(voltage_v * 1000), round(current_a * 1000), sequence, quality)
    return payload + struct.pack('<H', binascii.crc_hqx(payload, 0xFFFF))


def decode(frame):
    if len(frame) != 8:
        raise ValueError("length")
    payload, crc = frame[:6], struct.unpack('<H', frame[6:])[0]
    if binascii.crc_hqx(payload, 0xFFFF) != crc:
        raise ValueError("crc")
    mv, ma, sequence, quality = struct.unpack('<HhBB', payload)
    if quality != 1 or not 0 <= mv <= 20000:
        raise ValueError("quality/range")
    return mv / 1000, ma / 1000, sequence


def sequence_ok(previous, current):
    return previous is None or current == (previous + 1) % 256


def remote_enable(local_safe, fresh, requested):
    return bool(local_safe and fresh and requested)

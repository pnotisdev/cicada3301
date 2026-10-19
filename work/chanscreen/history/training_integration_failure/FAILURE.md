# Training adapter failure (not a held-out power result)

First training-only invocation attempted 8 tasks; each stopped before its first
score because M04 banks use bytes and np.ascontiguousarray(bytes,dtype=int32)
attempts to parse the bytes as a scalar integer. No calibration or held-out seeds
had been run. G0/G1 numerical tests all passed, but used list keys and missed
this input-representation case. Raw started markers and original adapter/manifest
are preserved here. Exception type ValueError; no complete score records existed.

Correction: convert bytes/bytearray to list at the ctypes boundary. Added parity
unit test for these types. This is training development, not threshold/seed tuning.
Repeat the SAME training seeds only; no replacement seeds. Existing G1 result
hashes describe the original adapter; a new suite record covers the correction.
No Rust, probabilistic model, gate threshold or seed changed.

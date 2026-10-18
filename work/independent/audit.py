"""Human-run deterministic audit: PGP byte claim and affine-screen redundancy."""
import random

from manual_common import execute, lp_module


def convolution(p, k, multiplier=1):
    out = [0.0] * 29
    for a, pa in enumerate(p):
        for b, pb in enumerate(k):
            out[(a + multiplier * b) % 29] += pa * pb
    return out


def population_ioc(probabilities):
    return 29 * sum(p * p for p in probabilities)


def audit(run):
    lp = lp_module()
    identifier = "7A35090F"
    raw = bytes.fromhex(identifier)
    expected = b"z5\t\x0f"
    if raw != expected or bytes.fromhex("7A357A35") != b"z5z5":
        raise AssertionError("Byte conversion control failed")
    run.log("7A35090F -> 7A 35 09 0F -> 'z', '5', TAB, SHIFT IN (U+000F).")
    run.log("It does NOT decode to z5z5. z5z5 would be 7A357A35; ASCII uppercase Z5 starts 5A35.")
    run.log("7A35090F is normally cited as a SHORT OpenPGP KEY identifier, not the signature's contents.")
    run.log("This does not verify any signature/key. Authentication needs an independently trusted full fingerprint and actual signature verification.")
    run.log("Z5 books: user-supplied title lead, bibliography and source/provenance NOT verified here.")
    run.log("A fixed predeclared two-byte prefix has probability 1/65536 under uniform bytes.")
    run.log("That is NOT a valid p-value for choosing a title AFTER inspecting the ID; the title/encoding choices were not predeclared.")

    # Positive control: encryption, including skipped key draws, then outer affine map.
    # Check every nonzero multiplier and every shift. No LP2 ciphertext is searched.
    rng = random.Random(73301)
    plain = lp.word_to_key("BELIEVENOTHINGEXCEPTWHATYOUKNOWTOBETRUE") * 12
    key = [rng.randrange(29) for _ in range(len(plain) * 4)]
    inner, used, j = [], [], 0
    for p in plain:
        while True:
            k = key[j]
            j += 1
            y = (p + k) % 29
            if not inner or y != inner[-1] or rng.random() >= 0.81:
                break
        inner.append(y)
        used.append(k)
    checked = 0
    for a in range(1, 29):
        inv = pow(a, -1, 29)
        for b in range(29):
            sigma = [(a * x + b) % 29 for x in range(29)]
            assert sorted(sigma) == list(range(29))
            cipher = [sigma[x] for x in inner]
            relabelled = [((inv * (c - b)) - k) % 29 for c, k in zip(cipher, used)]
            direct = [(c - a * k) % 29 for c, k in zip(cipher, used)]
            assert relabelled == plain
            assert direct == [(a * p + b) % 29 for p in plain]
            assert abs(lp.ioc(direct) - lp.ioc(plain)) < 1e-12
            assert [x == y for x, y in zip(inner, inner[1:])] == [x == y for x, y in zip(cipher, cipher[1:])]
            # The skip feasibility test itself is preserved for every p,k,prev.
            for p in range(29):
                for k in range(29):
                    prev = (7 * p + k) % 29
                    assert (((p + k) % 29) == prev) == (((a * p + b + a * k) % 29) == sigma[prev])
            checked += 1
        run.check()
    # Negative control: a bijective but non-affine map has no constant key multiplier
    # which removes the key for ALL plaintexts and key values.
    sigma = list(range(29))
    sigma[0], sigma[1] = sigma[1], sigma[0]
    increments = {(sigma[(p + 1) % 29] - sigma[p]) % 29 for p in range(29)}
    assert len(increments) > 1
    assert not any(all((sigma[(p + k) % 29] - m * k) % 29 == sigma[p]
                      for p in range(29) for k in range(29)) for m in range(1, 29))
    run.log(f"Affine identity controls pass for {checked} maps, including all shifts and Atbash.")
    run.log("Proof: c=a(p+m*k)+b => c-(a*m)*k=a*p+b. IoC is unchanged by the final affine permutation.")
    run.log("Therefore outer affine maps add NO key-family coverage to an existing all-28-multiplier screen, at the same windows/models/offsets.")
    run.log("A non-affine swap control fails that identity. Non-affine keyword alphabets remain genuinely different.")
    run.log("This is an algebraic scope correction, NOT a rerun or assessment of DeepSeek's current process.")
    run.save("audit.json", dict(identifier=identifier, bytes=list(raw), ascii_escaped=repr(raw),
                                repeated_z5_hex="7A357A35", book_provenance="not verified",
                                affine_maps_checked=checked, nonaffine_increment_witness=sorted(increments),
                                lp2_searched=False))


if __name__ == "__main__":
    raise SystemExit(execute("audit", audit))

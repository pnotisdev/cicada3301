// CUDA port of the kscreen IoC beam decoder (ioc_beam in src/main.rs). One thread = one (keystream item, start
// offset, multiplier) task; it loops over the anti-repeat models and the windows. The control flow follows the
// Rust code statement by statement (same state vector operations in the same order, a stable sort at the beam cut)
// so that the CPU engine and this kernel give the same s and `used` for every decode. gpu.py compiles it with NVRTC
// and prepends the #defines:
//   NEED   key values per task (the CPU engine's `need`)      BEAM   beam width
//   NW     windows                                            NMODEL anti-repeat models, NMULT multipliers
//   MODE   0 = file/rand keystreams read from `lib`, 1 = linear recurrence of order ORD, 2 = polynomial of degree ORD
//   HBINS  histogram bins                                     DUMP   1 = also write s and used of every decode
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;

#define Q 29
#ifndef BACK
#define BACK 0          // 1 = the key runs backward through the text (dir=back), see src/main.rs
#endif
#define CAP (3 * BEAM)

struct St {
    u32 j;
    u32 s;
    u16 cnt[Q];
};

__device__ __forceinline__ u32 sub29(u32 c, u32 k) { return c >= k ? c - k : c + Q - k; }
__device__ __forceinline__ u32 add29(u32 t, u32 k) { u32 r = t + k; return r >= Q ? r - Q : r; }
__device__ __forceinline__ void take(St &st, u32 t, u32 nj) {
    st.s += 2u * st.cnt[t];
    st.cnt[t] += 1;
    st.j = nj;
}

#define MK(jj) (((u32)kp[(jj)] * m) % Q)

// Returns the best coincidence sum s; *used is the number of runes decoded (n, or abort_at, or max(i, 2) if the beam died).
__device__ u32 beam_decode(const u8 *__restrict__ c, const signed char *__restrict__ pv, const u8 *__restrict__ kp, u32 m, int model, int n,
                           int abort_at, u32 abort_s, u32 *used) {
    St cur[CAP];
    St ext[2 * BEAM];
    int nc = 1;
    cur[0].j = 0;
    cur[0].s = 0;
    for (int x = 0; x < Q; x++) cur[0].cnt[x] = 0;
    for (int i = 0; i < n; i++) {
        const u32 ci = c[i];
        const int prev = (int)pv[i];                 // the value a candidate ciphertext is compared with (P line)
        int ne = 0;
        int idx = 0;
        while (idx < nc) {
            const u32 j = cur[idx].j;
            if (j + 3 > NEED) {                       // swap_remove(idx)
                cur[idx] = cur[nc - 1];
                nc--;
                continue;
            }
            const u32 k0 = MK(j);
            const u32 t0 = sub29(ci, k0);
            if (prev >= 0) {
                const u32 pv = (u32)prev;
#if BACK
                // key runs backward through the text: the used key comes first in pointer order, the colliding draws follow
                const u32 k1 = MK(j + 1);
                const u32 k2 = MK(j + 2);
                if (model == 0) {
                    if (add29(t0, k1) == pv) {
                        ext[ne] = cur[idx];
                        take(ext[ne], t0, j + 2);
                        ne++;
                    }
                    if (add29(t0, k1) == pv && add29(t0, k2) == pv) {
                        ext[ne] = cur[idx];
                        take(ext[ne], t0, j + 3);
                        ne++;
                    }
                } else if (add29(t0, k2) == pv) {
                    ext[ne] = cur[idx];
                    take(ext[ne], t0, j + 3);
                    ne++;
                }
#else
                if (model == 0) {
                    const u32 k1 = MK(j + 1);
                    const u32 t1 = sub29(ci, k1);
                    if (add29(t1, k0) == pv) {
                        ext[ne] = cur[idx];
                        take(ext[ne], t1, j + 2);
                        ne++;
                    }
                    const u32 k2 = MK(j + 2);
                    const u32 t2 = sub29(ci, k2);
                    if (add29(t2, k0) == pv && add29(t2, k1) == pv) {
                        ext[ne] = cur[idx];
                        take(ext[ne], t2, j + 3);
                        ne++;
                    }
                } else {
                    const u32 k2 = MK(j + 2);
                    const u32 t2 = sub29(ci, k2);
                    if (add29(t2, k0) == pv) {
                        ext[ne] = cur[idx];
                        take(ext[ne], t2, j + 3);
                        ne++;
                    }
                }
#endif
            }
#if BACK
            if (model == 1 && prev >= 0 && prev == (int)ci)
                take(cur[idx], sub29(ci, MK(j + 1)), j + 2);          // a kept doublet: the coin first, then the used key
            else
                take(cur[idx], t0, j + 1);
#else
            const u32 nj = (model == 1 && prev == (int)ci) ? j + 2 : j + 1;
            take(cur[idx], t0, nj);
#endif
            idx++;
        }
        for (int e = 0; e < ne; e++) cur[nc + e] = ext[e];   // extend_from_slice
        nc += ne;
        if (nc == 0) {
            *used = i > 2 ? i : 2;
            return 0;
        }
        if (nc > 1) {
            int a = 0;
            while (a < nc) {                                  // merge states with the same key pointer
                int b = a + 1;
                while (b < nc) {
                    if (cur[b].j == cur[a].j) {
                        if (cur[b].s > cur[a].s) cur[a] = cur[b];
                        cur[b] = cur[nc - 1];
                        nc--;
                    } else {
                        b++;
                    }
                }
                a++;
            }
            if (nc > BEAM) {                                  // stable sort by s, descending; keep BEAM
                u8 ord[CAP];
                for (int r = 0; r < nc; r++) ord[r] = (u8)r;
                for (int r = 1; r < nc; r++) {
                    const u8 v = ord[r];
                    const u32 key = cur[v].s;
                    int q = r - 1;
                    while (q >= 0 && cur[ord[q]].s < key) {
                        ord[q + 1] = ord[q];
                        q--;
                    }
                    ord[q + 1] = v;
                }
                for (int r = 0; r < BEAM; r++) ext[r] = cur[ord[r]];
                for (int r = 0; r < BEAM; r++) cur[r] = ext[r];
                nc = BEAM;
            }
        }
        if (i + 1 == abort_at) {
            u32 best = 0;
            for (int r = 0; r < nc; r++) best = cur[r].s > best ? cur[r].s : best;
            if (best < abort_s) {
                *used = abort_at;
                return best;
            }
        }
    }
    u32 best = 0;
    for (int r = 0; r < nc; r++) best = cur[r].s > best ? cur[r].s : best;
    *used = n;
    return best;
}

// ---- fast path ---------------------------------------------------------------------------------------------------
// The same decoder with each state's letter counts kept in shared memory as packed bytes, laid out so that thread L's
// word w of slot q sits at ((q * 8 + w) * SBLK + L): whatever the letter index, the 32 lanes hit 32 different banks,
// where the generic path's per-letter local-memory access costs one cache line per lane. States stay at their vector
// positions (slot = position), so the order-dependent steps of the Rust code (appended extras, swap_remove in the
// merge) are reproduced exactly. It gives up (returns false) and the caller runs beam_decode from scratch when it
// needs more than KSLOT states at once, a count reaches 255, the key runs out (swap_remove in the first loop) or the
// beam would be cut; over 98% of decodes on random keys stay on the fast path.
#ifndef KSLOT
#define KSLOT 14       // measured: 16 slots = 4.1 M decodes/s, 14 = 5.2 M (less shared memory, more resident warps)
#endif
#define SC(q, w) sc[((q) * 8 + (w)) * SBLK]

__device__ __forceinline__ void cpslot(u32 *sc, int dst, int src) {
#pragma unroll
    for (int w = 0; w < 8; w++) SC(dst, w) = SC(src, w);
}

// adds letter t to slot q's counts: returns false if that count was already 255
__device__ __forceinline__ bool bump(u32 *sc, int q, u32 t, u32 &s) {
    const u32 w = SC(q, t >> 2), sh = (t & 3u) * 8u, cv = (w >> sh) & 255u;
    s += 2u * cv;
    SC(q, t >> 2) = w + (1u << sh);
    return cv != 255u;
}

__device__ bool beam_fast(const u8 *__restrict__ c, const signed char *__restrict__ pv, const u8 *__restrict__ kp, u32 m, int model, int n,
                          int abort_at, u32 abort_s, u32 *used, u32 *best_out, u32 *sc) {
    u32 J[KSLOT], S[KSLOT];
    int nc = 1;
    J[0] = 0;
    S[0] = 0;
#pragma unroll
    for (int w = 0; w < 8; w++) SC(0, w) = 0;
    for (int i = 0; i < n; i++) {
        const u32 ci = c[i];
        const int prev = (int)pv[i];                 // the value a candidate ciphertext is compared with (P line)
        const int nc0 = nc;
        int ne = 0;
        bool ok = true;
        for (int idx = 0; idx < nc0; idx++) {
            const u32 j = J[idx];
            if (j + 3 > NEED) return false;
            const u32 k0 = MK(j);
            const u32 t0 = sub29(ci, k0);
            if (prev >= 0) {
                const u32 pv = (u32)prev;
#if BACK
                const u32 k1 = MK(j + 1);
                const u32 k2 = MK(j + 2);
                if (model == 0) {
                    if (add29(t0, k1) == pv) {
                        const int q = nc0 + ne++;
                        if (q >= KSLOT) return false;
                        cpslot(sc, q, idx);
                        S[q] = S[idx];
                        ok &= bump(sc, q, t0, S[q]);
                        J[q] = j + 2;
                    }
                    if (add29(t0, k1) == pv && add29(t0, k2) == pv) {
                        const int q = nc0 + ne++;
                        if (q >= KSLOT) return false;
                        cpslot(sc, q, idx);
                        S[q] = S[idx];
                        ok &= bump(sc, q, t0, S[q]);
                        J[q] = j + 3;
                    }
                } else if (add29(t0, k2) == pv) {
                    const int q = nc0 + ne++;
                    if (q >= KSLOT) return false;
                    cpslot(sc, q, idx);
                    S[q] = S[idx];
                    ok &= bump(sc, q, t0, S[q]);
                    J[q] = j + 3;
                }
#else
                if (model == 0) {
                    const u32 k1 = MK(j + 1);
                    const u32 t1 = sub29(ci, k1);
                    if (add29(t1, k0) == pv) {
                        const int q = nc0 + ne++;
                        if (q >= KSLOT) return false;
                        cpslot(sc, q, idx);
                        S[q] = S[idx];
                        ok &= bump(sc, q, t1, S[q]);
                        J[q] = j + 2;
                    }
                    const u32 k2 = MK(j + 2);
                    const u32 t2 = sub29(ci, k2);
                    if (add29(t2, k0) == pv && add29(t2, k1) == pv) {
                        const int q = nc0 + ne++;
                        if (q >= KSLOT) return false;
                        cpslot(sc, q, idx);
                        S[q] = S[idx];
                        ok &= bump(sc, q, t2, S[q]);
                        J[q] = j + 3;
                    }
                } else {
                    const u32 k2 = MK(j + 2);
                    const u32 t2 = sub29(ci, k2);
                    if (add29(t2, k0) == pv) {
                        const int q = nc0 + ne++;
                        if (q >= KSLOT) return false;
                        cpslot(sc, q, idx);
                        S[q] = S[idx];
                        ok &= bump(sc, q, t2, S[q]);
                        J[q] = j + 3;
                    }
                }
#endif
            }
#if BACK
            if (model == 1 && prev >= 0 && prev == (int)ci) {
                ok &= bump(sc, idx, sub29(ci, MK(j + 1)), S[idx]);
                J[idx] = j + 2;
            } else {
                ok &= bump(sc, idx, t0, S[idx]);
                J[idx] = j + 1;
            }
#else
            ok &= bump(sc, idx, t0, S[idx]);
            J[idx] = (model == 1 && prev == (int)ci) ? j + 2 : j + 1;
#endif
        }
        if (!ok) return false;
        nc = nc0 + ne;
        if (nc > 1) {
            int a = 0;
            while (a < nc) {
                int b = a + 1;
                while (b < nc) {
                    if (J[b] == J[a]) {
                        if (S[b] > S[a]) {
                            J[a] = J[b];
                            S[a] = S[b];
                            cpslot(sc, a, b);
                        }
                        if (b != nc - 1) {
                            J[b] = J[nc - 1];
                            S[b] = S[nc - 1];
                            cpslot(sc, b, nc - 1);
                        }
                        nc--;
                    } else {
                        b++;
                    }
                }
                a++;
            }
            if (nc > BEAM) return false;
        }
        if (i + 1 == abort_at) {
            u32 best = 0;
            for (int r = 0; r < nc; r++) best = S[r] > best ? S[r] : best;
            if (best < abort_s) {
                *used = abort_at;
                *best_out = best;
                return true;
            }
        }
    }
    u32 best = 0;
    for (int r = 0; r < nc; r++) best = S[r] > best ? S[r] : best;
    *used = n;
    *best_out = best;
    return true;
}

// ---- kernels -----------------------------------------------------------------------------------------------------
// screen_kernel runs the fast path for every decode of its task and queues the few decodes that need the generic path
// (fb list); fallback_kernel then runs those with every lane busy. A decode's result does not depend on which path
// computed it.

struct Loc {
    int lo;
    u32 off, mi;
};

__device__ __forceinline__ Loc locate(const u64 task, const u64 *__restrict__ pre, const u32 *__restrict__ ioff0,
                                      const int n_items) {
    Loc L;
    L.mi = (u32)(task % NMULT);
    const u64 io = task / NMULT;
    int lo = 0, hi = n_items - 1;                             // largest item whose first task is <= io
    while (lo < hi) {
        const int mid = (lo + hi + 1) >> 1;
        if (pre[mid] <= io) lo = mid; else hi = mid - 1;
    }
    L.lo = lo;
    L.off = ioff0[lo] + (u32)(io - pre[lo]);
    return L;
}

#if MODE != 0
__device__ void make_key(u8 *key, const u8 *co, const u32 off) {
#if MODE == 1
    u32 x = off + 1;
    for (int e = 0; e < ORD; e++) { key[e] = (u8)(x % Q); x /= Q; }
    for (int t = ORD; t < NEED; t++) {
        u32 acc = 0;
        for (int e = 1; e <= ORD; e++) acc += (u32)co[e - 1] * key[t - e];
        key[t] = (u8)(acc % Q);
    }
#else
    u8 ptab[Q];
    for (int nn = 0; nn < Q; nn++) {
        u32 acc = 0, pw = 1;
        for (int e = 0; e < ORD; e++) { pw = pw * nn % Q; acc += (u32)co[e] * pw; }
        ptab[nn] = (u8)(acc % Q);
    }
    for (int t = 0; t < NEED; t++) key[t] = ptab[(off + t) % Q];
#endif
}
#endif

// histogram, window best and hit list for one finished decode (shist: block-shared histogram, else global ghist)
__device__ __forceinline__ void finish(const u32 s, const u32 used, const int n, const int wi, const int model,
                                       const u64 task, const float thr, u32 *shist, u64 *ghist, u64 *wbest,
                                       u32 *hcount, u32 *hits, const u32 hcap, u32 &nab) {
    const double ioc = used < 2 ? 0.0 : 29.0 * (double)s / ((double)used * ((double)used - 1.0));
    const float f = (float)ioc;
    int bin = (int)(f * 100.0f);
    if (bin > HBINS - 1) bin = HBINS - 1;
    if (shist) atomicAdd(&shist[bin], 1u); else atomicAdd(&ghist[bin], 1ull);
    if (used < (u32)n) {
        nab++;
        return;
    }
    const u64 key64 = ((u64)__float_as_uint(f) << 32) | (u64)(u32)(task * 2 + (u64)model);
    if (key64 > wbest[wi]) atomicMax(&wbest[wi], key64);
    if (f >= thr) {
        const u32 h = atomicAdd(hcount, 1u);
        if (h < hcap) {
            hits[3 * h] = __float_as_uint(f);
            hits[3 * h + 1] = (u32)task;
            hits[3 * h + 2] = ((u32)wi << 8) | (u32)model;
        }
    }
}

extern "C" __global__ void __launch_bounds__(SBLK)
screen_kernel(const u8 *__restrict__ lib, const u64 *__restrict__ ibase, const u64 *__restrict__ pre,
              const u32 *__restrict__ ioff0, const u8 *__restrict__ icoef, const int n_items, const u64 t0,
              const u64 n_tasks, const u8 *__restrict__ runes, const u32 *__restrict__ wstart,
              const u32 *__restrict__ wn, const signed char *__restrict__ wpv, const u32 *__restrict__ wab,
              const u8 *__restrict__ mults, const u8 *__restrict__ models, const u32 abort_s, const float thr,
              u64 *ghist, u64 *wbest, u32 *hcount, u32 *hits, const u32 hcap, u64 *gaborted, u32 *dump, u32 *fb,
              u32 *fbcount, const u32 fbcap) {
    __shared__ u32 sh[HBINS];
    __shared__ u32 scnt[KSLOT * 8 * SBLK];
    for (int b = threadIdx.x; b < HBINS; b += blockDim.x) sh[b] = 0;
    __syncthreads();
    const u64 g = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    u32 nab = 0;
    if (g < n_tasks) {
        const u64 task = t0 + g;
        const Loc L = locate(task, pre, ioff0, n_items);
        const u32 m = mults[L.mi];
#if MODE == 0
        const u8 *kp = lib + ibase[L.lo] + L.off;
#else
        u8 key[NEED];
        make_key(key, icoef + 4 * L.lo, L.off);
        const u8 *kp = key;
#endif
        for (int mdl = 0; mdl < NMODEL; mdl++) {
            const int model = models[mdl];
            for (int wi = 0; wi < NW; wi++) {
                const int n = (int)wn[wi];
                u32 used, s;
                if (!beam_fast(runes + wstart[wi], wpv + wstart[wi], kp, m, model, n, (int)wab[wi], abort_s, &used, &s,
                               scnt + threadIdx.x)) {
                    const u32 q = atomicAdd(fbcount, 1u);
                    if (q < fbcap) {
                        fb[2 * q] = (u32)task;
                        fb[2 * q + 1] = ((u32)mdl << 8) | (u32)wi;
                    }
                    continue;
                }
#if DUMP
                const u64 di = ((g * NMODEL + mdl) * NW + wi) * 2;
                dump[di] = s;
                dump[di + 1] = used;
#endif
                finish(s, used, n, wi, model, task, thr, sh, ghist, wbest, hcount, hits, hcap, nab);
            }
        }
        if (nab) atomicAdd(gaborted, (u64)nab);
    }
    __syncthreads();
    for (int b = threadIdx.x; b < HBINS; b += blockDim.x)
        if (sh[b]) atomicAdd(&ghist[b], (u64)sh[b]);
}

extern "C" __global__ void __launch_bounds__(128)
fallback_kernel(const u8 *__restrict__ lib, const u64 *__restrict__ ibase, const u64 *__restrict__ pre,
                const u32 *__restrict__ ioff0, const u8 *__restrict__ icoef, const int n_items, const u64 t0,
                const u8 *__restrict__ runes, const u32 *__restrict__ wstart, const u32 *__restrict__ wn,
                const signed char *__restrict__ wpv, const u32 *__restrict__ wab, const u8 *__restrict__ mults,
                const u8 *__restrict__ models, const u32 abort_s, const float thr, u64 *ghist, u64 *wbest,
                u32 *hcount, u32 *hits, const u32 hcap, u64 *gaborted, u32 *dump, const u32 *__restrict__ fb,
                const u32 n_fb) {
    const u32 q = blockIdx.x * blockDim.x + threadIdx.x;
    if (q >= n_fb) return;
    const u64 task = fb[2 * q];
    const int mdl = (int)(fb[2 * q + 1] >> 8), wi = (int)(fb[2 * q + 1] & 255u);
    const Loc L = locate(task, pre, ioff0, n_items);
    const u32 m = mults[L.mi];
#if MODE == 0
    const u8 *kp = lib + ibase[L.lo] + L.off;
#else
    u8 key[NEED];
    make_key(key, icoef + 4 * L.lo, L.off);
    const u8 *kp = key;
#endif
    const int model = models[mdl], n = (int)wn[wi];
    u32 used;
    const u32 s = beam_decode(runes + wstart[wi], wpv + wstart[wi], kp, m, model, n, (int)wab[wi], abort_s, &used);
#if DUMP
    const u64 di = (((task - t0) * NMODEL + mdl) * NW + wi) * 2;
    dump[di] = s;
    dump[di + 1] = used;
#endif
    u32 nab = 0;
    finish(s, used, n, wi, model, task, thr, nullptr, ghist, wbest, hcount, hits, hcap, nab);
    if (nab) atomicAdd(gaborted, (u64)nab);
}

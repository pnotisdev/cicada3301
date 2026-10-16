// CUDA port of the phpmt seed sweep (work/phpmt/src/main.rs): one thread = one seed. It generates the first K = 160
// outputs of the chosen generator, derives both key maps, and runs `decode_fast` for every (window, variant), keeping
// the Rust code's state-vector rules statement by statement so that the scores are identical (tests/test_phpmt_gpu.py).
// gpu.py prepends the #defines:  GEN (0 php mt_rand<7.1, 1 glibc random(), 2 .NET Random)   NW (windows)
//                                DUMP (0 none, 1 every score, 2 raw generator outputs)
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;

#define K 160
#define MOD 29
#define WMAX 64
#define HB 64

// ------------------------------------------------------------------ generators (first K raw outputs, 31 bits)

#if GEN == 0
#define MT_M 397
__device__ __forceinline__ u32 temper(u32 y) {
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c5680u;
    y ^= (y << 15) & 0xefc60000u;
    return y ^ (y >> 18);
}
__device__ void gen_raw(const u32 seed, u32 *raw) {
    u32 head[K + 1];
    u32 x = seed;
    head[0] = x;
    for (int i = 1; i <= MT_M + K - 1; i++) {               // s[i] = 1812433253 (s[i-1] ^ s[i-1] >> 30) + i
        x = 1812433253u * (x ^ (x >> 30)) + (u32)i;
        if (i <= K) head[i] = x;
        if (i >= MT_M) {                                    // x = s[o + M]: output o = temper(twist) >> 1
            const int o = i - MT_M;
            const u32 u = head[o], v = head[o + 1];
            const u32 t = x ^ (((u & 0x80000000u) | (v & 0x7fffffffu)) >> 1) ^ ((0u - (u & 1u)) & 0x9908b0dfu);
            raw[o] = temper(t) >> 1;
        }
    }
}
#elif GEN == 1
__device__ void gen_raw(const u32 seed, u32 *raw) {
    u32 ring[32];                                           // r[i] lives in ring[i & 31]
    int word = seed == 0 ? 1 : (int)seed;
    ring[0] = (u32)word;
    for (int i = 1; i < 31; i++) {
        const int hi = word / 127773, lo = word % 127773;
        word = (int)(16807u * (u32)lo - 2836u * (u32)hi);
        if (word < 0) word = (int)((u32)word + 2147483647u);
        ring[i] = (u32)word;
    }
    for (int i = 31; i < 34; i++) ring[i & 31] = ring[(i - 31) & 31];
    for (int i = 34; i < 344 + K; i++) {
        const u32 v = ring[(i - 31) & 31] + ring[(i - 3) & 31];
        ring[i & 31] = v;
        if (i >= 344) raw[i - 344] = v >> 1;
    }
}
#else
__device__ void gen_raw(const u32 seed, u32 *raw) {
    const int MBIG = 2147483647, MSEED = 161803398;
    const int s = (int)seed;
    const int sub = s == (int)0x80000000 ? MBIG : (s < 0 ? -s : s);
    int a[56];
    int mj = MSEED - sub;
    a[55] = mj;
    int mk = 1;
    for (int i = 1; i < 55; i++) {
        const int ii = (21 * i) % 55;
        a[ii] = mk;
        mk = mj - mk;
        if (mk < 0) mk += MBIG;
        mj = a[ii];
    }
    for (int p = 1; p < 5; p++)
        for (int i = 1; i < 56; i++) {
            a[i] = (int)((u32)a[i] - (u32)a[1 + (i + 30) % 55]);
            if (a[i] < 0) a[i] += MBIG;
        }
    int inext = 0, inextp = 21;
    for (int o = 0; o < K; o++) {
        if (++inext >= 56) inext = 1;
        if (++inextp >= 56) inextp = 1;
        int v = (int)((u32)a[inext] - (u32)a[inextp]);
        if (v == MBIG) v -= 1;
        if (v < 0) v += MBIG;
        a[inext] = v;
        raw[o] = (u32)v;
    }
}
#endif

// map 0 = the language's own range call, map 1 = raw % 29
__device__ __forceinline__ u8 key0(const u32 n) {
#if GEN == 2
    return (u8)(((double)n * (1.0 / 2147483647.0)) * 29.0);                  // (int)(Sample() * 29)
#else
    return (u8)((29ull * n) >> 31);                                           // 29 * (n / 2^31), exact for 31-bit n
#endif
}

// ------------------------------------------------------------------ decoder

struct PS {
    u64 code;
    u16 j;
    u16 score;
    u8 len;
};

__device__ __forceinline__ bool in_dict(const u64 *__restrict__ dcodes, const u32 *__restrict__ dstart, u32 len, u64 code) {
    if (len >= 13) return false;
    int lo = (int)dstart[len], hi = (int)dstart[len + 1] - 1;
    while (lo <= hi) {
        const int mid = (lo + hi) >> 1;
        const u64 v = dcodes[mid];
        if (v == code) return true;
        if (v < code) lo = mid + 1; else hi = mid - 1;
    }
    return false;
}

__device__ __forceinline__ int subk(int c, int k, int sign) {
    int v = sign > 0 ? c - k : c + k;
    return v < 0 ? v + MOD : (v >= MOD ? v - MOD : v);
}
__device__ __forceinline__ int addk(int t, int k, int sign) {
    int v = sign > 0 ? t + k : t - k;
    return v < 0 ? v + MOD : (v >= MOD ? v - MOD : v);
}

// decode_fast of the Rust engine
__device__ u32 decode_fast(const u8 *__restrict__ runes, const u8 *__restrict__ wend, const int *__restrict__ meta,
                           const u8 *key, const int sign, const bool atb, const int model, const u64 *__restrict__ dcodes,
                           const u32 *__restrict__ dstart) {
    const int wprev = meta[0], wn = meta[1], abort1 = meta[2], abort2 = meta[3];
    PS states[16];
    PS next[48];
    int ns = 1;
    states[0].code = 0;
    states[0].j = 0;
    states[0].score = 0;
    states[0].len = 0;
    for (int i = 0; i < wn; i++) {
        const int c = runes[i];
        const int prev = i == 0 ? wprev : (int)runes[i - 1];
        int nn = 0;
        for (int si = 0; si < ns; si++) {
            const PS s = states[si];
            const int j = s.j;
            if (j + 3 >= K) continue;
#define PUSH(TT, NJ)                                                                                         \
    {                                                                                                        \
        if (nn < 48) {                                                                                       \
            const int t_ = (TT);                                                                             \
            next[nn].j = (u16)(NJ);                                                                          \
            next[nn].code = s.code * 29ull + (u64)(atb ? 28 - t_ : t_);                                     \
            next[nn].len = (u8)(s.len + 1);                                                                  \
            next[nn].score = s.score;                                                                        \
            nn++;                                                                                            \
        }                                                                                                    \
    }
            const int k0 = key[j];
            if (model == 0) {
                PUSH(subk(c, k0, sign), j + 1);
                if (prev >= 0) {
                    const int t1 = subk(c, key[j + 1], sign);
                    if (addk(t1, k0, sign) == prev) PUSH(t1, j + 2);
                    const int t2 = subk(c, key[j + 2], sign);
                    if (addk(t2, k0, sign) == prev && addk(t2, key[j + 1], sign) == prev) PUSH(t2, j + 3);
                }
            } else {
                if (prev >= 0 && c == prev) PUSH(subk(c, k0, sign), j + 2)
                else PUSH(subk(c, k0, sign), j + 1);
                if (prev >= 0) {
                    const int t = subk(c, key[j + 2], sign);
                    if (addk(t, k0, sign) == prev) PUSH(t, j + 3);
                }
            }
        }
        if (nn == 0) return 0;
        if (wend[i]) {
            ns = 0;
            for (int q = 0; q < nn; q++) {
                PS s = next[q];
                if (s.len >= 3 && in_dict(dcodes, dstart, s.len, s.code)) s.score += s.len;
                s.code = 0;
                s.len = 0;
                bool found = false;                         // merge equal key pointers (the future depends only on j)
                for (int r = 0; r < ns; r++) {
                    if (states[r].j == s.j) {
                        if (s.score > states[r].score) states[r] = s;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    if (ns < 16) {
                        states[ns++] = s;
                    } else {                                // replace the first worst state if this one is better
                        int wi = 0;
                        u32 ws = states[0].score;
                        for (int r = 1; r < 16; r++)
                            if (states[r].score < ws) { ws = states[r].score; wi = r; }
                        if (s.score > ws) states[wi] = s;
                    }
                }
            }
            if (i + 1 == abort1 || i + 1 == abort2) {
                u32 best = 0;
                for (int r = 0; r < ns; r++) best = states[r].score > best ? states[r].score : best;
                if ((i + 1 == abort1 && best == 0) || (i + 1 == abort2 && best < 6)) return best;
            }
        } else {
            ns = nn < 16 ? nn : 16;
            for (int r = 0; r < ns; r++) states[r] = next[r];
        }
    }
    u32 best = 0;
    for (int r = 0; r < ns; r++) best = states[r].score > best ? states[r].score : best;
    return best;
}

extern "C" __global__ void __launch_bounds__(128)
sweep_kernel(const u8 *__restrict__ wrunes, const u8 *__restrict__ wend, const int *__restrict__ wmeta,
             const u64 *__restrict__ dcodes, const u32 *__restrict__ dstart, const u64 seed0, const u64 nseeds,
             const u32 thr, u64 *ghist, u32 *cand, u32 *ccount, const u32 ccap, u32 *dump) {
    __shared__ u32 sh[HB];
    for (int b = threadIdx.x; b < HB; b += blockDim.x) sh[b] = 0;
    __syncthreads();
    const u64 g = (u64)blockIdx.x * blockDim.x + threadIdx.x;
    if (g < nseeds) {
        const u32 seed = (u32)(seed0 + g);
        u32 raw[K];
        gen_raw(seed, raw);
#if DUMP == 2
        for (int i = 0; i < K; i++) dump[g * K + i] = raw[i];
#else
        u8 keys[2][K];
        for (int i = 0; i < K; i++) {
            keys[0][i] = key0(raw[i]);
            keys[1][i] = (u8)(raw[i] % 29u);
        }
        for (int wi = 0; wi < NW; wi++) {
            for (int v = 0; v < 16; v++) {
                const bool atb = v & 1;
                const int sign = ((v >> 1) & 1) == 0 ? 1 : -1;
                const int map = (v >> 2) & 1;
                const int model = (v >> 3) & 1;
                const u32 s = decode_fast(wrunes + wi * WMAX, wend + wi * WMAX, wmeta + 4 * wi, keys[map], sign, atb, model,
                                          dcodes, dstart);
                atomicAdd(&sh[s < HB - 1 ? s : HB - 1], 1u);
#if DUMP == 1
                dump[(g * NW + wi) * 16 + v] = s;
#endif
                if (s > 0 && s >= thr) {
                    const u32 q = atomicAdd(ccount, 1u);
                    if (q < ccap) {
                        cand[2 * q] = seed;
                        cand[2 * q + 1] = (s << 16) | ((u32)wi << 8) | (u32)v;
                    }
                }
            }
        }
#endif
    }
    __syncthreads();
    for (int b = threadIdx.x; b < HB; b += blockDim.x)
        if (sh[b]) atomicAdd(&ghist[b], (u64)sh[b]);
}

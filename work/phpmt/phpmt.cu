// CUDA port of the phpmt seed sweep (work/phpmt/src/main.rs): one thread = one seed. It generates the first K = 160
// outputs of the chosen generator, derives both key maps, and runs `decode_fast` for every (window, variant), keeping
// the Rust code's state-vector rules statement by statement so that the scores are identical (tests/test_phpmt_gpu.py).
// gpu.py prepends the #defines:  GEN (0 php mt_rand<7.1, 1 glibc random(), 2 .NET Random, 3 py3, 4 mt32, 5 mt31, 6 java,
//                                     7 msvc, 8 drand48, 9 ruby: see work/phpmt/src/gens.rs)   NW (windows)
//                                DUMP (0 none, 1 every score, 2 raw generator outputs (GEN 0-2), 3 both key maps)
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

// ---- generators that give key values directly (rejection, two outputs per key, ...): gens.rs ------------------------
#if GEN >= 3
#define MASK48 ((1ull << 48) - 1)
#define JMUL 0x5DEECE66Dull
#define GEN_MT (GEN == 3 || GEN == 4 || GEN == 5 || GEN == 9)

#if GEN_MT
#define MT_N 624
#define MT_MM 397
__device__ __forceinline__ u32 mt_temper(u32 y) {
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c5680u;
    y ^= (y << 15) & 0xefc60000u;
    return y ^ (y >> 18);
}

// the 624 state words after seeding and one full twist; output i is mt_temper(s[i]) (at most 2K + slack < 624 are needed)
__device__ void mt_state(u32 *s, const u32 seed) {
#if GEN == 3 || GEN == 9
    s[0] = 19650218u;                                                // init_genrand(19650218), then init_by_array([seed])
    for (int i = 1; i < MT_N; i++) s[i] = 1812433253u * (s[i - 1] ^ (s[i - 1] >> 30)) + (u32)i;
    int i = 1;
    for (int k = MT_N; k > 0; k--) {
        s[i] = (s[i] ^ ((s[i - 1] ^ (s[i - 1] >> 30)) * 1664525u)) + seed;
        i++;
        if (i >= MT_N) { s[0] = s[MT_N - 1]; i = 1; }
    }
    for (int k = MT_N - 1; k > 0; k--) {
        s[i] = (s[i] ^ ((s[i - 1] ^ (s[i - 1] >> 30)) * 1566083941u)) - (u32)i;
        i++;
        if (i >= MT_N) { s[0] = s[MT_N - 1]; i = 1; }
    }
    s[0] = 0x80000000u;
#else
    s[0] = seed;                                                     // init_genrand(seed)
    for (int i = 1; i < MT_N; i++) s[i] = 1812433253u * (s[i - 1] ^ (s[i - 1] >> 30)) + (u32)i;
#endif
    for (int i = 0; i < MT_N - MT_MM; i++) {
        const u32 u = s[i], v = s[i + 1];
        s[i] = s[i + MT_MM] ^ (((u & 0x80000000u) | (v & 0x7fffffffu)) >> 1) ^ ((0u - (v & 1u)) & 0x9908b0dfu);
    }
    for (int i = MT_N - MT_MM; i < MT_N - 1; i++) {
        const u32 u = s[i], v = s[i + 1];
        s[i] = s[i + MT_MM - MT_N] ^ (((u & 0x80000000u) | (v & 0x7fffffffu)) >> 1) ^ ((0u - (v & 1u)) & 0x9908b0dfu);
    }
    {
        const u32 u = s[MT_N - 1], v = s[0];
        s[MT_N - 1] = s[MT_MM - 1] ^ (((u & 0x80000000u) | (v & 0x7fffffffu)) >> 1) ^ ((0u - (v & 1u)) & 0x9908b0dfu);
    }
}
__device__ __forceinline__ u32 mt_at(const u32 *s, int p) { return mt_temper(s[p < MT_N ? p : MT_N - 1]); }
__device__ __forceinline__ u8 res53_key(const u32 *s, int p) {
    const double a = (double)(mt_at(s, p) >> 5), b = (double)(mt_at(s, p + 1) >> 6);
    return (u8)(((a * 67108864.0 + b) * (1.0 / 9007199254740992.0)) * 29.0);          // int(random() * 29)
}
#endif

#if GEN == 6
__device__ __forceinline__ u32 jnext(u64 &st, const int bits) {
    st = (st * JMUL + 0xBull) & MASK48;
    return (u32)(st >> (48 - bits));
}
#endif

__device__ void gen_keys(const u32 seed, u8 keys[2][K]) {
#if GEN_MT
    u32 s[MT_N];
    mt_state(s, seed);
    int p = 0;
#if GEN == 3                                                          // py3: randrange(29) | int(random() * 29)
    for (int i = 0; i < K; i++) {
        u32 r;
        do { r = mt_at(s, p++) >> 27; } while (r >= 29u);
        keys[0][i] = (u8)r;
    }
    for (int i = 0; i < K; i++) keys[1][i] = res53_key(s, 2 * i);
#elif GEN == 9                                                        // ruby: rand(29) (y & 31, retry > 28) | rand float
    for (int i = 0; i < K; i++) {
        u32 r;
        do { r = mt_at(s, p++) & 31u; } while (r > 28u);
        keys[0][i] = (u8)r;
    }
    for (int i = 0; i < K; i++) keys[1][i] = res53_key(s, 2 * i);
#elif GEN == 4                                                        // mt32: Lemire uniform_int_distribution | y % 29
    for (int i = 0; i < K; i++) {
        u64 prod = (u64)mt_at(s, p++) * 29ull;
        if ((u32)prod < 29u) {
            const u32 thr = (0u - 29u) % 29u;
            while ((u32)prod < thr) prod = (u64)mt_at(s, p++) * 29ull;
        }
        keys[0][i] = (u8)(prod >> 32);
        keys[1][i] = (u8)(mt_at(s, i) % 29u);
    }
#else                                                                 // mt31: (y >> 1) % 29 | floor(29 * (y >> 1) / 2^31)
    for (int i = 0; i < K; i++) {
        const u32 n = mt_at(s, i) >> 1;
        keys[0][i] = (u8)(n % 29u);
        keys[1][i] = (u8)(29.0 * ((double)n / 2147483648.0));
    }
#endif
#elif GEN == 6                                                        // java.util.Random(int seed): nextInt(29) | (int)(nextDouble() * 29)
    u64 st = ((u64)(long long)(int)seed ^ JMUL) & MASK48;
    for (int i = 0; i < K; i++) {
        int bits, val;
        do {
            bits = (int)jnext(st, 31);
            val = bits % 29;
        } while ((int)((u32)bits - (u32)val + 28u) < 0);
        keys[0][i] = (u8)val;
    }
    st = ((u64)(long long)(int)seed ^ JMUL) & MASK48;
    for (int i = 0; i < K; i++) {
        const u64 hi = jnext(st, 26);
        const u64 lo = jnext(st, 27);
        keys[1][i] = (u8)(((double)((hi << 27) + lo) * (1.0 / 9007199254740992.0)) * 29.0);
    }
#elif GEN == 7                                                        // MSVC rand() after srand(seed): r % 29 | r * 29 / 32768
    u32 x = seed;
    for (int i = 0; i < K; i++) {
        x = x * 214013u + 2531011u;
        const u32 r = (x >> 16) & 0x7fffu;
        keys[0][i] = (u8)(r % 29u);
        keys[1][i] = (u8)((r * 29u) >> 15);
    }
#else                                                                 // drand48 / Perl srand(seed): int(drand48() * 29) | lrand48() % 29
    u64 x = ((u64)seed << 16) | 0x330Eull;
    for (int i = 0; i < K; i++) {
        x = (x * JMUL + 0xBull) & MASK48;
        keys[0][i] = (u8)((x * 29ull) >> 48);
        keys[1][i] = (u8)((x >> 17) % 29ull);
    }
#endif
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
#if GEN <= 2
        u32 raw[K];
        gen_raw(seed, raw);
#endif
#if DUMP == 2
        for (int i = 0; i < K; i++) dump[g * K + i] = raw[i];
#else
        u8 keys[2][K];
#if GEN <= 2
        for (int i = 0; i < K; i++) {
            keys[0][i] = key0(raw[i]);
            keys[1][i] = (u8)(raw[i] % 29u);
        }
#else
        gen_keys(seed, keys);
#endif
#if DUMP == 3
        for (int m = 0; m < 2; m++)
            for (int i = 0; i < K; i++) dump[(g * 2 + m) * K + i] = keys[m][i];
#else
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
#endif
    }
    __syncthreads();
    for (int b = threadIdx.x; b < HB; b += blockDim.x)
        if (sh[b]) atomicAdd(&ghist[b], (u64)sh[b]);
}

// CUDA seed sweep for the STEP-DOMAIN cipher (work/kscreen/step28.py, research note C2): one thread = one seed. It generates
// the first K = 256 outputs of the chosen generator, derives the key maps for 28 classes (variant A: K mod 28 natively) and
// for 29 values (variant B: log2 of the non-zero values), and for each window, variant, map, mode and unit multiplier
// m of Z28 counts the class histogram of (J_t - m*key) mod 28 over NS steps. Score = index of coincidence (random 1.0,
// English 1.8). The generators are the ones of phpmt.cu (validated against the Rust engine and CPython/NumPy), with the
// key alphabet size KM as a template parameter; tests/test_stepmt.py checks both instantiations against the Rust `keys` mode.
// gpu step.py prepends the #defines:  GEN (0 php, 1 glibc, 2 .NET, 3 py3, 4 mt32, 5 mt31, 6 java, 7 msvc, 8 drand48, 9 ruby)
//                                      NW (windows)  NS (steps per window, <= 255)  DUMP (0 none, 1 every score, 2 both key sets)
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;

#define K 256
#define HB 64
#define NC 28
#define NM 12

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
    // first reload of the legacy state: output o uses the OLD s[o], s[o+1] and, for o < N-M = 227, the old s[o+M] (= x here);
    // from o = 227 on it uses the already twisted s[o+M-N] = tw[o-227] (K > 227 is what the step sweep needs)
    u32 head[K + 1], tw[29];
    u32 x = seed;
    head[0] = x;
    for (int i = 1; i <= MT_M + K - 1; i++) {
        x = 1812433253u * (x ^ (x >> 30)) + (u32)i;
        if (i <= K) head[i] = x;
        if (i >= MT_M) {
            const int o = i - MT_M;
            const u32 u = head[o], v = head[o + 1];
            const u32 m = o < 227 ? x : tw[o - 227];
            const u32 t = m ^ (((u & 0x80000000u) | (v & 0x7fffffffu)) >> 1) ^ ((0u - (u & 1u)) & 0x9908b0dfu);
            if (o < 29) tw[o] = t;
            raw[o] = temper(t) >> 1;
        }
    }
}
#elif GEN == 1
__device__ void gen_raw(const u32 seed, u32 *raw) {
    u32 ring[32];
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
#elif GEN == 2
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
__device__ void mt_state(u32 *s, const u32 seed) {
#if GEN == 3 || GEN == 9
    s[0] = 19650218u;
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
    s[0] = seed;
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
template <int KM>
__device__ __forceinline__ u8 res53_key(const u32 *s, int p) {
    const double a = (double)(mt_at(s, p) >> 5), b = (double)(mt_at(s, p + 1) >> 6);
    return (u8)(((a * 67108864.0 + b) * (1.0 / 9007199254740992.0)) * (double)KM);
}
#endif

#if GEN == 6
__device__ __forceinline__ u32 jnext(u64 &st, const int bits) {
    st = (st * JMUL + 0xBull) & MASK48;
    return (u32)(st >> (48 - bits));
}
#endif
#endif

// the key values of one seed for an alphabet of KM symbols: keys[0] = the language's own range call, keys[1] = the second map
template <int KM>
__device__ void gen_keys(const u32 seed, u8 keys[2][K]) {
#if GEN <= 2
    u32 raw[K];
    gen_raw(seed, raw);
    for (int i = 0; i < K; i++) {
#if GEN == 2
        keys[0][i] = (u8)(((double)raw[i] * (1.0 / 2147483647.0)) * (double)KM);          // (int)(Sample() * KM)
#else
        keys[0][i] = (u8)(((u64)KM * raw[i]) >> 31);                                       // KM * (n / 2^31), exact for 31-bit n
#endif
        keys[1][i] = (u8)(raw[i] % (u32)KM);
    }
#elif GEN_MT
    u32 s[MT_N];
    mt_state(s, seed);
    int p = 0;
#if GEN == 3                                                          // py3: randrange(KM) | int(random() * KM)
    for (int i = 0; i < K; i++) {
        u32 r;
        do { r = mt_at(s, p++) >> 27; } while (r >= (u32)KM);
        keys[0][i] = (u8)r;
    }
    for (int i = 0; i < K; i++) keys[1][i] = res53_key<KM>(s, 2 * i);
#elif GEN == 9                                                        // ruby: rand(KM) (y & 31, retry >= KM) | rand float
    for (int i = 0; i < K; i++) {
        u32 r;
        do { r = mt_at(s, p++) & 31u; } while (r >= (u32)KM);
        keys[0][i] = (u8)r;
    }
    for (int i = 0; i < K; i++) keys[1][i] = res53_key<KM>(s, 2 * i);
#elif GEN == 4                                                        // mt32: Lemire uniform_int_distribution | y % KM
    for (int i = 0; i < K; i++) {
        u64 prod = (u64)mt_at(s, p++) * (u64)KM;
        if ((u32)prod < (u32)KM) {
            const u32 thr = (0u - (u32)KM) % (u32)KM;
            while ((u32)prod < thr) prod = (u64)mt_at(s, p++) * (u64)KM;
        }
        keys[0][i] = (u8)(prod >> 32);
        keys[1][i] = (u8)(mt_at(s, i) % (u32)KM);
    }
#else                                                                 // mt31: (y >> 1) % KM | floor(KM * (y >> 1) / 2^31)
    for (int i = 0; i < K; i++) {
        const u32 n = mt_at(s, i) >> 1;
        keys[0][i] = (u8)(n % (u32)KM);
        keys[1][i] = (u8)((double)KM * ((double)n / 2147483648.0));
    }
#endif
#elif GEN == 6                                                        // java.util.Random(int seed): nextInt(KM) | (int)(nextDouble() * KM)
    u64 st = ((u64)(long long)(int)seed ^ JMUL) & MASK48;
    for (int i = 0; i < K; i++) {
        int bits, val;
        do {
            bits = (int)jnext(st, 31);
            val = bits % KM;
        } while ((int)((u32)bits - (u32)val + (u32)(KM - 1)) < 0);
        keys[0][i] = (u8)val;
    }
    st = ((u64)(long long)(int)seed ^ JMUL) & MASK48;
    for (int i = 0; i < K; i++) {
        const u64 hi = jnext(st, 26);
        const u64 lo = jnext(st, 27);
        keys[1][i] = (u8)(((double)((hi << 27) + lo) * (1.0 / 9007199254740992.0)) * (double)KM);
    }
#elif GEN == 7                                                        // MSVC rand() after srand(seed): r % KM | r * KM / 32768
    u32 x = seed;
    for (int i = 0; i < K; i++) {
        x = x * 214013u + 2531011u;
        const u32 r = (x >> 16) & 0x7fffu;
        keys[0][i] = (u8)(r % (u32)KM);
        keys[1][i] = (u8)((r * (u32)KM) >> 15);
    }
#else                                                                 // drand48 / Perl srand(seed): int(drand48() * KM) | lrand48() % KM
    u64 x = ((u64)seed << 16) | 0x330Eull;
    for (int i = 0; i < K; i++) {
        x = (x * JMUL + 0xBull) & MASK48;
        keys[0][i] = (u8)((x * (u64)KM) >> 48);
        keys[1][i] = (u8)((x >> 17) % (u64)KM);
    }
#endif
}

// ------------------------------------------------------------------ step-domain scoring

__constant__ u8 LOG2[29] = {0, 0, 1, 5, 2, 22, 6, 12, 3, 10, 23, 25, 7, 18, 13, 27, 4, 21, 11, 9, 24, 17, 26, 20, 8, 16, 19, 15, 14};
__constant__ u8 UNIT[NM] = {1, 3, 5, 9, 11, 13, 15, 17, 19, 23, 25, 27};

extern "C" __global__ void __launch_bounds__(128)
step_kernel(const u8 *__restrict__ wJ, const u8 *__restrict__ widx, const u64 seed0, const u64 nseeds, const float thr,
            u64 *ghist, u32 *cand, u32 *ccount, const u32 ccap, u32 *dump) {
    __shared__ u32 sh[HB];
    __shared__ u8 mk[NM][32];
    __shared__ u8 h[NC][128];
    for (int b = threadIdx.x; b < HB; b += blockDim.x) sh[b] = 0;
    for (int b = threadIdx.x; b < NM * 32; b += blockDim.x) mk[b / 32][b % 32] = (u8)((UNIT[b / 32] * (b % 32)) % NC);
    __syncthreads();
    const int tid = threadIdx.x;
    const u64 g = (u64)blockIdx.x * blockDim.x + tid;
    if (g < nseeds) {
        const u32 seed = (u32)(seed0 + g);
        u8 k28[2][K], k29[2][K], lg[2][K];
        gen_keys<28>(seed, k28);
        gen_keys<29>(seed, k29);
#if DUMP == 2
        for (int m = 0; m < 2; m++)
            for (int i = 0; i < K; i++) {
                dump[(g * 4 + m) * K + i] = k28[m][i];
                dump[(g * 4 + 2 + m) * K + i] = k29[m][i];
            }
#else
        int nl[2];
        for (int m = 0; m < 2; m++) {                                  // variant B reads log2 of the non-zero values, zeros dropped
            int c = 0;
            for (int i = 0; i < K; i++)
                if (k29[m][i]) lg[m][c++] = LOG2[k29[m][i]];
            nl[m] = c;
        }
        for (int wi = 0; wi < NW; wi++)
            for (int var = 0; var < 2; var++)
                for (int map = 0; map < 2; map++) {
                    const u8 *key = var == 0 ? k28[map] : lg[map];
                    const int nk = var == 0 ? K : nl[map];
                    const u8 *J = wJ + (wi * 2 + var) * NS;
                    for (int mode = 0; mode < 2; mode++) {
                        const u8 *ix = widx + (wi * 2 + mode) * NS;
                        for (int mi = 0; mi < NM; mi++) {
                            for (int d = 0; d < NC; d++) h[d][tid] = 0;
                            int n = 0;
                            for (int t = 0; t < NS; t++) {
                                const int j = J[t];
                                if (j == 255) continue;
                                const int i = ix[t];
                                if (i >= nk) continue;
                                int d = j - (int)mk[mi][key[i]];
                                if (d < 0) d += NC;
                                h[d][tid]++;
                                n++;
                            }
                            u32 ss = 0;
                            for (int d = 0; d < NC; d++) ss += (u32)h[d][tid] * (u32)h[d][tid];
                            const int combo = ((var * 2 + map) * 2 + mode) * NM + mi;
#if DUMP == 1
                            dump[(g * NW + wi) * 96 + combo] = ss | ((u32)n << 16);
#endif
                            const float ioc = n > 1 ? (float)NC * (float)(ss - n) / ((float)n * (float)(n - 1)) : 0.0f;
                            int b = (int)((ioc - 0.8f) * 100.0f);
                            b = b < 0 ? 0 : (b > HB - 1 ? HB - 1 : b);
                            atomicAdd(&sh[b], 1u);
                            if (ioc >= thr) {
                                const u32 q = atomicAdd(ccount, 1u);
                                if (q < ccap) {
                                    cand[2 * q] = seed;
                                    cand[2 * q + 1] = ((u32)(ioc * 1000.0f) << 16) | ((u32)wi << 8) | (u32)combo;
                                }
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

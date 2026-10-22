"""Pure-Python Whirlpool (final version, ISO/IEC 10118-3), checked against published test vectors."""
E=[0x1,0xB,0x9,0xC,0xD,0x6,0xF,0x3,0xE,0x8,0x7,0x4,0xA,0x2,0x5,0x0]
EI=[E.index(i) for i in range(16)]
R=[0x7,0xC,0xB,0xD,0xE,0x4,0x9,0xF,0x6,0x3,0x8,0xA,0x2,0x5,0x1,0x0]
SB=[]
for u in range(256):
    a=E[u>>4]; b=EI[u&15]; r=R[a^b]
    SB.append((E[a^r]<<4)|EI[b^r])
def gmul(a,b):
    p=0
    while b:
        if b&1:p^=a
        a<<=1
        if a&0x100:a^=0x11D
        b>>=1
    return p
C=(1,1,4,1,8,5,2,9)
MUL=[[gmul(x,c) for x in range(256)] for c in set(C)]
MUL={c:[gmul(x,c) for x in range(256)] for c in set(C)}
RC=[[SB[8*(r-1)+j] for j in range(8)]+[0]*56 for r in range(1,11)]
def rnd(a,k):  # a: 64 bytes row-major
    g=[SB[x] for x in a]
    p=[0]*64
    for i in range(8):
        for j in range(8): p[i*8+j]=g[((i-j)%8)*8+j]
    o=[0]*64
    for i in range(8):
        row=p[i*8:i*8+8]
        for j in range(8):
            v=0
            for kk in range(8): v^=MUL[C[(j-kk)%8]][row[kk]]
            o[i*8+j]=v^k[i*8+j]
    return o
def whirlpool(data:bytes)->bytes:
    n=len(data)
    data=data+b"\x80"
    data+=b"\0"*((32-len(data))%64)+(n*8).to_bytes(32,"big")
    H=[0]*64
    for off in range(0,len(data),64):
        m=list(data[off:off+64])
        k=H[:]; s=[m[i]^k[i] for i in range(64)]
        for r in range(10):
            k=rnd(k,RC[r]); s=rnd(s,k)
        H=[H[i]^s[i]^m[i] for i in range(64)]
    return bytes(H)
if __name__=="__main__":
    print(whirlpool(b"").hex()[:32], "expect 19fa61d75522a4669b44e39c1d2e1726")
    print(whirlpool(b"abc").hex()[:32], "expect 4e2448a4c6f486bb16b6562c73b4020b")

# --- table-driven fast version (same function; checked against whirlpool() above) ---
M64=(1<<64)-1
def _ror(x,n): return ((x>>n)|(x<<(64-n)))&M64
_C0=[]
for x in range(256):
    s=SB[x]; v=0
    for c in C: v=(v<<8)|MUL[c][s]
    _C0.append(v)
_T=[[_ror(v,8*t) for v in _C0] for t in range(8)]
_RC=[sum(SB[8*(r-1)+j]<<(56-8*j) for j in range(8)) for r in range(1,11)]
def _rf(K,rc=None):
    T0,T1,T2,T3,T4,T5,T6,T7=_T
    out=[]
    for i in range(8):
        v=(T0[(K[i]>>56)]^T1[(K[(i-1)%8]>>48)&255]^T2[(K[(i-2)%8]>>40)&255]^T3[(K[(i-3)%8]>>32)&255]
           ^T4[(K[(i-4)%8]>>24)&255]^T5[(K[(i-5)%8]>>16)&255]^T6[(K[(i-6)%8]>>8)&255]^T7[K[(i-7)%8]&255])
        out.append(v)
    if rc is not None: out[0]^=rc
    return out
def whirlpool_fast(data:bytes)->bytes:
    n=len(data)
    data=data+b"\x80"
    data+=b"\0"*((32-len(data))%64)+(n*8).to_bytes(32,"big")
    H=[0]*8
    for off in range(0,len(data),64):
        m=[int.from_bytes(data[off+8*i:off+8*i+8],"big") for i in range(8)]
        K=H[:]; S=[m[i]^K[i] for i in range(8)]
        for r in range(10):
            K=_rf(K,_RC[r]); S=_rf(S)
            S=[S[i]^K[i] for i in range(8)]
        H=[H[i]^S[i]^m[i] for i in range(8)]
    return b"".join(h.to_bytes(8,"big") for h in H)
if __name__=="__main__":
    import os,time
    for t in (b"",b"abc",os.urandom(1000)):
        assert whirlpool(t)==whirlpool_fast(t)
    t0=time.time(); whirlpool_fast(bytes(100000)); print("fast ok", time.time()-t0)

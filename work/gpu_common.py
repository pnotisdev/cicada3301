"""CUDA helpers shared by work/kscreen/gpu.py and work/phpmt/gpu.py (CuPy + NVRTC; the CPU engines stay the reference)."""
import numpy as np

NVRTC_OPTIONS = ("--std=c++14", "--fmad=false")    # --fmad=false keeps float/double arithmetic identical to Rust


def device_info():
    import cupy as cp
    p = cp.cuda.runtime.getDeviceProperties(0)
    return {"name": p["name"].decode(), "cc": f"{p['major']}.{p['minor']}", "sms": p["multiProcessorCount"],
            "gib": round(p["totalGlobalMem"] / 2 ** 30, 1)}


def probe():
    """Is CUDA usable (cupy imports, a device exists, NVRTC compiles and a kernel runs)? Prints one line; 0 if so."""
    try:
        info = device_info()
        import cupy as cp
        k = cp.RawKernel('extern "C" __global__ void t(unsigned *a){ a[threadIdx.x] = threadIdx.x * 3u + 1u; }', "t")
        a = cp.zeros(32, cp.uint32)
        k((1,), (32,), (a,))
        assert (a.get() == np.arange(32) * 3 + 1).all(), "test kernel gave wrong values"
    except Exception as e:  # noqa: BLE001
        print(f"cuda unavailable: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")
        return 1
    print(f"cuda ok: {info['name']} (cc {info['cc']}, {info['sms']} SMs, {info['gib']} GiB)")
    return 0

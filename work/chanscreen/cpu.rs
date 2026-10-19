// Auditable CPU accelerator: full finite pointer range, float64, no fast math.
// No libraries, threads, caches, pruning, or data writes.
use std::slice;

fn pred(a: &[f64], j: usize, p: usize, qn: usize, lm: &[f64]) -> f64 {
    let mut v = 0.0;
    for r in 0..qn { v += a[j*qn+r] * lm[r*qn+p]; }
    v
}

// mode: 0 hold, 1 spend, 2 uncapped skip, 3 skip5, 4 coin.
#[no_mangle]
pub unsafe extern "C" fn likelihood(cp:*const i32,n:usize,kp:*const i32,m:usize,
    off:usize,sign:i32,q:f64,mode:i32,qn:usize,pip:*const f64,lmp:*const f64)->f64 {
    let c=slice::from_raw_parts(cp,n); let k=slice::from_raw_parts(kp,m);
    let pi=slice::from_raw_parts(pip,qn); let lm=slice::from_raw_parts(lmp,qn*qn);
    if n==0 {return 0.0;}
    if off>=m {return f64::NEG_INFINITY;}
    let mut a=vec![0.0;(m+1)*qn]; let mut b=a.clone();
    let first=(c[0]-sign*k[off]).rem_euclid(qn as i32) as usize;
    let mut total=pi[first].ln();
    if !total.is_finite() {return total;}
    a[(off+1)*qn+first]=1.0;
    for i in 1..n {
        b.fill(0.0);
        let prev=c[i-1]; let y=c[i];
        for j in off..m {
            if !(0..qn).any(|r| a[j*qn+r]!=0.0) {continue;}
            let direct=(y-sign*k[j]).rem_euclid(qn as i32) as usize;
            let coll=(prev-sign*k[j]).rem_euclid(qn as i32) as usize;
            if y!=prev {
                let v=pred(&a,j,direct,qn,lm);
                b[(j+1)*qn+direct]+=v;
            }
            let v=pred(&a,j,coll,qn,lm);
            if mode==0 || mode==1 {
                if y==prev { b[(j+1)*qn+coll]+=v*(1.0-q); }
                else { b[(j+mode as usize)*qn+coll]+=v*q/(qn-1) as f64; }
            } else if mode==4 {
                if j+1<m {
                    if y==prev {b[(j+2)*qn+coll]+=v*(1.0-q);}
                    if j+2<m && (coll as i32+sign*k[j+2]).rem_euclid(qn as i32)==y {
                        b[(j+3)*qn+coll]+=v*q;
                    }
                }
            } else {
                // Collision plaintext is fixed throughout every retry. Enumerate
                // the ENTIRE finite tail. Missing slots contribute to FAILURE.
                let mut w=v; let mut t=0;
                while j+t<m {
                    let x=(coll as i32+sign*k[j+t]).rem_euclid(qn as i32);
                    if x!=prev || (mode==3 && t==5) {
                        if x==y { b[(j+t+1)*qn+coll]+=w; }
                        break;
                    }
                    if x==y {b[(j+t+1)*qn+coll]+=w*(1.0-q);}
                    w*=q; t+=1;
                }
            }
        }
        let z:f64=b.iter().sum();
        if z==0.0 {return f64::NEG_INFINITY;}
        total+=z.ln();
        for v in b.iter_mut() {*v/=z;}
        std::mem::swap(&mut a,&mut b);
    }
    total
}

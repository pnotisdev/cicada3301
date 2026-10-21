// Word-edge channel for chanscreen v2 (phase 24). New file: backward.rs is untouched.
//
// backward_edge(..., kind, cand, nu) = backward() when kind==0 (the base body is copied below
// verbatim from backward.rs, so the default output is bit-identical by construction and by test).
//   kind 1: at every candidate position i (cand[i]!=0, i>=1) the ciphertext rune may be a KEYLESS NULL
//           with probability nu: it is emitted uniformly (1/Q), consumes no key value, and is invisible
//           to the anti-repeat check and to the language model (the next real rune compares with the
//           last REAL rune and the LM conditions on the last REAL plaintext).
//   kind 2: before the real rune at candidate position i (i>=1) the key pointer advances by one extra
//           value with probability nu.
// Modes hold(0) spend(1) skip5(3) coin(4) are supported for kind 1,2 (uncapped skip, mode 2, is not).
// Return code: 0 ok, 1 unsupported (mode 2 with kind!=0), 2 bad arguments.
use std::slice;
const NEG:f64=f64::NEG_INFINITY;
#[inline] fn add(a:f64,b:f64)->f64 {if a==NEG{return b;} if b==NEG{return a;} let x=a.max(b);x+(a.min(b)-x).exp().ln_1p()}
#[inline] fn rune(c:i32,k:i32,s:i32,q:usize)->usize{(c-s*k).rem_euclid(q as i32) as usize}
fn cls(c:&[i32],k:&[i32],i:usize,j:usize,s:i32,q:usize,mode:i32)->[usize;2]{
 let mut out=[q,q];
 if j>0 {out[0]=rune(c[i-1],k[j-1],s,q);}
 if i>=2 {
  let second=if mode==0 && j<k.len(){rune(c[i-2],k[j],s,q)}
   else if mode==1 && j>0{rune(c[i-2],k[j-1],s,q)}
   else if mode==4 && j>=2{rune(c[i-2],k[j-2],s,q)}else{q};
  if second!=q && second!=out[0]{if out[0]==q{out[0]=second;}else{out[1]=second;}}
 }
 out
}
#[inline] fn get(b:&[[f64;2]],r:&[[usize;2]],h:usize,p:usize)->f64{
 if r[h][0]==p{b[h][0]}else if r[h][1]==p{b[h][1]}else{NEG}
}
#[derive(Clone,Copy)] struct Edge{p:usize,h:usize,w:f64}
fn push(es:&mut [Edge;6],len:&mut usize,p:usize,h:usize,w:f64){if w!=NEG{es[*len]=Edge{p,h,w};*len+=1;}}

// ---- base channel (copied verbatim from backward.rs; the only change is the function name) ----
unsafe fn backward_base(cp:*const i32,n:usize,kp:*const i32,m:usize,
 s:i32,q:f64,mode:i32,qn:usize,pip:*const f64,lmp:*const f64,op:*mut f64){
 let c=slice::from_raw_parts(cp,n);let k=slice::from_raw_parts(kp,m);
 let pi=slice::from_raw_parts(pip,qn);let lm=slice::from_raw_parts(lmp,qn*qn);
 let out=slice::from_raw_parts_mut(op,2*(m+1));
 if n==0{out.fill(0.);return;}
 let logs:Vec<f64>=lm.iter().map(|x|x.ln()).collect();
 let lq=q.ln();let lk=(1.-q).ln();let lu=-(qn as f64).ln();let lr=lq-((qn-1) as f64).ln();
 let mut ends=vec![m;m];
 for j in (0..m).rev(){if j+1<m && k[j]==k[j+1]{ends[j]=ends[j+1];}else{ends[j]=j+1;}}
 let mut rs:Vec<[usize;2]>=(0..=m).map(|j|cls(c,k,n,j,s,qn,mode)).collect();
 let mut b=vec![[0.;2];m+1];let mut u=vec![0.;m+1];
 let mut a=vec![[NEG;2];m+1];let mut v=vec![NEG;m+1];let mut rt=rs.clone();
 let mut tail=vec![NEG;m+1];let mut utail=tail.clone();
 for i in (1..n).rev(){
  let prev=c[i-1];let y=c[i];
  a.fill([NEG;2]);v.fill(NEG);tail.fill(NEG);utail.fill(NEG);
  for j in (0..=m).rev(){
   let cr=cls(c,k,i,j,s,qn,mode);rt[j]=cr;
   if j==m{continue;}
   let p=rune(prev,k[j],s,qn);let d=rune(y,k[j],s,qn);
   if mode==2 && y==prev {
    tail[j]=lk+get(&b,&rs,j+1,p);utail[j]=lk+u[j+1];
    if j+1<m && k[j]==k[j+1]{tail[j]=add(tail[j],lq+tail[j+1]);utail[j]=add(utail[j],lq+utail[j+1]);}
    for z in 0..2{if cr[z]<qn{a[j][z]=logs[cr[z]*qn+p]+tail[j];}}
    v[j]=lu+utail[j];continue;
   }
   let mut es=[Edge{p:0,h:0,w:0.};6];let mut len=0;
   if y!=prev{push(&mut es,&mut len,d,j+1,0.);}
   if mode==0 || mode==1{
    if y==prev{push(&mut es,&mut len,p,j+1,lk);}
    else{push(&mut es,&mut len,p,j+mode as usize,lr);}
   }else if mode==4{
    if j+1<m {
     if y==prev{push(&mut es,&mut len,p,j+2,lk);}
     if j+2<m && (p as i32+s*k[j+2]).rem_euclid(qn as i32)==y{push(&mut es,&mut len,p,j+3,lq);}
    }
   }else if mode==2 {
    let h=ends[j];
    if h<m && (p as i32+s*k[h]).rem_euclid(qn as i32)==y{push(&mut es,&mut len,p,h+1,(h-j) as f64*lq);}
   }else{
    let mut w=0.;
    for t in 0..6{
     let h=j+t;if h>=m{break;}
     let x=(p as i32+s*k[h]).rem_euclid(qn as i32);
     if x!=prev || t==5{if x==y{push(&mut es,&mut len,p,h+1,w);}break;}
     if x==y{push(&mut es,&mut len,p,h+1,w+lk);}
     w+=lq;
    }
   }
   for e in &es[..len]{
    let suffix=e.w+get(&b,&rs,e.h,e.p);
    for z in 0..2{if cr[z]<qn{a[j][z]=add(a[j][z],logs[cr[z]*qn+e.p]+suffix);}}
    v[j]=add(v[j],lu+e.w+u[e.h]);
   }
  }
  std::mem::swap(&mut a,&mut b);std::mem::swap(&mut u,&mut v);std::mem::swap(&mut rs,&mut rt);
 }
 for o in 0..m{let p=rune(c[0],k[o],s,qn);out[2*o]=pi[p].ln()+get(&b,&rs,o+1,p);out[2*o+1]=lu+u[o+1];}
 out[2*m]=NEG;out[2*m+1]=NEG;
}

// ---- edges of one emission step from pointer j, previous REAL ciphertext rune prev, observed y (modes 0,1,3,4) ----
fn mk_edges(k:&[i32],m:usize,j:usize,prev:i32,y:i32,s:i32,qn:usize,mode:i32,lk:f64,lq:f64,lr:f64,es:&mut [Edge;6])->usize{
 let mut len=0;
 let p=rune(prev,k[j],s,qn);let d=rune(y,k[j],s,qn);
 if y!=prev{push(es,&mut len,d,j+1,0.);}
 if mode==0 || mode==1{
  if y==prev{push(es,&mut len,p,j+1,lk);}
  else{push(es,&mut len,p,j+mode as usize,lr);}
 }else if mode==4{
  if j+1<m {
   if y==prev{push(es,&mut len,p,j+2,lk);}
   if j+2<m && (p as i32+s*k[j+2]).rem_euclid(qn as i32)==y{push(es,&mut len,p,j+3,lq);}
  }
 }else{
  let mut w=0.;
  for t in 0..6{
   let h=j+t;if h>=m{break;}
   let x=(p as i32+s*k[h]).rem_euclid(qn as i32);
   if x!=prev || t==5{if x==y{push(es,&mut len,p,h+1,w);}break;}
   if x==y{push(es,&mut len,p,h+1,w+lk);}
   w+=lq;
  }
 }
 len
}

// ---- kind 2: extra key advance before the real rune at candidate positions ----
unsafe fn backward_adv(c:&[i32],k:&[i32],cand:&[u8],s:i32,q:f64,mode:i32,qn:usize,nu:f64,
 pi:&[f64],lm:&[f64],out:&mut [f64]){
 let n=c.len();let m=k.len();
 let logs:Vec<f64>=lm.iter().map(|x|x.ln()).collect();
 let lq=q.ln();let lk=(1.-q).ln();let lu=-(qn as f64).ln();let lr=lq-((qn-1) as f64).ln();
 let lnu=nu.ln();let lnn=(1.-nu).ln();
 let mut rs:Vec<[usize;2]>=(0..=m).map(|j|cls(c,k,n,j,s,qn,mode)).collect();
 let mut b=vec![[0.;2];m+1];let mut u=vec![0.;m+1];
 let mut a=vec![[NEG;2];m+1];let mut v=vec![NEG;m+1];let mut rt=rs.clone();
 for i in (1..n).rev(){
  let prev=c[i-1];let y=c[i];let adv=cand[i]!=0;
  a.fill([NEG;2]);v.fill(NEG);
  for j in (0..=m).rev(){
   let cr=cls(c,k,i,j,s,qn,mode);rt[j]=cr;
   if j==m{continue;}
   let mut es=[Edge{p:0,h:0,w:0.};6];
   for pass in 0..2{
    let jj=j+pass;
    if pass==1 && !(adv && jj<m){break;}
    let wn=if !adv{0.}else if pass==0{lnn}else{lnu};
    let len=mk_edges(k,m,jj,prev,y,s,qn,mode,lk,lq,lr,&mut es);
    for e in &es[..len]{
     let suffix=wn+e.w+get(&b,&rs,e.h,e.p);
     for z in 0..2{if cr[z]<qn{a[j][z]=add(a[j][z],logs[cr[z]*qn+e.p]+suffix);}}
     v[j]=add(v[j],lu+wn+e.w+u[e.h]);
    }
   }
  }
  std::mem::swap(&mut a,&mut b);std::mem::swap(&mut u,&mut v);std::mem::swap(&mut rs,&mut rt);
 }
 for o in 0..m{let p=rune(c[0],k[o],s,qn);out[2*o]=pi[p].ln()+get(&b,&rs,o+1,p);out[2*o+1]=lu+u[o+1];}
 out[2*m]=NEG;out[2*m+1]=NEG;
}

// ---- kind 1: keyless nulls. State (j, d, r): d = nulls emitted since the last real rune. ----
// Class list of (i,j,d): ordinary (last real cipher rune with key j-1) plus the collision class of every
// possible earlier real rune (a run of candidate positions can hide it). 255 = empty slot.
fn fill_cls(c:&[i32],k:&[i32],cand:&[u8],i:usize,d:usize,j:usize,s:i32,qn:usize,mode:i32,out:&mut [u8]){
 out.fill(255);
 let mut cnt=0;
 let t=i-1-d;
 if j>0{out[0]=rune(c[t],k[j-1],s,qn) as u8;cnt=1;}
 if t>=1 && mode!=3{
  let mut tp=t-1;
  loop{
   let kj:Option<i32>=if mode==0 && j<k.len(){Some(k[j])}else if mode==1 && j>0{Some(k[j-1])}else if mode==4 && j>=2{Some(k[j-2])}else{None};
   if let Some(kv)=kj{
    let r=rune(c[tp],kv,s,qn) as u8;
    if !out[..cnt].contains(&r){out[cnt]=r;cnt+=1;}
   }
   // an earlier real rune can sit behind positions tp.. t-1 only if all of tp.. are candidate nulls
   if tp>=1 && cand[tp]!=0{tp-=1;}else{break;}
  }
 }
}

unsafe fn backward_null(c:&[i32],k:&[i32],cand:&[u8],s:i32,q:f64,mode:i32,qn:usize,nu:f64,
 pi:&[f64],lm:&[f64],out:&mut [f64]){
 let n=c.len();let m=k.len();
 let logs:Vec<f64>=lm.iter().map(|x|x.ln()).collect();
 let lq=q.ln();let lk=(1.-q).ln();let lu=-(qn as f64).ln();let lr=lq-((qn-1) as f64).ln();
 let lnu=nu.ln();let lnn=(1.-nu).ln();
 // dm[i] = number of consecutive candidate positions ending at i-1 (positions >=1)
 let mut dm=vec![0usize;n+1];
 for i in 1..=n{dm[i]=if i>=2 && cand[i-1]!=0{dm[i-1]+1}else if cand[i-1]!=0 && i-1>=1{1}else{0};}
 let dmax=*dm.iter().max().unwrap();
 let kk=dmax+2;let w=m+1;let nd=dmax+1;
 let mut rs=vec![255u8;nd*w*kk];let mut rt=rs.clone();
 let mut b=vec![NEG;nd*w*kk];let mut a=b.clone();
 let mut u=vec![NEG;nd*w];let mut v=u.clone();
 for d in 0..=dm[n]{for j in 0..=m{
  fill_cls(c,k,cand,n,d,j,s,qn,mode,&mut rs[(d*w+j)*kk..(d*w+j+1)*kk]);
  for z in 0..kk{if rs[(d*w+j)*kk+z]!=255{b[(d*w+j)*kk+z]=0.;}}
  u[d*w+j]=0.;
 }}
 let lookup=|b:&[f64],rs:&[u8],d:usize,h:usize,p:usize|->f64{
  let base=(d*w+h)*kk;
  for z in 0..kk{let r=rs[base+z];if r==255{break;}if r as usize==p{return b[base+z];}}
  NEG
 };
 for i in (1..n).rev(){
  let y=c[i];let cd=cand[i]!=0;
  let wr=if cd{lnn}else{0.};
  for x in a.iter_mut(){*x=NEG;}for x in v.iter_mut(){*x=NEG;}
  for d in 0..=dm[i]{
   let prev=c[i-1-d];
   for j in (0..=m).rev(){
    let base=(d*w+j)*kk;
    fill_cls(c,k,cand,i,d,j,s,qn,mode,&mut rt[base..base+kk]);
    // null branch: same state, one more trailing null
    if cd{
     let nb=((d+1)*w+j)*kk;
     for z in 0..kk{
      if rt[base+z]==255{break;}
      // classes of (i+1,j,d+1) equal those of (i,j,d); use the slot with the same class value
      let r=rt[base+z] as usize;
      let val=lookup(&b,&rs,d+1,j,r);
      if val!=NEG{a[base+z]=add(a[base+z],lnu+lu+val);}
      let _=nb;
     }
     v[d*w+j]=add(v[d*w+j],lnu+lu+u[(d+1)*w+j]);
    }
    if j==m{continue;}
    let mut es=[Edge{p:0,h:0,w:0.};6];
    let len=mk_edges(k,m,j,prev,y,s,qn,mode,lk,lq,lr,&mut es);
    for e in &es[..len]{
     let suffix=wr+e.w+lookup(&b,&rs,0,e.h,e.p);
     for z in 0..kk{
      let r=rt[base+z];if r==255{break;}
      a[base+z]=add(a[base+z],logs[r as usize*qn+e.p]+suffix);
     }
     v[d*w+j]=add(v[d*w+j],lu+wr+e.w+u[e.h]);
    }
   }
  }
  std::mem::swap(&mut a,&mut b);std::mem::swap(&mut u,&mut v);std::mem::swap(&mut rs,&mut rt);
 }
 for o in 0..m{
  let p=rune(c[0],k[o],s,qn);
  out[2*o]=pi[p].ln()+lookup(&b,&rs,0,o+1,p);out[2*o+1]=lu+u[o+1];
 }
 out[2*m]=NEG;out[2*m+1]=NEG;
}

#[no_mangle]
pub unsafe extern "C" fn backward_edge(cp:*const i32,n:usize,kp:*const i32,m:usize,
 s:i32,q:f64,mode:i32,qn:usize,pip:*const f64,lmp:*const f64,op:*mut f64,
 kind:i32,candp:*const u8,nu:f64)->i32{
 if kind==0{backward_base(cp,n,kp,m,s,q,mode,qn,pip,lmp,op);return 0;}
 if kind<0 || kind>2 || qn>=255 || !(0.0..=1.0).contains(&nu){return 2;}
 if mode==2 || mode<0 || mode>4{return 1;}
 let c=slice::from_raw_parts(cp,n);let k=slice::from_raw_parts(kp,m);
 let pi=slice::from_raw_parts(pip,qn);let lm=slice::from_raw_parts(lmp,qn*qn);
 let out=slice::from_raw_parts_mut(op,2*(m+1));
 if n==0{out.fill(0.);return 0;}
 let mut cand=slice::from_raw_parts(candp,n).to_vec();
 cand[0]=0; // a null or advance before the first rune is an offset shift / unknown start: not modelled
 if kind==1{backward_null(c,k,&cand,s,q,mode,qn,nu,pi,lm,out);}else{backward_adv(c,k,&cand,s,q,mode,qn,nu,pi,lm,out);}
 0
}

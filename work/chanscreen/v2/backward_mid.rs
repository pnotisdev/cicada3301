// Mid-word keyless-null channel for chanscreen v2 (phase 51). New file: backward.rs and backward_edge.rs are untouched.
//
// backward_mid(..., kind, cand, nu, wstart): kinds 0, 1, 2 are backward_edge() (its source is included verbatim below, so the
// default and the edge-arc outputs are bit-identical by construction and by test).
//   kind 3: per word (wstart[i]!=0 starts a word; position 0 always does) of cipher length Lc>=3, with probability nu ONE keyless
//           null sits at an interior position t in 1..Lc-2 (probability nu/(Lc-2) each, uniform 1/Q emission, no key value, invisible
//           to the anti-repeat check and the language model, as the edge null); with probability 1-nu none. Words with Lc<3: no slot.
// Return code: 0 ok, 1 unsupported (mode 2), 2 bad arguments.
include!("backward_edge.rs");

// classes of a state whose last real cipher rune is at index t, pointer j: the ordinary one plus the collision class of the real rune
// before it (position t-1, or t-2 when t-1 could be the null). 255 = empty slot.
fn fill_m(c:&[i32],k:&[i32],cand:&[u8],t:usize,j:usize,s:i32,qn:usize,mode:i32,out:&mut [u8]){
 out[..3].fill(255);
 let mut cnt=0;
 if j>0{out[0]=rune(c[t],k[j-1],s,qn) as u8;cnt=1;}
 if t>=1 && mode!=3{
  let kv:Option<i32>=if mode==0 && j<k.len(){Some(k[j])}else if mode==1 && j>0{Some(k[j-1])}else if mode==4 && j>=2{Some(k[j-2])}else{None};
  if let Some(kv)=kv{
   let mut tp=t-1;
   for step in 0..2{
    let r=rune(c[tp],kv,s,qn) as u8;
    if !out[..cnt].contains(&r){out[cnt]=r;cnt+=1;}
    if step==0 && tp>=1 && cand[tp]!=0{tp-=1;}else{break;}
   }
  }
 }
}

unsafe fn backward_midword(c:&[i32],k:&[i32],ws:&[u8],s:i32,q:f64,mode:i32,qn:usize,nu:f64,
 pi:&[f64],lm:&[f64],out:&mut [f64]){
 let n=c.len();let m=k.len();
 let logs:Vec<f64>=lm.iter().map(|x|x.ln()).collect();
 let lq=q.ln();let lk=(1.-q).ln();let lu=-(qn as f64).ln();let lr=lq-((qn-1) as f64).ln();
 let lnu=nu.ln();let lnn=(1.-nu).ln();
 // word structure: cand[i] = interior slot, nullw[i] = ln(nu/(Lc-2)), endw[i] = ln(1-nu) at the last position of a word with Lc>=3, isend[i]
 let mut cand=vec![0u8;n];let mut nullw=vec![NEG;n];let mut endw=vec![0.;n];let mut isend=vec![false;n];
 let mut a0=0;
 while a0<n{
  let mut b0=a0+1;while b0<n && ws[b0]==0{b0+=1;}
  let lc=b0-a0;
  if lc>=3{
   for i in a0+1..b0-1{cand[i]=1;nullw[i]=lnu-((lc-2) as f64).ln();}
   endw[b0-1]=lnn;
  }
  isend[b0-1]=true;
  a0=b0;
 }
 // forward reachability of the three states: 0 = (no null yet in this word), 1 = (null used, last position real), 2 = (null at the previous position)
 let mut reach=vec![[false;3];n+1];
 reach[1.min(n)][0]=true;
 for i in 1..n{
  for st in 0..3{
   if !reach[i][st]{continue;}
   let u=st>=1;
   reach[i+1][if isend[i]{0}else if u{1}else{0}]=true;
   if cand[i]!=0 && st==0{reach[i+1][2]=true;}
  }
 }
 let w=m+1;let kk=3;
 let ix=|st:usize,j:usize|->usize{(st*w+j)*kk};
 let mut rs=vec![255u8;3*w*kk];let mut rt=rs.clone();
 let mut b=vec![NEG;3*w*kk];let mut a=b.clone();
 let mut u=vec![NEG;3*w];let mut v=u.clone();
 for st in 0..3{
  if !reach[n][st]{continue;}
  let t=n-1-(st==2) as usize;
  for j in 0..=m{
   fill_m(c,k,&cand,t,j,s,qn,mode,&mut rs[ix(st,j)..ix(st,j)+kk]);
   for z in 0..kk{if rs[ix(st,j)+z]!=255{b[ix(st,j)+z]=0.;}}
   u[st*w+j]=0.;
  }
 }
 let lookup=|b:&[f64],rs:&[u8],st:usize,h:usize,p:usize|->f64{
  let base=ix(st,h);
  for z in 0..kk{let r=rs[base+z];if r==255{break;}if r as usize==p{return b[base+z];}}
  NEG
 };
 for i in (1..n).rev(){
  let y=c[i];
  for x in a.iter_mut(){*x=NEG;}for x in v.iter_mut(){*x=NEG;}
  for st in 0..3{
   if !reach[i][st]{continue;}
   let d=(st==2) as usize;let t=i-1-d;let prev=c[t];
   let uf=st>=1;
   let stn=if isend[i]{0}else if uf{1}else{0};
   let wr=if isend[i] && !uf{endw[i]}else{0.};
   for j in (0..=m).rev(){
    let base=ix(st,j);
    fill_m(c,k,&cand,t,j,s,qn,mode,&mut rt[base..base+kk]);
    if cand[i]!=0 && st==0{
     for z in 0..kk{
      let r=rt[base+z];if r==255{break;}
      let val=lookup(&b,&rs,2,j,r as usize);
      if val!=NEG{a[base+z]=add(a[base+z],nullw[i]+lu+val);}
     }
     v[st*w+j]=add(v[st*w+j],nullw[i]+lu+u[2*w+j]);
    }
    if j==m{continue;}
    let mut es=[Edge{p:0,h:0,w:0.};6];
    let len=mk_edges(k,m,j,prev,y,s,qn,mode,lk,lq,lr,&mut es);
    for e in &es[..len]{
     let suffix=wr+e.w+lookup(&b,&rs,stn,e.h,e.p);
     for z in 0..kk{
      let r=rt[base+z];if r==255{break;}
      a[base+z]=add(a[base+z],logs[r as usize*qn+e.p]+suffix);
     }
     v[st*w+j]=add(v[st*w+j],lu+wr+e.w+u[stn*w+e.h]);
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
pub unsafe extern "C" fn backward_mid(cp:*const i32,n:usize,kp:*const i32,m:usize,
 s:i32,q:f64,mode:i32,qn:usize,pip:*const f64,lmp:*const f64,op:*mut f64,
 kind:i32,candp:*const u8,nu:f64,wsp:*const u8)->i32{
 if kind<3{return backward_edge(cp,n,kp,m,s,q,mode,qn,pip,lmp,op,kind,candp,nu);}
 if kind>3 || qn>=255 || !(0.0..=1.0).contains(&nu){return 2;}
 if mode==2 || mode<0 || mode>4{return 1;}
 let c=slice::from_raw_parts(cp,n);let k=slice::from_raw_parts(kp,m);
 let pi=slice::from_raw_parts(pip,qn);let lm=slice::from_raw_parts(lmp,qn*qn);
 let out=slice::from_raw_parts_mut(op,2*(m+1));
 if n==0{out.fill(0.);return 0;}
 let ws=slice::from_raw_parts(wsp,n);
 backward_midword(c,k,ws,s,q,mode,qn,nu,pi,lm,out);
 0
}

// Union keyless-null arc for chanscreen v2 (R4 repair session s08). New file: nothing existing is touched.
//
// backward_union(..., place, nu, wstart): per word (wstart[i]!=0 starts a word; position 0 always does) of cipher length Lc, with probability nu ONE keyless null
// sits at one slot of the word's slot set S (probability nu/|S| each; uniform 1/Q emission, no key value, invisible to the anti-repeat check and the language model,
// exactly as the mid arc / edge arc nulls); with probability 1-nu none. Words whose S is empty carry no weight.
//   place 0: S = {0..Lc-1} (Lc>=2)   -- the union arc: R4 as fitted (null slot uniform over 0..L, word edges included)
//   place 1: S = {1..Lc-2} (Lc>=3)   -- the mid arc (kind 3 of backward_mid), for the reduction gate
//   place 2: S = {0, Lc-1} (Lc>=2)   -- edge slots only (diagnostic)
// A null at the LAST position of word A and one at the FIRST position of word B are adjacent nulls (one per word); the real rune after them compares with the real rune before.
// A null at window position 0 is allowed (first word with 0 in S): c[1] is then the first real rune (no previous rune, LM starts at pi).
// Helpers (add, rune, mk_edges, Edge, NEG, ...) come from backward_edge.rs, included verbatim. Return code: 0 ok, 1 unsupported (mode 2), 2 bad arguments.
include!("../chanscreen/v2/backward_edge.rs");

// classes of a state whose last real cipher rune is at index t, pointer j: the ordinary one plus the collision classes of the real rune before it
// (at t-1, or t-2 / t-3 when the positions between may hold nulls). 255 = empty slot. nl[i]!=0: position i may be a null; ws[i]!=0: position i starts a word.
fn fill_u(c:&[i32],k:&[i32],nl:&[u8],ws:&[u8],t:usize,j:usize,s:i32,qn:usize,mode:i32,out:&mut [u8]){
 out[..4].fill(255);
 let mut cnt=0;
 if j>0{out[0]=rune(c[t],k[j-1],s,qn) as u8;cnt=1;}
 if t>=1 && mode!=3{
  let kv:Option<i32>=if mode==0 && j<k.len(){Some(k[j])}else if mode==1 && j>0{Some(k[j-1])}else if mode==4 && j>=2{Some(k[j-2])}else{None};
  if let Some(kv)=kv{
   let mut tp=t-1;let mut hops=0;
   loop{
    let r=rune(c[tp],kv,s,qn) as u8;
    if !out[..cnt].contains(&r){out[cnt]=r;cnt+=1;}
    if hops==0 && tp>=1 && nl[tp]!=0{tp-=1;hops=1;}
    else if hops==1 && tp>=1 && nl[tp]!=0 && ws[tp+1]!=0{tp-=1;hops=2;}
    else{break;}
   }
  }
 }
}

// states: 0=A (u0,d0)  1=B (u1,d0)  2=C (u1,d1)  3=D (u0,d1)  4=E (u1,d2)
const DST:[usize;5]=[0,0,1,1,2];
const UST:[bool;5]=[false,true,true,false,true];

unsafe fn backward_un(c:&[i32],k:&[i32],ws:&[u8],s:i32,q:f64,mode:i32,qn:usize,nu:f64,place:i32,
 pi:&[f64],lm:&[f64],out:&mut [f64]){
 let n=c.len();let m=k.len();
 let logs:Vec<f64>=lm.iter().map(|x|x.ln()).collect();
 let lq=q.ln();let lk=(1.-q).ln();let lu=-(qn as f64).ln();let lr=lq-((qn-1) as f64).ln();
 let lnu=nu.ln();let lnn=(1.-nu).ln();
 let mut nl=vec![0u8;n];let mut nullw=vec![NEG;n];let mut endw=vec![0.;n];let mut isend=vec![false;n];
 let mut a0=0;
 while a0<n{
  let mut b0=a0+1;while b0<n && ws[b0]==0{b0+=1;}
  let lc=b0-a0;
  let slots:Vec<usize>=match place{
   0=>if lc>=2{(a0..b0).collect()}else{vec![]},
   1=>if lc>=3{(a0+1..b0-1).collect()}else{vec![]},
   _=>if lc>=2{vec![a0,b0-1]}else{vec![]},
  };
  if !slots.is_empty(){
   let wl=lnu-(slots.len() as f64).ln();
   for &t in &slots{nl[t]=1;nullw[t]=wl;}
   endw[b0-1]=lnn;
  }
  isend[b0-1]=true;
  a0=b0;
 }
 // transitions out of state st at position i: (next state after a real rune, end weight, Some(next state after a null))
 let trans=|st:usize,i:usize|->(usize,f64,Option<usize>){
  let u=UST[st];let ise=isend[i];
  let sr=if ise||!u{0}else{1};
  let wr=if ise&&!u{endw[i]}else{0.};
  let sn=if !u && nl[i]!=0{Some(if st==0{if ise{3}else{2}}else{4})}else{None};
  (sr,wr,sn)
 };
 // forward reachability; 1.min(n) as the start state A; a null at window position 0 starts state (B or A) at position 2
 let mut reach=vec![[false;5];n+1];
 if n>=1{reach[1][0]=true;}
 let null0= n>=2 && nl[0]!=0;
 let stn0=if n>=2{if isend[1]{0}else{1}}else{0};
 if null0{reach[2][stn0]=true;}
 for i in 1..n{
  for st in 0..5{
   if !reach[i][st]{continue;}
   let (sr,_,sn)=trans(st,i);
   reach[i+1][sr]=true;
   if let Some(x)=sn{reach[i+1][x]=true;}
  }
 }
 let w=m+1;let kk=4;
 let ix=|st:usize,j:usize|->usize{(st*w+j)*kk};
 let mut rs=vec![255u8;5*w*kk];let mut rt=rs.clone();
 let mut b=vec![NEG;5*w*kk];let mut a=b.clone();
 let mut u=vec![NEG;5*w];let mut v=u.clone();
 for st in 0..5{
  if !reach[n][st]{continue;}
  let t=n-1-DST[st];
  for j in 0..=m{
   fill_u(c,k,&nl,ws,t,j,s,qn,mode,&mut rs[ix(st,j)..ix(st,j)+kk]);
   for z in 0..kk{if rs[ix(st,j)+z]!=255{b[ix(st,j)+z]=0.;}}
   u[st*w+j]=0.;
  }
 }
 let lookup=|b:&[f64],rs:&[u8],st:usize,h:usize,p:usize|->f64{
  let base=ix(st,h);
  for z in 0..kk{let r=rs[base+z];if r==255{break;}if r as usize==p{return b[base+z];}}
  NEG
 };
 let mut n0l=vec![NEG;m];let mut n0u=vec![NEG;m];
 for i in (1..n).rev(){
  let y=c[i];
  if i==1 && null0{
   // b,u,rs hold position 2 here: c[0] is a null (weight nullw[0], 1/Q), c[1] is the first real rune, key pointer o, no anti-repeat comparison, LM starts at pi
   for o in 0..m{
    let p1=rune(c[1],k[o],s,qn);
    let val=lookup(&b,&rs,stn0,o+1,p1);
    n0l[o]=nullw[0]+lu+pi[p1].ln()+val;
    n0u[o]=nullw[0]+lu+lu+u[stn0*w+o+1];
   }
  }
  for st in 0..5{
   if !reach[i][st]{continue;}
   for x in a[st*w*kk..(st+1)*w*kk].iter_mut(){*x=NEG;}
   for x in v[st*w..(st+1)*w].iter_mut(){*x=NEG;}
  }
  for st in 0..5{
   if !reach[i][st]{continue;}
   let t=i-1-DST[st];let prev=c[t];
   let (sr,wr,sn)=trans(st,i);
   for j in (0..=m).rev(){
    let base=ix(st,j);
    fill_u(c,k,&nl,ws,t,j,s,qn,mode,&mut rt[base..base+kk]);
    if let Some(sx)=sn{
     for z in 0..kk{
      let r=rt[base+z];if r==255{break;}
      let val=lookup(&b,&rs,sx,j,r as usize);
      if val!=NEG{a[base+z]=add(a[base+z],nullw[i]+lu+val);}
     }
     v[st*w+j]=add(v[st*w+j],nullw[i]+lu+u[sx*w+j]);
    }
    if j==m{continue;}
    let mut es=[Edge{p:0,h:0,w:0.};6];
    let len=mk_edges(k,m,j,prev,y,s,qn,mode,lk,lq,lr,&mut es);
    for e in &es[..len]{
     let suffix=wr+e.w+lookup(&b,&rs,sr,e.h,e.p);
     for z in 0..kk{
      let r=rt[base+z];if r==255{break;}
      a[base+z]=add(a[base+z],logs[r as usize*qn+e.p]+suffix);
     }
     v[st*w+j]=add(v[st*w+j],lu+wr+e.w+u[sr*w+e.h]);
    }
   }
  }
  std::mem::swap(&mut a,&mut b);std::mem::swap(&mut u,&mut v);std::mem::swap(&mut rs,&mut rt);
 }
 for o in 0..m{
  let p=rune(c[0],k[o],s,qn);
  let l=pi[p].ln()+lookup(&b,&rs,0,o+1,p);let un=lu+u[o+1];
  out[2*o]=if null0{add(l,n0l[o])}else{l};
  out[2*o+1]=if null0{add(un,n0u[o])}else{un};
 }
 out[2*m]=NEG;out[2*m+1]=NEG;
}

#[no_mangle]
pub unsafe extern "C" fn backward_union(cp:*const i32,n:usize,kp:*const i32,m:usize,
 s:i32,q:f64,mode:i32,qn:usize,pip:*const f64,lmp:*const f64,op:*mut f64,
 place:i32,nu:f64,wsp:*const u8)->i32{
 if place<0 || place>2 || qn>=255 || !(0.0..=1.0).contains(&nu){return 2;}
 if mode==2 || mode<0 || mode>4{return 1;}
 let c=slice::from_raw_parts(cp,n);let k=slice::from_raw_parts(kp,m);
 let pi=slice::from_raw_parts(pip,qn);let lm=slice::from_raw_parts(lmp,qn*qn);
 let out=slice::from_raw_parts_mut(op,2*(m+1));
 if n==0{out.fill(0.);return 0;}
 let ws=slice::from_raw_parts(wsp,n);
 backward_un(c,k,ws,s,q,mode,qn,nu,place,pi,lm,out);
 0
}

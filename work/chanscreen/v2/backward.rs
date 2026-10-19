// Full finite-state all-offset backward log likelihood. No dependencies/threads.
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
// Outputs interleaved [log_L(o), log_U(o)] for all o=0..m. mode as v1.
#[no_mangle]
pub unsafe extern "C" fn backward(cp:*const i32,n:usize,kp:*const i32,m:usize,
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

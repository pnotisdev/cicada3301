// Exact finite-state float64 forward; no beam or band. One block per cell.
#include <math.h>
__device__ int modq(int x,int Q){int v=x%Q;return v<0?v+Q:v;}
extern "C" __global__ void forward(
 const int* cs,const int* ks,const int* ns,const int* ms,const int* os,
 const int* signs,const double* qs,const int* modes,int NC,int MC,int Q,
 const double* pi,const double* lm,int uniform,double* AA,double* BB,double* out){
 int cell=blockIdx.x,t=threadIdx.x,n=ns[cell],m=ms[cell],off=os[cell],sg=signs[cell],mode=modes[cell];
 const int *c=cs+cell*NC,*k=ks+cell*MC; double q=qs[cell];
 int stride=(MC+1)*Q;
 double *a=AA+(long long)cell*stride,*b=BB+(long long)cell*stride;
 __shared__ double red[128],total,z;
 if(n==0){if(t==0)out[cell]=0;return;}
 if(off>=m){if(t==0)out[cell]=-INFINITY;return;}
 for(int s=t;s<stride;s+=128)a[s]=0;
 __syncthreads();
 if(t==0){int p=modq(c[0]-sg*k[off],Q);total=log(uniform?1.0/Q:pi[p]);a[(off+1)*Q+p]=1;}
 __syncthreads();
 if(!isfinite(total)){if(t==0)out[cell]=total;return;}
 for(int i=1;i<n;i++){
  for(int s=t;s<stride;s+=128)b[s]=0;
  __syncthreads();
  int prev=c[i-1],y=c[i];
  for(int j=off+t;j<m;j+=128){
   int d=modq(y-sg*k[j],Q),p=modq(prev-sg*k[j],Q);
   double vd=0,v=0;
   for(int r=0;r<Q;r++){
    double ar=a[j*Q+r];
    vd+=ar*(uniform?1.0/Q:lm[r*Q+d]);
    v+=ar*(uniform?1.0/Q:lm[r*Q+p]);
   }
   if(y!=prev && vd!=0)atomicAdd(&b[(j+1)*Q+d],vd);
   if(v==0)continue;
   if(mode==0 || mode==1){
    if(y==prev)atomicAdd(&b[(j+1)*Q+p],v*(1-q));
    else atomicAdd(&b[(j+mode)*Q+p],v*q/(Q-1));
   }else if(mode==4){
    if(j+1<m){
     if(y==prev)atomicAdd(&b[(j+2)*Q+p],v*(1-q));
     if(j+2<m && modq(p+sg*k[j+2],Q)==y)atomicAdd(&b[(j+3)*Q+p],v*q);
    }
   }else{
    double w=v;int h=0;
    while(j+h<m){
     int x=modq(p+sg*k[j+h],Q);
     if(x!=prev || (mode==3 && h==5)){
      if(x==y)atomicAdd(&b[(j+h+1)*Q+p],w);
      break;
     }
     if(x==y)atomicAdd(&b[(j+h+1)*Q+p],w*(1-q));
     w*=q;h++;
    }
   }
  }
  __syncthreads();
  double part=0;for(int s=t;s<stride;s+=128)part+=b[s];red[t]=part;
  __syncthreads();
  for(int d=64;d;d/=2){if(t<d)red[t]+=red[t+d];__syncthreads();}
  if(t==0){z=red[0];total+=log(z);}
  __syncthreads();
  if(z==0){if(t==0)out[cell]=-INFINITY;return;}
  for(int s=t;s<stride;s+=128)b[s]/=z;
  __syncthreads();
  double* tmp=a;a=b;b=tmp;
 }
 if(t==0)out[cell]=total;
}

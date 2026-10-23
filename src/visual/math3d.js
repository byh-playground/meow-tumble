const V = (x=0,y=0,z=0)=>[x,y,z];
const vadd=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
const vsub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const vmul=(a,s)=>[a[0]*s,a[1]*s,a[2]*s];
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const len=a=>Math.hypot(a[0],a[1],a[2]);
const norm=a=>{let k=len(a)||1;return vmul(a,1/k)};
const clamp=(a,lo,hi)=>Math.max(lo,Math.min(hi,a));
const lerp=(a,b,t)=>a+(b-a)*t;
const smooth=(a,b,t)=>{const v=clamp((t-a)/(b-a),0,1);return v*v*(3-2*v)};
const Q=()=>[0,0,0,1];
const qyaw=a=>[0,Math.sin(a/2),0,Math.cos(a/2)];
function qnorm(q){let l=Math.hypot(...q)||1;return q.map(v=>v/l)}
function qmul(a,b){return [a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]]}
function qrotate(q,v){const u=[q[0],q[1],q[2]],s=q[3],t=vmul(cross(u,v),2);return vadd(v,vadd(vmul(t,s),cross(u,t)));}
function qupdate(q,w,dt){const mag=len(w);if(mag<1e-8)return q;const half=mag*dt/2, sn=Math.sin(half)/mag;return qnorm(qmul([w[0]*sn,w[1]*sn,w[2]*sn,Math.cos(half)],q))}
const m4=()=>new Float32Array(16);
function compose(p,q,s){const x=q[0],y=q[1],z=q[2],w=q[3],x2=x+x,y2=y+y,z2=z+z,xx=x*x2,xy=x*y2,xz=x*z2,yy=y*y2,yz=y*z2,zz=z*z2,wx=w*x2,wy=w*y2,wz=w*z2;let o=m4();
 o[0]=(1-(yy+zz))*s[0];o[1]=(xy+wz)*s[0];o[2]=(xz-wy)*s[0];o[3]=0;
 o[4]=(xy-wz)*s[1];o[5]=(1-(xx+zz))*s[1];o[6]=(yz+wx)*s[1];o[7]=0;
 o[8]=(xz+wy)*s[2];o[9]=(yz-wx)*s[2];o[10]=(1-(xx+yy))*s[2];o[11]=0;
 o[12]=p[0];o[13]=p[1];o[14]=p[2];o[15]=1;return o;}
function matmul(a,b){let o=m4();for(let c=0;c<4;c++)for(let r=0;r<4;r++)o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3];return o}
function perspective(fovy,aspect,near,far){const f=1/Math.tan(fovy/2),p=m4();p[0]=f/aspect;p[5]=f;p[10]=(far+near)/(near-far);p[11]=-1;p[14]=2*far*near/(near-far);return p}
function lookAt(eye,target){const z=norm(vsub(eye,target)),x=norm(cross([0,1,0],z)),y=cross(z,x),m=m4();m[0]=x[0];m[1]=y[0];m[2]=z[0];m[4]=x[1];m[5]=y[1];m[6]=z[1];m[8]=x[2];m[9]=y[2];m[10]=z[2];m[12]=-dot(x,eye);m[13]=-dot(y,eye);m[14]=-dot(z,eye);m[15]=1;return m}
function rgb(hex){const clean=hex.replace('#','');const v=parseInt(clean,16);return [(v>>16&255)/255,(v>>8&255)/255,(v&255)/255,1]}

export { V, vadd, vsub, vmul, dot, cross, len, norm, clamp, lerp, smooth, Q, qyaw, qnorm, qmul, qrotate, qupdate, m4, compose, matmul, perspective, lookAt, rgb };

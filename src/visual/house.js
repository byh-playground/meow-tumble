import { Q, vadd, qrotate, norm } from './math3d.js';
import { COLOR } from './geometry.js';

/* Static house material system — all visuals are generated once; simulation never reads these. */
const MATERIALS=Object.freeze({
  oak:{tile:0,scale:.28},walnut:{tile:1,scale:.32},planks:{tile:2,scale:.26},paint:{tile:3,scale:.12},
  tile:{tile:4,scale:.27},sofa:{tile:5,scale:.43},rug:{tile:6,scale:.31},linen:{tile:7,scale:.41},
  stone:{tile:8,scale:.30},steel:{tile:9,scale:.35},marble:{tile:10,scale:.26},leather:{tile:11,scale:.5},
  ceramic:{tile:12,scale:.35},curtain:{tile:13,scale:.36},books:{tile:14,scale:.26},foliage:{tile:15,scale:.42},
});
function makeHouseAtlas(){
 const SIDE=192,GRID=4,canvas=document.createElement('canvas');canvas.width=canvas.height=SIDE*GRID;
 const ctx=canvas.getContext('2d',{alpha:false});let seed=787222;
 function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
 function rect(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(x,y,w,h)}
 function stroke(x1,y1,x2,y2,color,width=1){ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()}
 function grain(base,dark,light,plankCount){rect(0,0,SIDE,SIDE,base);
  const stride=SIDE/plankCount;
  for(let j=0;j<plankCount;j++){
   let y=j*stride+.5;stroke(0,y,SIDE,y,dark,1.3);
   for(let k=0;k<2;k++){
    const xx=(k*SIDE/2+(j%2)*SIDE/4)%SIDE;stroke(xx,y,xx,y+stride,dark,.8);
   }
   for(let i=0;i<36;i++){
    const py=y+rand()*stride,px=rand()*SIDE;stroke(px,py,px+12+rand()*90,py+(rand()-.5)*1.8,rand()<.65?dark:light,rand()*.85+.2);
   }
  }
 }
 for(let t=0;t<16;t++){
  ctx.save();ctx.translate(t%GRID*SIDE,Math.floor(t/GRID)*SIDE);
  switch(t){
   case 0:grain('#dbb17c','#ae805d65','#ffe4b76a',4);break;
   case 1:grain('#906247','#462a2277','#c08b6477',5);break;
   case 2:grain('#c29d70','#89694b89','#f2d2a38a',6);break;
   case 3:rect(0,0,SIDE,SIDE,'#e8e0d2');for(let i=0;i<3000;i++){let x=rand()*SIDE,y=rand()*SIDE;rect(x,y,rand()*.8+.3,rand()*.8+.3,rand()<.45?'#ffffff26':'#acafa226');}break;
   case 4:rect(0,0,SIDE,SIDE,'#dad6cc');for(let i=0;i<=4;i++){stroke(i*SIDE/4,0,i*SIDE/4,SIDE,'#8e979479',2.3);stroke(0,i*SIDE/4,SIDE,i*SIDE/4,'#8e979479',2.3)}for(let i=0;i<85;i++){const x=rand()*SIDE,y=rand()*SIDE;rect(x,y,rand()*3+.5,rand()*3+.5,'#ffffff18')}break;
   case 5:rect(0,0,SIDE,SIDE,'#9fa99b');for(let x=0;x<SIDE;x+=3)for(let y=0;y<SIDE;y+=3){rect(x,y,1.1,1.1,(x+y)%6?'#26362a1d':'#fcf5d344');}break;
   case 6:rect(0,0,SIDE,SIDE,'#c2a384');for(let i=0;i<9;i++)stroke(0,9+i*20,SIDE,9+i*20,'#efe1cf64',2);for(let j=0;j<2100;j++)rect(rand()*SIDE,rand()*SIDE,1,2,rand()<.5?'#5e6b6640':'#f8eec546');break;
   case 7:rect(0,0,SIDE,SIDE,'#e7dfd1');for(let i=0;i<3200;i++)rect(rand()*SIDE,rand()*SIDE,1,1.6,rand()<.5?'#b6aa9962':'#ffffff60');break;
   case 8:rect(0,0,SIDE,SIDE,'#b9b4aa');for(let i=0;i<800;i++){const x=rand()*SIDE,y=rand()*SIDE,r=rand()*2.4+.5;ctx.fillStyle=['#ebe0cb','#819089','#eae9e5','#9c837b'][Math.floor(rand()*4)]+'78';ctx.beginPath();ctx.ellipse(x,y,r,r*.55,rand()*3,0,Math.PI*2);ctx.fill();}break;
   case 9:rect(0,0,SIDE,SIDE,'#b2babd');for(let i=0;i<400;i++){const x=rand()*SIDE;stroke(x,0,x,SIDE,rand()<.5?'#edf2f345':'#5d6c7160',rand()*.8+.2)}break;
   case 10:rect(0,0,SIDE,SIDE,'#e9e8df');for(let i=0;i<16;i++){let x=rand()*SIDE;ctx.beginPath();ctx.strokeStyle=i%3?'#9faca052':'#c2c5ba85';ctx.lineWidth=rand()*1.8+.5;ctx.moveTo(x,-20);for(let y=0;y<220;y+=8){x+=rand()*10-5;ctx.lineTo(x,y)}ctx.stroke();}break;
   case 11:rect(0,0,SIDE,SIDE,'#967466');for(let i=0;i<2500;i++)rect(rand()*SIDE,rand()*SIDE,rand()*1.6+.4,rand()*1.6+.4,rand()<.5?'#523c3452':'#e6b39a48');break;
   case 12:rect(0,0,SIDE,SIDE,'#ebe9df');for(let i=0;i<140;i++){let x=rand()*SIDE,y=rand()*SIDE;rect(x,y,rand()*5+.5,.5,'#ffffff75')}break;
   case 13:rect(0,0,SIDE,SIDE,'#d1b4a6');for(let x=0;x<SIDE;x+=17){rect(x,0,9,SIDE,'#927d7c38');stroke(x+9,0,x+9,SIDE,'#f5e8e091',1)}break;
   case 14:rect(0,0,SIDE,SIDE,'#785f53');for(let x=0;x<SIDE;x+=11){rect(x,0,8,SIDE,['#769ba0','#cca47e','#b27d86','#a8a172','#9b96b0'][Math.floor(rand()*5)]);stroke(x+2,26,x+6,26,'#e2d2ac',1.2);stroke(x+2,144,x+6,144,'#e2d2ac',1.2)}break;
   case 15:rect(0,0,SIDE,SIDE,'#648b64');for(let i=0;i<700;i++)stroke(rand()*SIDE,rand()*SIDE,rand()*SIDE,rand()*SIDE,rand()<.5?'#44775b4a':'#bad3a04a',.5);break;
  }
  ctx.restore();
 }
 return canvas;
}

/* Immutable visual geometry compiled into a few GPU batches. Decor is NEVER a physics owner. */
class HouseScene {
 constructor(){this.items=[];this.batches=[];this.alpha=[];this.ready=false;this.triangleCount=0;}
 cube(p,s,c,q=Q(),a=1,mat=null){this.draw('cube',p,s,c,q,a,mat)}
 orb(p,s,c,mat=null){this.draw('sphere',p,s,c,Q(),1,mat)}
 tube(p,s,c,q=Q(),mat=null){this.draw('cylinder',p,s,c,q,1,mat)}
 cone(p,s,c,q=Q(),mat=null){this.draw('cone',p,s,c,q,1,mat)}
 disc(p,r,c,a=.2){this.draw('disc',p,[r,1,r],c,Q(),a,null)}
 ring(p,r,c,a=.9){this.draw('ring',p,[r,1,r],c,Q(),a,null)}
 draw(type,p,s,c,q=Q(),a=1,mat=null){this.items.push({type,p,s,c,q,a,mat});}
 bake(renderer){
  if(this.ready)return;const gl=renderer.gl;
  const stride=13, chunks=[];let verts=[],indices=[],indexBase=0;
  const flush=()=>{if(!indexBase)return;
   const v=gl.createBuffer(),i=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,v);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);
   gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,i);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(indices),gl.STATIC_DRAW);
   chunks.push({vertex:v,index:i,count:indices.length});verts=[];indices=[];indexBase=0;
  };
  for(const item of this.items){
   if(item.a<.99){this.alpha.push(item);continue;}
   const geom=renderer.sourceMeshes[item.type];if(!geom)continue;
   const {pos,norm:normals,ind,uv}=geom,n=pos.length/3;if(indexBase+n>64000)flush();
   const mat=typeof item.mat==='string'?MATERIALS[item.mat]:item.mat,tile=mat?.tile??-1,scale=mat?.scale??.2;
   const col=typeof item.c==='string'?COLOR[item.c]:item.c;
   for(let j=0;j<n;j++){
    const xx=pos[j*3]*item.s[0],yy=pos[j*3+1]*item.s[1],zz=pos[j*3+2]*item.s[2];
    const pp=vadd(item.p,qrotate(item.q,[xx,yy,zz]));
    const nn=norm(qrotate(item.q,[normals[j*3]/Math.max(.01,item.s[0]),normals[j*3+1]/Math.max(.01,item.s[1]),normals[j*3+2]/Math.max(.01,item.s[2])]));
    let u=uv[j*2]??.5,vv=uv[j*2+1]??.5;
    if(item.type==='cube'){
     const normalX=Math.abs(normals[j*3]),normalY=Math.abs(normals[j*3+1]);
     const du=normalX>0.5?item.s[2]:item.s[0], dv=normalY>0.5?item.s[2]:item.s[1];
     u*=du*scale;vv*=dv*scale;
    }else{u*=Math.max(item.s[0],item.s[2])*scale;vv*=item.s[1]*scale;}
    verts.push(pp[0],pp[1],pp[2],nn[0],nn[1],nn[2],u,vv,col[0],col[1],col[2],col[3]??1,tile);
   }
   for(const idx of ind)indices.push(idx+indexBase);
   indexBase+=n;this.triangleCount+=ind.length/3;
  }
  flush();this.batches=chunks;this.ready=true;this.items.length=0;
 }
 render(renderer){const gl=renderer.gl;if(!this.ready)this.bake(renderer);const a=renderer.attrib,u=renderer.u;
  gl.useProgram(renderer.prog);gl.uniform1f(u.staticMode,1);gl.uniformMatrix4fv(u.vp,false,renderer.vp);
  for(const chunk of this.batches){gl.bindBuffer(gl.ARRAY_BUFFER,chunk.vertex);
   const stride=13*4;function ptr(key,sz,offset){gl.enableVertexAttribArray(a[key]);gl.vertexAttribPointer(a[key],sz,gl.FLOAT,false,stride,offset*4)}
   ptr('p',3,0);ptr('n',3,3);ptr('uv',2,6);ptr('tint',4,8);ptr('tile',1,12);
   gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,chunk.index);gl.drawElements(gl.TRIANGLES,chunk.count,gl.UNSIGNED_SHORT,0);renderer.drawCalls++;
  }
  gl.uniform1f(u.staticMode,0);
  for(const item of this.alpha){renderer.draw(item.type,item.p,item.s,item.c,item.q,item.a,1,item.mat)}
 }
 dispose(renderer){const gl=renderer.gl;for(const b of this.batches){gl.deleteBuffer(b.vertex);gl.deleteBuffer(b.index);}this.batches=[];this.ready=false;this.alpha=[];}
}


export { MATERIALS, makeHouseAtlas, HouseScene };

import { V, vadd, vsub, vmul, dot, cross, len, norm, clamp, lerp, smooth, Q, qyaw, qnorm, qmul, qrotate, qupdate, m4, compose, matmul, perspective, lookAt, rgb } from './math3d.js';
import { COLOR, meshCube, meshSphere, meshCylinder, meshRing, meshDisc } from './geometry.js';
import { MATERIALS, makeHouseAtlas, HouseScene } from './house.js';

class Toon3D {
 constructor(canvas){this.canvas=canvas;const gl=canvas.getContext('webgl',{alpha:false,antialias:true,depth:true,preserveDrawingBuffer:false});if(!gl)throw new Error('WebGL이 지원되지 않습니다.');this.gl=gl;this.resources=[];
 const vs=`precision mediump float;
attribute vec3 p;attribute vec3 n;attribute vec2 uv;attribute vec4 tint;attribute float tile;
uniform mat4 model;uniform mat4 vp;uniform vec4 col;uniform float unlit;uniform float staticMode;uniform float dynamicTile;uniform vec2 uvScale;
varying vec3 normal;varying vec3 worldPos;varying vec2 texUv;varying vec4 fragCol;varying float fragTile;varying float fragUnlit;
void main(){vec4 wp=staticMode>.5?vec4(p,1.):model*vec4(p,1.);
worldPos=wp.xyz;normal=staticMode>.5?n:mat3(model)*n;
texUv=staticMode>.5?uv:uv*uvScale;fragCol=staticMode>.5?tint:col;
fragTile=staticMode>.5?tile:dynamicTile;fragUnlit=staticMode>.5?0.:unlit;
gl_Position=vp*wp;}`;
 const fs=`precision mediump float;
uniform sampler2D atlas;
varying vec3 normal;varying vec3 worldPos;varying vec2 texUv;varying vec4 fragCol;varying float fragTile;varying float fragUnlit;
void main(){vec3 nn=normalize(normal);float sun=max(0.,dot(nn,normalize(vec3(-.4,.89,.52))));
float illum=.70+.31*sun;float indirect=.045*exp(-length(worldPos.xz-vec2(0.,0.))/24.);
float lamp=0.;
lamp+=.16*exp(-length((worldPos.xz-vec2(-33.,-14.)))/18.);
lamp+=.14*exp(-length((worldPos.xz-vec2(34.,-15.)))/18.);
lamp+=.11*exp(-length((worldPos.xz-vec2(-33.,23.)))/19.);
illum=min(1.18,illum+indirect+lamp);
vec3 pigment=vec3(1.);
if(fragTile>-.5){float t=floor(fragTile+.5);
vec2 tiled=vec2(mod(t,4.),floor(t/4.));
vec2 fracUv=fract(texUv);pigment=texture2D(atlas,(tiled+mix(vec2(.012),vec2(.988),fracUv))/4.).rgb;}
vec3 color=fragCol.rgb*pigment*mix(illum,1.,fragUnlit);
color=pow(max(color,vec3(.00001)),vec3(.96));
gl_FragColor=vec4(color,fragCol.a);}`;
 const sh=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s};const prog=gl.createProgram();gl.attachShader(prog,sh(gl.VERTEX_SHADER,vs));gl.attachShader(prog,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(prog));gl.useProgram(prog);this.prog=prog;
 this.attrib={p:gl.getAttribLocation(prog,'p'),n:gl.getAttribLocation(prog,'n'),uv:gl.getAttribLocation(prog,'uv'),tint:gl.getAttribLocation(prog,'tint'),tile:gl.getAttribLocation(prog,'tile')};
 this.u={model:gl.getUniformLocation(prog,'model'),vp:gl.getUniformLocation(prog,'vp'),col:gl.getUniformLocation(prog,'col'),unlit:gl.getUniformLocation(prog,'unlit'),staticMode:gl.getUniformLocation(prog,'staticMode'),dynamicTile:gl.getUniformLocation(prog,'dynamicTile'),uvScale:gl.getUniformLocation(prog,'uvScale'),atlas:gl.getUniformLocation(prog,'atlas')};
 this.sourceMeshes={cube:meshCube(),sphere:meshSphere(),cylinder:meshCylinder(),cone:meshCylinder(16,true),ring:meshRing(),disc:meshDisc()};
 this.mesh=Object.fromEntries(Object.entries(this.sourceMeshes).map(([key,geometry])=>[key,this.make(geometry)]));
 this.atlasTexture=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.atlasTexture);
 gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,makeHouseAtlas());
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 gl.uniform1i(this.u.atlas,0);gl.uniform1f(this.u.staticMode,0);
 gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.clearColor(.83,.89,.86,1);this.drawCalls=0;this.lastW=0;this.lastH=0;this.vp=m4();this.eye=V();}
 make(g){const gl=this.gl,p=gl.createBuffer(),n=gl.createBuffer(),uv=gl.createBuffer(),i=gl.createBuffer();
 if(!g.uv){g.uv=[];for(let j=0;j<g.pos.length/3;j++){g.uv.push(g.pos[j*3]*.5+.5,g.pos[j*3+2]*.5+.5)}}
 gl.bindBuffer(gl.ARRAY_BUFFER,p);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(g.pos),gl.STATIC_DRAW);
 gl.bindBuffer(gl.ARRAY_BUFFER,n);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(g.norm),gl.STATIC_DRAW);
 gl.bindBuffer(gl.ARRAY_BUFFER,uv);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(g.uv),gl.STATIC_DRAW);
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,i);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(g.ind),gl.STATIC_DRAW);
 this.resources.push(p,n,uv,i);return{p,n,uv,i,count:g.ind.length}}
 resize(){const c=this.canvas,dpr=Math.min(devicePixelRatio||1,innerWidth<650?1.45:1.8);const w=Math.max(1,Math.round(c.clientWidth*dpr)),h=Math.max(1,Math.round(c.clientHeight*dpr));if(c.width!==w||c.height!==h){c.width=w;c.height=h;}if(w!==this.lastW||h!==this.lastH){this.gl.viewport(0,0,w,h);this.lastW=w;this.lastH=h;}}
 frame(eye,target){this.resize();this.eye=eye;const aspect=this.canvas.clientWidth/Math.max(1,this.canvas.clientHeight);const fov=aspect<.75?1.38:Math.PI/3.12;const proj=perspective(fov,this.lastW/this.lastH,.08,150);this.vp=matmul(proj,lookAt(eye,target));const gl=this.gl;gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(this.prog);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.atlasTexture);gl.uniformMatrix4fv(this.u.vp,false,this.vp);gl.uniform1f(this.u.staticMode,0);this.drawCalls=0;}
 draw(mesh,p,s,col,q=Q(),alpha=1,unlit=0,mat=null){const gl=this.gl,g=this.mesh[mesh];if(!g)return;let m=compose(p,q,s);
 const c=typeof col==='string'?COLOR[col]:col;
 gl.uniform1f(this.u.staticMode,0);gl.uniformMatrix4fv(this.u.model,false,m);
 gl.uniform4f(this.u.col,c[0],c[1],c[2],(c[3]??1)*alpha*(this.localOpacity??1));
 gl.uniform1f(this.u.unlit,unlit);const material=typeof mat==='string'?MATERIALS[mat]:mat;
 gl.uniform1f(this.u.dynamicTile,material?.tile??-1);const rep=material?.scale??1;
 gl.uniform2f(this.u.uvScale,Math.max(1,s[0]*rep),Math.max(1,s[2]*rep));
 gl.bindBuffer(gl.ARRAY_BUFFER,g.p);gl.enableVertexAttribArray(this.attrib.p);gl.vertexAttribPointer(this.attrib.p,3,gl.FLOAT,false,0,0);
 gl.bindBuffer(gl.ARRAY_BUFFER,g.n);gl.enableVertexAttribArray(this.attrib.n);gl.vertexAttribPointer(this.attrib.n,3,gl.FLOAT,false,0,0);
 gl.bindBuffer(gl.ARRAY_BUFFER,g.uv);gl.enableVertexAttribArray(this.attrib.uv);gl.vertexAttribPointer(this.attrib.uv,2,gl.FLOAT,false,0,0);
 gl.disableVertexAttribArray(this.attrib.tint);gl.vertexAttrib4f(this.attrib.tint,1,1,1,1);
 gl.disableVertexAttribArray(this.attrib.tile);gl.vertexAttrib1f(this.attrib.tile,-1);
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,g.i);gl.drawElements(gl.TRIANGLES,g.count,gl.UNSIGNED_SHORT,0);this.drawCalls++}
 cube(p,s,col,q=Q(),a=1,mat=null){this.draw('cube',p,s,col,q,a,0,mat)}
 orb(p,s,col,mat=null){this.draw('sphere',p,s,col,Q(),1,0,mat)}
 tube(p,s,col,q=Q(),mat=null){this.draw('cylinder',p,s,col,q,1,0,mat)}
 cone(p,s,col,q=Q(),mat=null){this.draw('cone',p,s,col,q,1,0,mat)}
 disc(p,r,col,a=.2){this.gl.depthMask(false);this.draw('disc',p,[r,1,r],col,Q(),a,1);this.gl.depthMask(true)}
 ring(p,r,col,a=.9){this.gl.depthMask(false);this.draw('ring',p,[r,1,r],col,Q(),a,1);this.gl.depthMask(true)}
 screen(p){const m=this.vp,x=p[0],y=p[1],z=p[2],w=m[3]*x+m[7]*y+m[11]*z+m[15];if(w<=0)return null;const nx=(m[0]*x+m[4]*y+m[8]*z+m[12])/w,ny=(m[1]*x+m[5]*y+m[9]*z+m[13])/w;return{x:(nx*.5+.5)*this.canvas.clientWidth,y:(-.5*ny+.5)*this.canvas.clientHeight,w};}
 }

export { Toon3D };

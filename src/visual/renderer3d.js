import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Q, compose } from './math3d.js';
import { COLOR, meshCube, meshSphere, meshCylinder, meshRing, meshDisc } from './geometry.js';
import { MATERIALS, makeHouseAtlas } from './house.js';

/* The renderer keeps the old immediate-mode calls (cube/orb/tube/cone/disc/ring/draw) so game drawing code is
   unchanged, but a frame is now a three.js scene: every call acquires a pooled Mesh, ordered by call sequence,
   and render() submits the scene once. Authored glb models join the same scene. */
THREE.ColorManagement.enabled = false;

const VERTEX = `
varying vec3 vNormal;varying vec3 vWorld;varying vec2 vUv;varying vec4 vColor;varying float vTile;varying float vUnlit;
#ifdef STATIC
attribute vec4 tint;attribute float tile;
#else
uniform vec4 col;uniform float unlit;uniform float dynamicTile;uniform vec2 uvScale;
#endif
void main(){
#ifdef STATIC
 vec4 wp=vec4(position,1.);vNormal=normal;vUv=uv;vColor=tint;vTile=tile;vUnlit=0.;
#else
 vec4 wp=modelMatrix*vec4(position,1.);vNormal=mat3(modelMatrix)*normal;vUv=uv*uvScale;vColor=col;vTile=dynamicTile;vUnlit=unlit;
#endif
 vWorld=wp.xyz;gl_Position=projectionMatrix*viewMatrix*wp;}`;

const FRAGMENT = `
uniform sampler2D atlas;
varying vec3 vNormal;varying vec3 vWorld;varying vec2 vUv;varying vec4 vColor;varying float vTile;varying float vUnlit;
void main(){vec3 nn=normalize(vNormal);float sun=max(0.,dot(nn,normalize(vec3(-.4,.89,.52))));
float illum=.70+.31*sun;float indirect=.045*exp(-length(vWorld.xz-vec2(0.,0.))/24.);
float lamp=0.;
lamp+=.16*exp(-length((vWorld.xz-vec2(-33.,-14.)))/18.);
lamp+=.14*exp(-length((vWorld.xz-vec2(34.,-15.)))/18.);
lamp+=.11*exp(-length((vWorld.xz-vec2(-33.,23.)))/19.);
illum=min(1.18,illum+indirect+lamp);
vec3 pigment=vec3(1.);
if(vTile>-.5){float t=floor(vTile+.5);
vec2 tiled=vec2(mod(t,4.),floor(t/4.));
vec2 fracUv=fract(vUv);pigment=texture2D(atlas,(tiled+mix(vec2(.012),vec2(.988),fracUv))/4.).rgb;}
vec3 color=vColor.rgb*pigment*mix(illum,1.,vUnlit);
color=pow(max(color,vec3(.00001)),vec3(.96));
gl_FragColor=vec4(color,vColor.a);}`;

function toGeometry(source) {
  const g = new THREE.BufferGeometry();
  // Meshes without authored uv get a planar projection; baked house geometry reads the same values from the source.
  const uv = source.uv ??= Array.from({ length: source.pos.length / 3 * 2 }, (_, k) => source.pos[Math.floor(k / 2) * 3 + (k % 2 ? 2 : 0)] * .5 + .5);
  g.setAttribute('position', new THREE.Float32BufferAttribute(source.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(source.norm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(new THREE.Uint16BufferAttribute(source.ind, 1));
  return g;
}

class Toon3D {
  constructor(canvas) {
    this.canvas = canvas;
    this.three = new THREE.WebGLRenderer({ canvas, alpha: false, antialias: true, depth: true, powerPreference: 'high-performance' });
    this.three.outputColorSpace = THREE.LinearSRGBColorSpace;
    this.three.setClearColor(new THREE.Color(.83, .89, .86), 1);
    this.three.autoClear = true;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(60, 1, .08, 150);
    this.atlas = new THREE.CanvasTexture(makeHouseAtlas());
    this.atlas.flipY = false; this.atlas.generateMipmaps = false;
    this.atlas.minFilter = THREE.LinearFilter; this.atlas.magFilter = THREE.LinearFilter;
    this.atlas.wrapS = this.atlas.wrapT = THREE.ClampToEdgeWrapping; this.atlas.colorSpace = THREE.NoColorSpace;
    const material = (isStatic, depthWrite) => new THREE.ShaderMaterial({
      vertexShader: VERTEX, fragmentShader: FRAGMENT, defines: isStatic ? { STATIC: 1 } : {},
      uniforms: {
        atlas: { value: this.atlas }, col: { value: new THREE.Vector4(1, 1, 1, 1) }, unlit: { value: 0 },
        dynamicTile: { value: -1 }, uvScale: { value: new THREE.Vector2(1, 1) },
      },
      transparent: true, depthTest: true, depthWrite, side: THREE.FrontSide,
    });
    this.materials = { write: material(false, true), noWrite: material(false, false), house: material(true, true) };
    this.sourceMeshes = { cube: meshCube(), sphere: meshSphere(), cylinder: meshCylinder(), cone: meshCylinder(16, true), ring: meshRing(), disc: meshDisc() };
    this.geometry = Object.fromEntries(Object.entries(this.sourceMeshes).map(([key, source]) => [key, toGeometry(source)]));
    this.pool = Object.fromEntries(Object.keys(this.geometry).map(key => [key, { meshes: [], used: 0 }]));
    this.statics = new Set();
    this.depthWrite = true;
    this.localOpacity = 1;
    this.seq = 0;
    this.drawCalls = 0;
    this.lastW = 0; this.lastH = 0;
    this.vp = new THREE.Matrix4();
    this.eye = [0, 0, 0];
  }

  /* Authored glb models draw through the same call-ordered path as primitives: draw('<name>', ...). `modelSize`
     is the authored bounding box so callers can scale a model to a physics size without knowing the asset. */
  async loadModels(urls) {
    const loader = new GLTFLoader(); this.modelSize ??= {};
    await Promise.all(Object.entries(urls).map(async ([name, url]) => {
      const gltf = await loader.loadAsync(url); let mesh = null;
      gltf.scene.traverse(node => { if (!mesh && node.isMesh) mesh = node; });
      if (!mesh) throw new Error(`${url}: 메시가 없습니다.`);
      const g = mesh.geometry.clone(); g.applyMatrix4(mesh.matrixWorld);
      if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(g.attributes.position.count * 2).fill(0), 2));
      g.computeBoundingBox(); const size = g.boundingBox.getSize(new THREE.Vector3());
      this.modelSize[name] = [size.x, size.y, size.z]; this.geometry[name] = g; this.pool[name] = { meshes: [], used: 0 };
    }));
  }

  resize() {
    const c = this.canvas, dpr = Math.min(devicePixelRatio || 1, innerWidth < 650 ? 1.45 : 1.8);
    const w = Math.max(1, Math.round(c.clientWidth * dpr)), h = Math.max(1, Math.round(c.clientHeight * dpr));
    if (w !== this.lastW || h !== this.lastH) { this.three.setPixelRatio(1); this.three.setSize(w, h, false); this.lastW = w; this.lastH = h; }
  }

  frame(eye, target) {
    this.resize(); this.eye = eye;
    const aspect = this.canvas.clientWidth / Math.max(1, this.canvas.clientHeight);
    const cam = this.camera;
    cam.fov = (aspect < .75 ? 1.38 : Math.PI / 3.12) * 180 / Math.PI;
    cam.aspect = this.lastW / this.lastH; cam.near = .08; cam.far = 150; cam.updateProjectionMatrix();
    cam.position.set(eye[0], eye[1], eye[2]); cam.up.set(0, 1, 0); cam.lookAt(target[0], target[1], target[2]); cam.updateMatrixWorld(true);
    this.vp.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse);
    for (const entry of Object.values(this.pool)) { for (let i = 0; i < entry.used; i++) entry.meshes[i].visible = false; entry.used = 0; }
    for (const mesh of this.statics) mesh.visible = false;
    this.seq = 0; this.depthWrite = true;
  }

  render() { this.three.render(this.scene, this.camera); this.drawCalls = this.three.info.render.calls; }

  /* A static mesh (house batch, authored model) takes part in the same call-ordered pass as pooled primitives. */
  addStatic(mesh) { mesh.frustumCulled = false; mesh.visible = false; this.scene.add(mesh); this.statics.add(mesh); return mesh; }
  removeStatic(mesh) { this.scene.remove(mesh); this.statics.delete(mesh); }
  show(mesh) { mesh.visible = true; mesh.renderOrder = this.seq++; }

  acquire(kind) {
    const entry = this.pool[kind];
    if (entry.used === entry.meshes.length) {
      const mesh = new THREE.Mesh(this.geometry[kind], this.materials.write);
      mesh.frustumCulled = false; mesh.matrixAutoUpdate = false; mesh.matrixWorldAutoUpdate = false;
      mesh.onBeforeRender = (renderer, scene, camera, geometry, mat) => {
        const d = mesh.userData, u = mat.uniforms;
        u.col.value.set(d.r, d.g, d.b, d.a); u.unlit.value = d.unlit; u.dynamicTile.value = d.tile; u.uvScale.value.set(d.uvx, d.uvy);
        mat.uniformsNeedUpdate = true;
      };
      this.scene.add(mesh); entry.meshes.push(mesh);
    }
    return entry.meshes[entry.used++];
  }

  draw(kind, p, s, col, q = Q(), alpha = 1, unlit = 0, mat = null, forceNoDepthWrite = false) {
    if (!this.geometry[kind]) return;
    const mesh = this.acquire(kind), c = typeof col === 'string' ? COLOR[col] : col;
    const material = typeof mat === 'string' ? MATERIALS[mat] : mat, rep = material?.scale ?? 1, d = mesh.userData;
    mesh.matrixWorld.fromArray(compose(p, q, s));
    mesh.material = forceNoDepthWrite || !this.depthWrite ? this.materials.noWrite : this.materials.write;
    d.r = c[0]; d.g = c[1]; d.b = c[2]; d.a = (c[3] ?? 1) * alpha * this.localOpacity; d.unlit = unlit;
    d.tile = material?.tile ?? -1; d.uvx = Math.max(1, s[0] * rep); d.uvy = Math.max(1, s[2] * rep);
    this.show(mesh);
  }

  cube(p, s, col, q = Q(), a = 1, mat = null) { this.draw('cube', p, s, col, q, a, 0, mat); }
  orb(p, s, col, mat = null) { this.draw('sphere', p, s, col, Q(), 1, 0, mat); }
  tube(p, s, col, q = Q(), mat = null) { this.draw('cylinder', p, s, col, q, 1, 0, mat); }
  cone(p, s, col, q = Q(), mat = null) { this.draw('cone', p, s, col, q, 1, 0, mat); }
  disc(p, r, col, a = .2) { this.draw('disc', p, [r, 1, r], col, Q(), a, 1, null, true); }
  ring(p, r, col, a = .9) { this.draw('ring', p, [r, 1, r], col, Q(), a, 1, null, true); }

  screen(p) {
    const m = this.vp.elements, x = p[0], y = p[1], z = p[2], w = m[3] * x + m[7] * y + m[11] * z + m[15];
    if (w <= 0) return null;
    const nx = (m[0] * x + m[4] * y + m[8] * z + m[12]) / w, ny = (m[1] * x + m[5] * y + m[9] * z + m[13]) / w;
    return { x: (nx * .5 + .5) * this.canvas.clientWidth, y: (-.5 * ny + .5) * this.canvas.clientHeight, w };
  }
}

export { Toon3D, THREE };

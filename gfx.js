/* DRIFT graphics: WebGL generators for the nebula, planets, asteroids and the wormhole lens.
 * Everything here renders to offscreen canvases that the 2D game draws as images.
 * If WebGL is missing or a shader fails, window.DriftGFX.ok stays false and the game
 * falls back to its plain canvas drawing. */
(function () {
  'use strict';

  const VS = 'attribute vec2 a;varying vec2 vUv;void main(){vUv=a*.5+.5;gl_Position=vec4(a,0.,1.);}';

  const HEAD = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 vUv;
`;

  // hashes without sin() (stable across GPUs), value noise and fbm
  const NOISE = `
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float hash13(vec3 p3){ p3 = fract(p3 * .1031); p3 += dot(p3, p3.zyx + 31.32); return fract((p3.x + p3.y) * p3.z); }
vec3 hash33(vec3 p3){ p3 = fract(p3 * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yxz + 33.33); return fract((p3.xxy + p3.yxx) * p3.zyx); }
float n3(vec3 p){
  vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(mix(hash13(i), hash13(i + vec3(1,0,0)), f.x), mix(hash13(i + vec3(0,1,0)), hash13(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash13(i + vec3(0,0,1)), hash13(i + vec3(1,0,1)), f.x), mix(hash13(i + vec3(0,1,1)), hash13(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm3(vec3 p){ float v = 0., a = .5; for (int i = 0; i < 5; i++) { v += a * n3(p); p = p * 2.02 + vec3(1.7, 9.2, 3.1); a *= .5; } return v; }
float fbm3l(vec3 p){ float v = 0., a = .5; for (int i = 0; i < 3; i++) { v += a * n3(p); p = p * 2.03 + vec3(4.1, 1.3, 7.7); a *= .5; } return v / .875; }
vec3 lin(vec3 c){ return pow(c, vec3(2.2)); }
`;

  // ---------------------------------------------------------------- nebula
  // Tileable: every octave's lattice wraps, so the texture repeats seamlessly.
  const NEB = `
uniform vec3 uC1, uC2, uC3;
uniform vec2 uSeed;
uniform float uGain;
float n2p(vec2 p, float per){
  vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3. - 2. * f);
  float a = hash12(mod(i, per) + uSeed), b = hash12(mod(i + vec2(1., 0.), per) + uSeed);
  float c = hash12(mod(i + vec2(0., 1.), per) + uSeed), d = hash12(mod(i + vec2(1., 1.), per) + uSeed);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbmp(vec2 p, float per){ float v = 0., a = .5; for (int i = 0; i < 6; i++) { v += a * n2p(p, per); p *= 2.; per *= 2.; a *= .5; } return v; }
void main(){
  float per = 3.;
  vec2 p = vUv * per;
  vec2 q = vec2(fbmp(p, per), fbmp(p + vec2(5.2, 1.3), per));
  vec2 r = vec2(fbmp(p + 3. * q + vec2(1.7, 9.2), per), fbmp(p + 3. * q + vec2(8.3, 2.8), per));
  float f = fbmp(p + 2.5 * r, per);
  float gas = smoothstep(0.4, 0.92, f); gas *= gas;
  vec3 col = mix(uC1, uC2, clamp((q.x - 0.3) * 2.2, 0., 1.));
  col = mix(col, uC3, clamp((r.y - 0.38) * 2.6, 0., 1.) * 0.85);
  float fil = pow(1. - abs(2. * fbmp(p * 2. + 3. * r + vec2(11., 4.), per * 2.) - 1.), 7.);
  vec3 E = col * gas * 1.3;
  E += mix(col, vec3(1.), 0.3) * fil * smoothstep(0.25, 0.7, f) * 0.55;
  E += vec3(1., .93, .86) * pow(gas, 4.) * 0.35;
  E += col * smoothstep(0.2, 0.8, f) * 0.045;
  float dust = smoothstep(0.5, 0.76, fbmp(p * 2. + 2. * q + vec2(21., 7.), per * 2.));
  dust *= smoothstep(0.22, 0.6, f);
  E *= 1. - dust * 0.9;
  E *= uGain;
  float al = clamp(max(dust * 0.88, max(E.r, max(E.g, E.b))), 0., 1.);
  E = min(E, vec3(al));
  gl_FragColor = vec4(E, al);
}`;

  // ---------------------------------------------------------------- planets
  const PLANET = `
uniform float uSize, uR, uType, uBands, uAtmK, uTilt, uB, uSpin, uRing, uRin, uRout;
uniform vec3 uC1, uC2, uC3, uAtm, uRingC, uSeed, uL;
mat3 rotX(float a){ float c = cos(a), s = sin(a); return mat3(1., 0., 0., 0., c, s, 0., -s, c); }
mat3 rotY(float a){ float c = cos(a), s = sin(a); return mat3(c, 0., -s, 0., 1., 0., s, 0., c); }
mat3 rotZ(float a){ float c = cos(a), s = sin(a); return mat3(c, s, 0., -s, c, 0., 0., 0., 1.); }
float ringDens(float rr){
  float t = (rr - uRin) / (uRout - uRin);
  if (t < 0. || t > 1.) return 0.;
  float d = 0.45 + 0.25 * sin(rr * 47. + uSeed.x) + 0.45 * n3(vec3(rr * 38., uSeed.y, 0.));
  d *= smoothstep(0., 0.06, t) * smoothstep(1., 0.85, t);
  d *= 1. - 0.94 * smoothstep(0.035, 0.0, abs(t - 0.63));
  d *= 1. - 0.5 * smoothstep(0.02, 0.0, abs(t - 0.27));
  return clamp(d, 0., 1.);
}
void craters(vec3 P, inout vec3 nObj, inout float alb, float amount){
  for (int k = 0; k < 22; k++) {
    float fk = float(k);
    vec3 c = normalize(hash33(uSeed + fk * 1.618) - 0.5);
    float rad = mix(0.035, 0.21, pow(hash13(uSeed.yzx + fk * 2.71), 2.5));
    vec3 dv = P - c;
    float dd = length(dv) / rad;
    if (dd < 1.35) {
      vec3 tng = normalize(dv - dot(dv, P) * P + 1e-5);
      if (dd < 1.) { nObj -= tng * dd * 0.6 * amount; alb *= mix(0.72, 1., dd * dd); }
      else { float rim = smoothstep(1.35, 1., dd); nObj += tng * rim * 0.4 * amount; alb *= 1. + rim * 0.14 * amount; }
    }
  }
  nObj = normalize(nObj);
}
void main(){
  vec2 px = (gl_FragCoord.xy - vec2(uSize * 0.5)) / uR;
  vec3 L = normalize(uL);
  float d2 = dot(px, px), d = sqrt(d2);
  vec3 pole = rotZ(uTilt) * vec3(0., cos(uB), sin(uB));
  vec3 pc = vec3(0.); float cov = 0.; float zs = -1e3;
  if (d2 < 1.) {
    zs = sqrt(1. - d2);
    cov = clamp((1. - d) * uR * 1.2, 0., 1.);
    vec3 N = vec3(px, zs);
    mat3 M = rotY(uSpin) * rotX(-uB) * rotZ(-uTilt);
    mat3 Mi = rotZ(uTilt) * rotX(uB) * rotY(-uSpin);
    vec3 P = M * N;
    vec3 nObj = P; float alb = 1., spec = 0., clouds = 0., emisDay = 0.15;
    vec3 emis = vec3(0.), col = vec3(0.5);
    if (uType < 0.5) {                                   // gas giant
      float w = fbm3(P * vec3(2., 5., 2.) + uSeed);
      float lat = P.y + (w - 0.5) * 0.16;
      float bands = sin(lat * uBands * 3.14159 + (fbm3(P * vec3(1.5, 10., 1.5) + uSeed * 1.3) - 0.5) * 4.);
      float fine = fbm3(P * vec3(5., 30., 5.) + uSeed * 0.7);
      col = mix(lin(uC1), lin(uC2), 0.5 + 0.5 * bands);
      col = mix(col, lin(uC3), smoothstep(0.55, 0.8, fine) * 0.45);
      col *= 0.82 + 0.36 * fine;
      vec3 dv = P - normalize(vec3(0.5, -0.28, 0.82)); dv.y *= 2.4;
      float sd = length(dv);
      col = mix(col, lin(uC3) * 1.1, smoothstep(0.22, 0.07, sd) * 0.8);
      col = mix(col, lin(uC2) * 0.8, smoothstep(0.07, 0.02, sd) * 0.5);
      col *= 1. - smoothstep(0.75, 1., abs(P.y)) * 0.35;
    } else if (uType < 1.5) {                            // terran / ocean
      float h = fbm3(P * 1.8 + uSeed) + (fbm3(P * 7. + uSeed * 2.) - 0.5) * 0.14;
      float sea = 0.5;
      float land = smoothstep(sea, sea + 0.015, h);
      vec3 ocean = mix(lin(vec3(0.01, 0.04, 0.14)), lin(vec3(0.05, 0.22, 0.42)), smoothstep(sea - 0.18, sea, h));
      vec3 ground = mix(lin(uC1), lin(uC2), smoothstep(sea + 0.02, sea + 0.2, h));
      ground = mix(ground, lin(vec3(0.6, 0.58, 0.55)), smoothstep(sea + 0.22, sea + 0.32, h));
      float dry = smoothstep(0.38, 0.05, abs(P.y)) * smoothstep(0.48, 0.66, fbm3(P * 3. + uSeed * 3.));
      ground = mix(ground, lin(vec3(0.74, 0.6, 0.4)), dry * 0.75);
      col = mix(ocean, ground, land);
      float ice = smoothstep(0.8, 0.88, abs(P.y) + (h - 0.5) * 0.4);
      col = mix(col, lin(vec3(0.92, 0.95, 1.)), ice);
      spec = (1. - land) * (1. - ice);
      float cl = fbm3(P * 2.4 + vec3(fbm3(P * 1.2 + uSeed * 5.)) * 2. + uSeed * 4.);
      clouds = smoothstep(0.5, 0.72, cl) * 0.95;
      emis = lin(vec3(1., 0.72, 0.38)) * land * (1. - ice) * step(0.9, hash13(floor(P * 150.))) * smoothstep(0.45, 0.6, fbm3(P * 6. + uSeed)) * 1.6;
      nObj = normalize(P + (vec3(n3(P * 14. + 1.), n3(P * 14. + 2.), n3(P * 14. + 3.)) - 0.5) * 0.22 * land);
    } else if (uType < 2.5) {                            // rocky moon
      float h = fbm3(P * 2.4 + uSeed);
      col = mix(lin(uC1), lin(uC2), smoothstep(0.35, 0.7, h));
      col *= 0.7 + 0.55 * fbm3(P * 10. + uSeed);
      craters(P, nObj, alb, 1.);
    } else if (uType < 3.5) {                            // ice world
      float h = fbm3(P * 2. + uSeed);
      col = mix(lin(vec3(0.8, 0.88, 0.96)), lin(uC1), smoothstep(0.3, 0.8, h));
      float cr = pow(1. - abs(2. * fbm3(P * 4.5 + uSeed * 2.) - 1.), 24.);
      col = mix(col, lin(uC2), cr * 0.45);
      spec = 0.25;
      craters(P, nObj, alb, 0.4);
    } else if (uType < 4.5) {                            // desert
      float h = fbm3(P * 2.2 + uSeed);
      float dune = 0.5 + 0.5 * sin(P.y * 18. + h * 9.);
      col = mix(lin(uC1), lin(uC2), smoothstep(0.3, 0.75, h));
      col *= 0.86 + 0.18 * dune;
      col = mix(col, lin(vec3(0.95, 0.93, 0.9)), smoothstep(0.86, 0.93, abs(P.y) + (h - 0.5) * 0.2));
      craters(P, nObj, alb, 0.6);
    } else if (uType < 5.5) {                            // lava
      float h = fbm3(P * 2.6 + uSeed);
      float cr = pow(1. - abs(2. * fbm3(P * 3.5 + uSeed * 3.) - 1.), 9.);
      col = lin(vec3(0.09, 0.07, 0.07)) * (0.6 + 0.9 * h);
      emis = lin(vec3(1., 0.32, 0.05)) * cr * 2.2 * (0.4 + h) + lin(vec3(1., 0.75, 0.3)) * pow(cr, 28.) * 3.;
      emisDay = 0.6;
      craters(P, nObj, alb, 0.5);
    } else {                                             // chrome: a mirror reflecting a silver sky
      vec3 Rv = vec3(2. * N.z * N.x, 2. * N.z * N.y, 2. * N.z * N.z - 1.);
      float h = Rv.y + (fbm3(P * 2.2 + uSeed) - 0.5) * 0.35;
      vec3 sky = mix(lin(uC2), lin(uC1), smoothstep(-0.05, 0.85, h));
      vec3 ground = lin(uC3) * (0.55 + 0.45 * smoothstep(-1., -0.05, h));
      col = h > 0. ? sky : ground;
      col += vec3(1.) * smoothstep(0.05, 0., abs(h)) * 0.7;
      col = mix(col, lin(uC1), pow(1. - N.z, 3.) * 0.5);
    }
    vec3 nV = normalize(Mi * nObj);
    float ndl = dot(nV, L), ndlS = dot(N, L);
    float diff = max(ndl, 0.) * smoothstep(-0.15, 0.1, ndlS);
    float twilight = smoothstep(-0.2, 0.1, ndlS) * (1. - smoothstep(0.1, 0.5, ndlS)) * uAtmK;
    float ringSh = 1.;
    if (uRing > 0.5) { float tt = -dot(N, pole) / dot(L, pole); if (tt > 0.) ringSh = 1. - ringDens(length(N + L * tt)) * 0.8; }
    vec3 lit = col * alb * (diff * 1.35 * ringSh + 0.01);
    lit += col * twilight * lin(uAtm) * 0.3;
    if (clouds > 0.) {
      vec3 cc = vec3(0.95) * (max(ndlS, 0.) * 1.35 * ringSh + 0.01);
      lit = mix(lit, cc, clouds); spec *= 1. - clouds; emis *= 1. - clouds;
    }
    vec3 H = normalize(L + vec3(0., 0., 1.));
    lit += vec3(1., 0.95, 0.85) * pow(max(dot(N, H), 0.), 70.) * spec * 0.9 * step(0., ndlS);
    if (uType > 5.5) lit = col * (0.5 + 0.6 * max(ndlS, 0.)) + vec3(1.) * pow(max(dot(N, H), 0.), 120.) * 1.6;
    lit += emis * mix(1., emisDay, smoothstep(-0.2, 0.25, ndlS));
    float rim = pow(1. - zs, 2.5);
    lit += lin(uAtm) * rim * uAtmK * clamp(ndlS + 0.35, 0., 1.) * 1.4;
    pc = lit;
  }
  // atmosphere halo just outside the limb
  vec3 hc = vec3(0.); float ha = 0.;
  if (d > 0.97 && uAtmK > 0.) {
    float h = exp(-max(d - 1., 0.) * 28.);
    float side = clamp(dot(normalize(vec3(px, 0.)), L) * 0.8 + 0.3, 0., 1.);
    hc = lin(uAtm) * h * uAtmK * side * 0.9;
    ha = clamp(max(hc.r, max(hc.g, hc.b)), 0., 1.);
  }
  vec3 colOut = pc * cov + hc * (1. - cov);
  float aOut = cov + ha * (1. - cov);
  if (uRing > 0.5) {
    float zr = -(px.x * pole.x + px.y * pole.y) / pole.z;
    vec3 Rp = vec3(px, zr);
    float rr = length(Rp);
    float dens = ringDens(rr);
    if (dens > 0.001 && (d2 >= 1. || zr > zs)) {
      float tpl = dot(Rp, L);
      float perp = length(Rp - L * tpl);
      float sh = tpl < 0. ? smoothstep(0.96, 1.04, perp) * 0.92 + 0.08 : 1.;
      float bright = 0.3 + 0.7 * abs(dot(pole, L));
      vec3 rc = lin(uRingC) * (0.7 + 0.6 * n3(vec3(rr * 26., uSeed.x, 3.))) * bright * sh * 1.2;
      float ra = dens * 0.92;
      colOut = rc * ra + colOut * (1. - ra);
      aOut = ra + aOut * (1. - ra);
    }
  }
  vec3 c = aOut > 0.0001 ? colOut / aOut : vec3(0.);
  c = c / (1. + c * 0.12);
  c = pow(c, vec3(1. / 2.2));
  gl_FragColor = vec4(c * aOut, aOut);
}`;

  // ---------------------------------------------------------------- asteroids
  // Each tile of the sheet is one frame of a ray-marched lumpy rock tumbling around uAxis.
  const ROCK = `
uniform vec2 uGrid;
uniform float uTile;
uniform vec3 uSeed, uAxis, uStretch, uTint, uL;
mat3 axisRot(vec3 a, float t){
  a = normalize(a); float c = cos(t), s = sin(t), o = 1. - c;
  return mat3(c + a.x * a.x * o, a.y * a.x * o + a.z * s, a.z * a.x * o - a.y * s,
              a.x * a.y * o - a.z * s, c + a.y * a.y * o, a.z * a.y * o + a.x * s,
              a.x * a.z * o + a.y * s, a.y * a.z * o - a.x * s, c + a.z * a.z * o);
}
mat3 Ri;
float sdf(vec3 pw){
  vec3 q = (Ri * pw) / uStretch;
  float d = length(q) - 0.55;
  d += (fbm3l(q * 1.3 + uSeed) - 0.5) * 0.55;
  d += (n3(q * 4.3 + uSeed.yzx) - 0.5) * 0.08;
  for (int k = 0; k < 5; k++) {
    float fk = float(k);
    vec3 c = normalize(hash33(uSeed + fk * 7.13) - 0.5) * 0.64;
    float rad = 0.06 + 0.11 * hash13(uSeed.zxy + fk * 3.1);
    d = max(d, -(length(q - c) - rad));
  }
  return d * 0.5;
}
void main(){
  vec2 cell = floor(gl_FragCoord.xy / uTile);
  vec2 lp = (gl_FragCoord.xy - cell * uTile) / uTile * 2. - 1.;
  float row = uGrid.y - 1. - cell.y;
  float frame = cell.x + row * uGrid.x;
  float ang = frame / (uGrid.x * uGrid.y) * 6.2831853;
  Ri = axisRot(uAxis, -ang);
  float r2 = dot(lp, lp);
  if (r2 > 0.95) { gl_FragColor = vec4(0.); return; }
  float z0 = sqrt(0.95 - r2);
  float z = z0, minD = 1e3, zMin = z0;
  bool hit = false;
  for (int i = 0; i < 60; i++) {
    float dd = sdf(vec3(lp, z));
    if (dd < minD) { minD = dd; zMin = z; }
    if (dd < 0.0015) { hit = true; break; }
    z -= max(dd, 0.004);
    if (z < -z0) break;
  }
  float alpha = hit ? 1. : smoothstep(0.012, 0.0, minD);
  if (alpha <= 0.) { gl_FragColor = vec4(0.); return; }
  vec3 p = vec3(lp, hit ? z : zMin);
  vec2 e = vec2(0.004, 0.);
  vec3 n = normalize(vec3(sdf(p + e.xyy) - sdf(p - e.xyy), sdf(p + e.yxy) - sdf(p - e.yxy), sdf(p + e.yyx) - sdf(p - e.yyx)));
  vec3 q = Ri * p;
  vec3 L = normalize(uL);
  vec3 alb = lin(uTint) * (0.55 + 0.6 * fbm3l(q * 3.2 + uSeed * 2.));
  alb *= 0.8 + 0.3 * n3(q * 16.);
  float ao = clamp(0.3 + sdf(p + n * 0.08) / (0.08 * 0.5) * 0.7, 0., 1.);
  float ndl = dot(n, L);
  vec3 col = alb * (max(ndl, 0.) * 2.1 * mix(0.5, 1., ao) + 0.015 * ao);
  col += alb * 0.05 * max(-ndl, 0.) * ao;
  col = col / (1. + col * 0.2);
  col = pow(col, vec3(1. / 2.2));
  gl_FragColor = vec4(col * alpha, alpha);
}`;

  // ---------------------------------------------------------------- wormhole lens
  const LENS = `
uniform sampler2D uTex;
uniform float uT, uRt;
uniform vec3 uA, uB, uAcc;
void main(){
  vec2 p = vUv * 2. - 1.;
  float d = length(p);
  vec3 col; float alpha;
  if (d > uRt) {
    float fall = 1. - smoothstep(0.5, 1., d);
    float beta = d - uRt * uRt * 1.15 / d * fall;
    float sw = 0.9 * uRt * uRt / (d * d) * fall;
    vec2 dir = p / d;
    float cs = cos(sw), sn = sin(sw);
    dir = vec2(dir.x * cs - dir.y * sn, dir.x * sn + dir.y * cs);
    col = texture2D(uTex, dir * beta * 0.5 + 0.5).rgb;
    float ring = exp(-pow((d - uRt) / 0.018, 2.));
    col += (uAcc * 0.7 + vec3(0.35)) * ring;
    col += uAcc * 0.2 * exp(-(d - uRt) * 10.) * fall;
    alpha = 1. - smoothstep(0.86, 1., d);
  } else {
    vec2 q = p / uRt;
    float z = sqrt(max(0., 1. - dot(q, q)));
    vec2 s = q / (z + 0.3) * 1.3;
    float a = uT * 0.12;
    s = vec2(s.x * cos(a) - s.y * sin(a), s.x * sin(a) + s.y * cos(a));
    float n = fbm3(vec3(s * 1.4, uT * 0.03 + 4.));
    float n2 = fbm3(vec3(s * 3. + n * 2., 9.));
    col = mix(uA, uB, smoothstep(0.3, 0.7, n2)) * smoothstep(0.35, 0.85, n) * 2.4;
    vec2 g = s * 30.; float h = hash12(floor(g));
    col += vec3(1.) * smoothstep(0.22, 0., length(fract(g) - 0.5)) * step(0.93, h) * (h - 0.93) * 14.;
    col *= 0.25 + 0.75 * z;
    col += uAcc * pow(1. - z, 4.) * 0.9;
    alpha = 1.;
  }
  gl_FragColor = vec4(col * alpha, alpha);
}`;

  function makeGL() {
    const c = document.createElement('canvas');
    c.width = c.height = 4;
    let gl = null;
    try {
      gl = c.getContext('webgl', { alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: true, antialias: false, depth: false, stencil: false });
    } catch (e) { gl = null; }
    if (!gl) return null;
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    c.addEventListener('webglcontextlost', e => e.preventDefault());
    function shader(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) || 'shader compile failed');
      return s;
    }
    function program(fs) {
      const p = gl.createProgram();
      gl.attachShader(p, shader(gl.VERTEX_SHADER, VS));
      gl.attachShader(p, shader(gl.FRAGMENT_SHADER, HEAD + NOISE + fs));
      gl.bindAttribLocation(p, 0, 'a');
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p) || 'link failed');
      const locs = {};
      return { p, loc: n => (n in locs ? locs[n] : (locs[n] = gl.getUniformLocation(p, n))) };
    }
    function run(P, w, h, u) {
      if (gl.isContextLost()) return false;
      if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
      gl.viewport(0, 0, w, h);
      gl.useProgram(P.p);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.enableVertexAttribArray(0);
      gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      for (const k in u) {
        const l = P.loc(k), v = u[k];
        if (l === null) continue;
        if (typeof v === 'number') { if (k.indexOf('uTex') === 0) gl.uniform1i(l, v); else gl.uniform1f(l, v); }
        else if (v.length === 2) gl.uniform2fv(l, v);
        else if (v.length === 3) gl.uniform3fv(l, v);
        else gl.uniform4fv(l, v);
      }
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      return !gl.isContextLost();
    }
    function snapshot(w, h) {
      const o = document.createElement('canvas');
      o.width = w; o.height = h;
      o.getContext('2d').drawImage(c, 0, 0);
      return o;
    }
    return { c, gl, program, run, snapshot };
  }

  const R = Math.random;
  const api = { ok: false, lensOk: false };

  try {
    const G = makeGL();
    if (!G) throw new Error('WebGL unavailable');
    const P = { neb: G.program(NEB), planet: G.program(PLANET), rock: G.program(ROCK) };

    api.nebula = o => {
      const S = o.size || 1024;
      return G.run(P.neb, S, S, { uC1: o.c1, uC2: o.c2, uC3: o.c3, uSeed: [R() * 400, R() * 400], uGain: o.gain || 1 })
        ? G.snapshot(S, S) : null;
    };

    // o: { r (css px), dpr, type, c1, c2, c3, atm, atmK, bands, tilt, b, ring, rin, rout, ringC, light }
    api.planet = o => {
      const half = o.r * Math.max(1.2, o.ring ? o.rout + 0.04 : 0) + 3;
      const S = Math.ceil(half * 2 * o.dpr);
      const ok = G.run(P.planet, S, S, {
        uSize: S, uR: o.r * o.dpr, uType: o.type, uBands: o.bands || 7, uAtmK: o.atmK, uTilt: o.tilt, uB: o.b,
        uSpin: R() * 6.28, uRing: o.ring ? 1 : 0, uRin: o.rin || 1.3, uRout: o.rout || 2,
        uC1: o.c1, uC2: o.c2, uC3: o.c3, uAtm: o.atm, uRingC: o.ringC || [0.8, 0.75, 0.65],
        uSeed: [R() * 50, R() * 50, R() * 50], uL: o.light,
      });
      return ok ? { canvas: G.snapshot(S, S), half } : null;
    };

    // o: { tile, cols, rows, tint, light }
    api.rockSheet = o => {
      const w = o.cols * o.tile, h = o.rows * o.tile;
      const ax = [R() - 0.5, R() - 0.5, R() - 0.5];
      const ok = G.run(P.rock, w, h, {
        uGrid: [o.cols, o.rows], uTile: o.tile, uSeed: [R() * 50, R() * 50, R() * 50],
        uAxis: ax, uStretch: [0.85 + R() * 0.55, 0.7 + R() * 0.3, 0.75 + R() * 0.35], uTint: o.tint, uL: o.light,
      });
      return ok ? { canvas: G.snapshot(w, h), tile: o.tile, cols: o.cols, rows: o.rows, frames: o.cols * o.rows } : null;
    };
    api.ok = true;
  } catch (e) {
    console.warn('DRIFT: WebGL graphics disabled -', e.message);
  }

  try {
    const LG = makeGL();
    if (!LG) throw new Error('WebGL unavailable');
    const LP = LG.program(LENS);
    const gl = LG.gl;
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const src = document.createElement('canvas');
    const sctx = src.getContext('2d');
    // Copies a square of `from` (canvas pixels), bends it around the throat and returns the lens canvas.
    api.lens = (from, sx, sy, size, o) => {
      const L = Math.max(64, Math.min(768, Math.round(size)));
      if (src.width !== L) { src.width = src.height = L; }
      sctx.clearRect(0, 0, L, L);
      sctx.drawImage(from, sx, sy, size, size, 0, 0, L, L);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
      gl.activeTexture(gl.TEXTURE0);
      return LG.run(LP, L, L, { uTex: 0, uT: o.t, uRt: o.rt, uA: o.a, uB: o.b, uAcc: o.acc }) ? LG.c : null;
    };
    api.lensOk = true;
  } catch (e) {
    console.warn('DRIFT: wormhole lens disabled -', e.message);
  }

  window.DriftGFX = api;
})();

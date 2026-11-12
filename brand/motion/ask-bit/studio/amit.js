// Stylised 3D avatar of Amit for the studio (built from simple shapes, units = studio mm).
// Styles: 'A' chunky toy (rounded boxes, matches Bit), 'B' round cartoon, 'C' low-poly faceted.
// Traits: thick wavy black hair (volume on top, short faded sides), thick dark brows, dark brown eyes,
// warm brown skin, full dark beard with grey at the chin, navy crew-neck T-shirt with a small pink Bit badge.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
const SKIN = 0xa8734f, HAIR = 0x15110f, BEARD = 0x231b17, GREY = 0x86817b, NAVY = 0x2b3966, EYE = 0x2a1a12;
export function buildAmit(style = 'A') {
  const flat = style === 'C';
  const M = (c, o = {}) => new THREE.MeshStandardMaterial(Object.assign({ color: c, roughness: .7, flatShading: flat }, o));
  const g = new THREE.Group(), head = new THREE.Group(); g.add(head);
  const seg = flat ? 1 : 6, sph = (r) => new THREE.SphereGeometry(r, flat ? 7 : 24, flat ? 5 : 16), ico = (r) => new THREE.IcosahedronGeometry(r, flat ? 0 : 2);
  const add = (geo, mat, x, y, z, p = g) => { const o = new THREE.Mesh(geo, mat); o.position.set(x, y, z); o.castShadow = o.receiveShadow = true; p.add(o); return o; };
  const box = (w, h, d, r) => flat ? new THREE.BoxGeometry(w, h, d) : new RoundedBoxGeometry(w, h, d, seg, r);
  // torso + arms (seated; desk hides the lower half)
  add(box(118, 96, 62, 22), M(NAVY), 0, 78, 0);
  add(box(40, 12, 34, 6), M(NAVY), 0, 128, 0);                                   // shoulders/neck line
  for (const s of [-1, 1]) {
    const arm = add(new THREE.CapsuleGeometry(15, 50, flat ? 2 : 6, flat ? 6 : 14), M(NAVY), s * 64, 84, 8); arm.rotation.z = s * .22; arm.rotation.x = -.35;
    add(sph(11), M(0x8c5d42), s * 70, 50, 34);                                       // hands resting on the desk
  }
  // pink Bit badge on the chest
  const badge = add(box(18, 15, 3, 3), M(0xF0359E, { emissive: 0xF0359E, emissiveIntensity: .25 }), -28, 104, 31.5);
  add(new THREE.BoxGeometry(11, 5, 1), M(0x1e2132), -28, 106, 33.2); add(new THREE.BoxGeometry(2.4, 2.4, 1), M(0x00F0FF, { emissive: 0x00F0FF, emissiveIntensity: 1 }), -30.5, 106, 33.8); add(new THREE.BoxGeometry(2.4, 2.4, 1), M(0x00F0FF, { emissive: 0x00F0FF, emissiveIntensity: 1 }), -25.5, 106, 33.8);
  add(new THREE.CylinderGeometry(13, 15, 16, flat ? 6 : 16), M(SKIN), 0, 136, 0);  // neck
  head.position.set(0, 175, 2);
  // head shape
  const hw = style === 'B' ? 74 : 70, hh = style === 'B' ? 78 : 80;
  if (style === 'B') { const h = add(sph(40), M(SKIN), 0, 0, 0, head); h.scale.set(hw / 80, hh / 80, .95); }
  else add(box(hw, hh, 64, flat ? 0 : 24), M(SKIN), 0, 0, 0, head);
  for (const s of [-1, 1]) { const e = add(sph(9), M(SKIN), s * (hw / 2 + 1), 2, -2, head); e.scale.set(.5, 1, .8); } // ears
  // beard: wraps the jaw, grey at the chin
  const bw = hw + 6;
  const beard = add(box(bw, 32, 62, flat ? 0 : 15), M(BEARD, { roughness: 1 }), 0, -31, 4, head);
  for (const s of [-1, 1]) add(box(8, 30, 40, flat ? 0 : 3), M(BEARD, { roughness: 1 }), s * (bw / 2 - 4), -10, -4, head);   // sideburns
  const chin = add(box(30, 13, 8, flat ? 0 : 4), M(GREY, { roughness: 1 }), 0, -40, 33, head);
  add(box(28, 6, 8, flat ? 0 : 3), M(BEARD, { roughness: 1 }), 0, -16, 34, head);                       // moustache
  // mouth (opens with voice; scale.y is driven from outside)
  const mouth = add(box(16, 5, 4, flat ? 0 : 2), M(0x3a1a18), 0, -23, 35.5, head); mouth.name = 'mouth';
  // nose, eyes, brows
  const nose = add(box(12, 16, 12, flat ? 0 : 4), M(0x8c5d42), 0, -4, 33, head);
  for (const s of [-1, 1]) {
    add(sph(8), M(0xf3ece6, { roughness: .4 }), s * 15, 9, 30, head).scale.set(1, .8, .35);
    add(sph(5.2), M(EYE, { roughness: .15 }), s * 15, 9, 32.2, head).scale.set(1, 1, .4);
    add(sph(1.4), M(0xffffff, { emissive: 0xffffff, emissiveIntensity: .6 }), s * 15 + 1.8, 11, 34.4, head);
    const brow = add(box(20, 5.5, 6, flat ? 0 : 2), M(HAIR), s * 15, 21, 32, head); brow.rotation.z = -s * .08; brow.name = 'brow';
  }
  // hair: short faded sides + a big wavy top made of overlapping blobs
  add(box(hw + 4, 22, 66, flat ? 0 : 10), M(0x241c18, { roughness: 1 }), 0, 30, -3, head);              // faded sides
  const tufts = [[-24, 46, 8, 17], [-6, 50, 12, 18], [12, 49, 10, 18], [28, 44, 6, 15], [-30, 40, -8, 15], [32, 38, -10, 14], [-14, 52, -10, 18], [8, 53, -14, 18], [-2, 46, 22, 14], [20, 45, 20, 13], [-20, 44, 20, 13], [0, 42, -26, 16]];
  const hm = M(HAIR, { roughness: .9 });
  for (const [x, y, z, r] of tufts) { const t = add(style === 'C' ? ico(r) : sph(r), hm, x, y, z, head); t.scale.set(1.1, .8, 1); t.rotation.set(x * .05, z * .07, y * .03); }
  g.userData = { head, mouth };
  return g;
}

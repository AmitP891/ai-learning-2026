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
  add(box(150, 52, 68, 22), M(NAVY), 0, 104, 0);                                // broad chest
  add(box(118, 56, 60, 20), M(NAVY), 0, 62, 0);                                  // narrower waist (V-shape)
  for (const s of [-1, 1]) {
    add(sph(26), M(NAVY), s * 72, 116, 0).scale.set(1, .85, 1);                  // shoulder caps
    const arm = add(new THREE.CapsuleGeometry(20, 44, flat ? 2 : 6, flat ? 6 : 14), M(NAVY), s * 82, 84, 10); arm.rotation.z = s * .2; arm.rotation.x = -.4;
    const fore = add(new THREE.CapsuleGeometry(15, 30, flat ? 2 : 6, flat ? 6 : 14), M(SKIN), s * 84, 56, 34); fore.rotation.x = -1.3;
    const hand = new THREE.Group(); hand.position.set(s * 80, 49, 58); hand.rotation.y = -s * .35; g.add(hand);   // hands resting on the desk
    add(box(26, 11, 24, flat ? 0 : 5), M(SKIN), 0, 0, 0, hand);
    for (let f = 0; f < 4; f++) add(box(5.5, 8, 10, flat ? 0 : 2.5), M(SKIN), -9 + f * 6, -1.5, 15, hand);   // fingers
    add(box(7, 7, 13, flat ? 0 : 3), M(SKIN), -s * 15, 0, 4, hand).rotation.y = s * .6;                   // thumb
  }
  // pink Bit badge on the chest
  const badge = add(box(18, 15, 3, 3), M(0xF0359E, { emissive: 0xF0359E, emissiveIntensity: .25 }), -34, 110, 34.5);
  add(new THREE.BoxGeometry(11, 5, 1), M(0x1e2132), -34, 112, 36.2); add(new THREE.BoxGeometry(2.4, 2.4, 1), M(0x00F0FF, { emissive: 0x00F0FF, emissiveIntensity: 1 }), -36.5, 112, 36.8); add(new THREE.BoxGeometry(2.4, 2.4, 1), M(0x00F0FF, { emissive: 0x00F0FF, emissiveIntensity: 1 }), -31.5, 112, 36.8);
  add(new THREE.CylinderGeometry(19, 22, 18, flat ? 6 : 16), M(SKIN), 0, 136, 0);  // thicker neck
  head.position.set(0, 180, 2);
  // head shape
  const hw = style === 'B' ? 74 : 70, hh = style === 'B' ? 78 : 80;
  if (style === 'B') { const h = add(sph(40), M(SKIN), 0, 0, 0, head); h.scale.set(hw / 80, hh / 80, .95); }
  else add(box(hw, hh, 64, flat ? 0 : 24), M(SKIN), 0, 0, 0, head);
  for (const s of [-1, 1]) { const e = add(sph(9), M(SKIN), s * (hw / 2 + 1), 2, -2, head); e.scale.set(.5, 1, .8); } // ears
  // beard: crisp, defined shape. Straight cheek line, tapered jaw, clean neckline, grey at the chin
  const bm = M(BEARD, { roughness: 1 });
  const bshape = new THREE.Shape(); const W2 = hw / 2 + 3;
  bshape.moveTo(-W2, 2); bshape.lineTo(-W2 + 4, -20); bshape.lineTo(-W2 + 14, -40); bshape.quadraticCurveTo(-12, -54, 0, -55); bshape.quadraticCurveTo(12, -54, W2 - 14, -40); bshape.lineTo(W2 - 4, -20); bshape.lineTo(W2, 2);
  bshape.lineTo(W2 - 8, 2); bshape.lineTo(17, -17); bshape.quadraticCurveTo(0, -13, -17, -17); bshape.lineTo(-W2 + 8, 2); bshape.closePath();   // cheek lines cut up to the sideburns
  const beard = add(new THREE.ExtrudeGeometry(bshape, { depth: 10, bevelEnabled: !flat, bevelThickness: 2, bevelSize: 1.5, bevelSegments: 2 }), bm, 0, 0, 25, head);
  add(box(hw + 4, 30, 50, flat ? 0 : 10), bm, 0, -32, 2, head);                    // jaw volume behind the front shape
  const cs = new THREE.Shape(); cs.moveTo(-14, -38); cs.quadraticCurveTo(0, -35, 14, -38); cs.lineTo(11, -48); cs.quadraticCurveTo(0, -55, -11, -48); cs.closePath();
  const chin = add(new THREE.ExtrudeGeometry(cs, { depth: 1, bevelEnabled: !flat, bevelThickness: 1, bevelSize: 1, bevelSegments: 2 }), M(GREY, { roughness: 1 }), 0, 0, 36.2, head);
  add(box(30, 4.5, 4, flat ? 0 : 2), bm, 0, -17, 36, head);                        // moustache
  // mouth (opens with voice; scale.y is driven from outside)
  const mouth = add(box(15, 4, 2, flat ? 0 : 1.5), M(0x3a1a18), 0, -23, 37.2, head); mouth.name = 'mouth';
  // nose, eyes, brows
  const nose = add(box(12, 16, 12, flat ? 0 : 4), M(0x8c5d42), 0, -4, 33, head);
  for (const s of [-1, 1]) {
    add(sph(8), M(0xf3ece6, { roughness: .4 }), s * 15, 9, 30, head).scale.set(1, .8, .35);
    add(sph(5.2), M(EYE, { roughness: .15 }), s * 15, 9, 32.2, head).scale.set(1, 1, .4);
    add(sph(1.4), M(0xffffff, { emissive: 0xffffff, emissiveIntensity: .6 }), s * 15 + 1.8, 11, 34.4, head);
    const brow = add(box(19, 3.2, 4, flat ? 0 : 1.2), M(HAIR), s * 15, 20, 32.5, head); brow.rotation.z = -s * .08; brow.name = 'brow';
  }
  // hair: short faded sides, a few curls peeking out under the beanie
  add(box(hw + 4, 18, 64, flat ? 0 : 8), M(0x241c18, { roughness: 1 }), 0, 28, -3, head);
  const hm = M(HAIR, { roughness: .9 });
  for (const [x, y, z, r] of [[-26, 34, 26, 8], [-14, 36, 30, 7], [24, 34, 26, 7], [-32, 30, 14, 7], [32, 30, 12, 7]]) add(style === 'C' ? ico(r) : sph(r), hm, x, y, z, head);
  // beanie: charcoal knit with a folded cuff and a small pink tag
  const knit = M(0x4a4e5c, { roughness: 1 }), cuffM = M(0x565a69, { roughness: 1 });
  const crown = add(sph(41), knit, 0, 42, -2, head); crown.scale.set((hw + 10) / 82, .78, 1.0);
  const cuff = add(new THREE.CylinderGeometry(hw / 2 + 6, hw / 2 + 6, 16, flat ? 8 : 32), cuffM, 0, 40, -2, head); cuff.scale.z = 66 / (hw + 12);
  if (!flat) for (let i = 0; i < 18; i++) { const a = i / 18 * Math.PI * 2; const r = add(new THREE.BoxGeometry(2, 15, 2), M(0x4f5361, { roughness: 1 }), Math.cos(a) * (hw / 2 + 6.5), 40, Math.sin(a) * (hw / 2 + 6.5) * 66 / (hw + 12) - 2, head); }
  add(new THREE.BoxGeometry(12, 8, 2), M(0xF0359E, { emissive: 0xF0359E, emissiveIntensity: .25 }), 22, 40, 34 , head);
  g.userData = { head, mouth };
  return g;
}

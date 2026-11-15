// Bit's eye expressions, drawn on a patch over the printed eyes (svg units, same mapping as the mouth patch).
// Expressions: normal (patch hidden), happy, shocked, smug, sleepy, love, blink
export const EYE_BOX = { x0: 200, x1: 400, y0: 150, y1: 240 };
const S = 4;
export function drawEyes(g, expr, emissive) {
  const E = EYE_BOX, cw = (E.x1 - E.x0) * S, ch = (E.y1 - E.y0) * S;
  g.clearRect(0, 0, cw, ch); g.fillStyle = emissive ? '#000' : '#1e2132'; g.fillRect(0, 0, cw, ch);
  const col = emissive ? '#00F0FF' : '#5fe9f0'; g.strokeStyle = g.fillStyle = col; g.lineCap = g.lineJoin = 'round'; g.lineWidth = 11 * S;
  const ey = (199 - E.y0) * S;
  for (const x of [244, 356].map(v => (v - E.x0) * S)) {
    g.beginPath(); g.strokeStyle = g.fillStyle = col; g.lineWidth = 11 * S;
    if (expr === 'happy') { g.moveTo(x - 20 * S, ey + 10 * S); g.quadraticCurveTo(x, ey - 26 * S, x + 20 * S, ey + 10 * S); g.stroke(); }
    else if (expr === 'shocked') { g.lineWidth = 9 * S; g.arc(x, ey, 25 * S, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(x, ey, 9 * S, 0, Math.PI * 2); g.fill(); }
    else if (expr === 'smug') { g.roundRect(x - 22 * S, ey - 2 * S, 44 * S, 20 * S, 9 * S); g.fill(); g.lineWidth = 7 * S; g.beginPath(); g.moveTo(x - 24 * S, ey - 14 * S); g.lineTo(x + 24 * S, ey - 6 * S); g.stroke(); }
    else if (expr === 'sleepy') { g.moveTo(x - 20 * S, ey + 4 * S); g.quadraticCurveTo(x, ey + 22 * S, x + 20 * S, ey + 4 * S); g.stroke(); }
    else if (expr === 'blink') { g.moveTo(x - 20 * S, ey + 4 * S); g.lineTo(x + 20 * S, ey + 4 * S); g.stroke(); }
    else if (expr === 'love') { const s = 1.05 * S; g.moveTo(x, ey + 22 * s); g.bezierCurveTo(x - 34 * s, ey - 2 * s, x - 18 * s, ey - 28 * s, x, ey - 10 * s); g.bezierCurveTo(x + 18 * s, ey - 28 * s, x + 34 * s, ey - 2 * s, x, ey + 22 * s); g.fillStyle = emissive ? '#FF4FB8' : '#ff7fc8'; g.fill(); }
  }
  if (expr === 'sleepy') { g.fillStyle = col; g.font = `bold ${26 * S}px sans-serif`; g.fillText('z', cw - 34 * S, 30 * S); g.font = `bold ${18 * S}px sans-serif`; g.fillText('z', cw - 18 * S, 14 * S); }
}
export const EYE_TEX_SIZE = [(EYE_BOX.x1 - EYE_BOX.x0) * S, (EYE_BOX.y1 - EYE_BOX.y0) * S];

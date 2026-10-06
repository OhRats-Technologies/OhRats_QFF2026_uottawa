// Preserve the heatmap; choose legible text over its composited cell colour.
export function matrixCellStyle(value, base) {
  const alpha = Math.max(0.04, Math.min(0.85, value * 0.8));
  const luminance = [152, 210, 174]
    .map((channel, i) => (channel * alpha + base[i] * (1 - alpha)) / 255)
    .map(channel => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
    .reduce((total, channel, i) => total + channel * [0.2126, 0.7152, 0.0722][i], 0);
  const ink = (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) ? '#000' : '#fff';
  return `background:rgba(152,210,174,${alpha});color:${ink}`;
}

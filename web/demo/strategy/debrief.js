// Describe realized fictional impacts; these are not counterfactual response gains.
export function seasonBreakdown(state) {
  const fires = state.incidents.map(fire => ({
    id: fire.id, name: fire.name,
    impact: fire.history.reduce((total, row) => total + row.damage, 0),
  }));
  const total = fires.reduce((sum, fire) => sum + fire.impact, 0);
  const peak = state.history.reduce((highest, row) =>
    !highest || row.damage > highest.damage ? row : highest, null);
  return {
    total,
    top: fires.filter(fire => fire.impact > 0)
      .sort((a, b) => b.impact - a.impact || a.id - b.id).slice(0, 3)
      .map(fire => ({ ...fire, share: fire.impact / total })),
    peak: peak ? { front: peak.turn + 1, impact: peak.damage,
      weather: state.weather[peak.turn].name } : null,
  };
}

export function impactReport(summary) {
  if (!summary.total) return '<small>No pressure impact was recorded.</small>';
  const rows = summary.top.map(fire => `<div class="impact-row" data-impact-fire="${fire.id}">
    <span>${fire.name}</span><span>${fire.impact.toFixed(1)} · ${(fire.share * 100).toFixed(0)}%</span>
    <i aria-hidden="true"><b style="width:${fire.share * 100}%"></b></i>
  </div>`).join('');
  return `<small id="impact-heading" title="Cumulative simulated damage before reserve is floored at zero.">Largest pressure impact · share of total</small>${rows}`;
}

// Keep an early loss on the same twelve-front axis as a completed season.
export function reserveChart(state) {
  const x = (front) => 34 + (front / 12) * 448;
  const y = (reserve) => 12 + ((100 - reserve) / 100) * 76;
  const values = [100, ...state.history.map((row) => row.integrity)];
  const path = values
    .map((value, front) => `${x(front)},${y(value)}`)
    .join(" ");
  const endX = x(state.turn);
  const endY = y(state.integrity);
  const reserve = Math.round(state.integrity);
  const ticks = [0, 4, 8, 12]
    .map(
      (front) =>
        `<text x="${x(front)}" y="108" text-anchor="middle">${front}</text>`,
    )
    .join("");
  return `<svg viewBox="0 0 500 130" role="img" aria-label="Reserve starts at 100 and ends at ${reserve} after ${state.turn} of 12 fronts. Loss limit: 40. Fictional game units.">
    <g fill="#8caaa5" font-size="11">
      <text x="0" y="16">100</text><text x="0" y="${y(40) + 4}">40</text>
      ${ticks}<text x="258" y="126" text-anchor="middle">Weather front</text>
    </g>
    <line x1="34" y1="${y(40)}" x2="482" y2="${y(40)}" stroke="#b87e5b" stroke-dasharray="4 5"/>
    <text x="482" y="${y(40) - 6}" text-anchor="end" fill="#b87e5b" font-size="10">Loss limit</text>
    <line x1="${endX}" y1="12" x2="${endX}" y2="90" stroke="#8caaa5" opacity=".2"/>
    <polyline points="${path}" fill="none" stroke="#a9d2ac" stroke-width="2"/>
    <circle data-season-end="${state.turn}" cx="${endX}" cy="${endY}" r="3" fill="#e9ede4"/>
    <text x="${endX - 7}" y="${endY - 8}" text-anchor="end" fill="#e9ede4" font-size="12">${reserve}</text>
  </svg>`;
}

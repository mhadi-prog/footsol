export default function BreakdownBars({ breakdown }) {
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
  const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v)), 0.01);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontFamily: 'var(--font-mono)', fontSize: 12 }}>
      {entries.map(([type, value]) => (
        <div key={type} style={{ display: 'grid', gridTemplateColumns: '110px 1fr 48px', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--text-muted)' }}>{type}</span>
          <div style={{ height: 6, background: 'var(--surface)', borderRadius: 3, overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: `${(Math.abs(value) / maxAbs) * 100}%`,
                marginLeft: value < 0 ? 'auto' : 0,
                background: value < 0 ? 'var(--negative)' : 'var(--amber)',
              }}
            />
          </div>
          <span style={{ textAlign: 'right', color: value < 0 ? 'var(--negative)' : 'var(--amber)' }}>
            {value > 0 ? '+' : ''}{value.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

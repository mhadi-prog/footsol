export default function RatingBadge({ rating, size = 'md' }) {
  const glowStrength = Math.max(0, (rating - 6) / 4); // 0 at rating 6, 1 at rating 10
  const dims = size === 'lg' ? { w: 64, h: 64, font: 28 } : { w: 44, h: 44, font: 18 };

  return (
    <div
      style={{
        width: dims.w,
        height: dims.h,
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-display)',
        fontWeight: 800,
        fontSize: dims.font,
        background: 'var(--surface-raised)',
        border: '1px solid var(--line)',
        color: rating < 5 ? 'var(--negative)' : 'var(--text)',
        boxShadow: glowStrength > 0 ? `0 0 ${12 * glowStrength}px ${8 * glowStrength}px var(--amber-dim)` : 'none',
      }}
    >
      {rating.toFixed(1)}
    </div>
  );
}

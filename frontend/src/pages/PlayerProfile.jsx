import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import RatingBadge from '../components/RatingBadge';
import BreakdownBars from '../components/BreakdownBars';

export default function PlayerProfile() {
  const { playerId } = useParams();
  const [summary, setSummary] = useState(null);
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getPlayerSummary(playerId), api.getPlayerMatches(playerId)])
      .then(([s, m]) => {
        setSummary(s);
        setMatches(m);
      })
      .catch(() => setError('Could not load this player. They may not have any rated matches yet.'));
  }, [playerId]);

  if (error) return <div style={{ padding: 48, color: 'var(--negative)' }}>{error}</div>;
  if (!summary) return <div style={{ padding: 48, color: 'var(--text-muted)' }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '48px 24px' }}>
      <Link to="/" style={{ color: 'var(--text-muted)', fontSize: 14 }}>&larr; Back to search</Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20, margin: '16px 0 8px' }}>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 44, fontWeight: 800, margin: 0 }}>
          {summary.player.name}
        </h1>
        <RatingBadge rating={summary.average_rating} size="lg" />
      </div>
      <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
        {summary.matches_played} matches rated &middot; high {summary.highest_rating.toFixed(1)} &middot; low {summary.lowest_rating.toFixed(1)}
      </p>

      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, marginTop: 40 }}>Match history</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {matches.map((m) => (
          <div
            key={m.statsbomb_match_id}
            style={{
              padding: 16,
              background: 'var(--surface)',
              border: '1px solid var(--line)',
              borderRadius: 8,
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: 16,
              alignItems: 'start',
            }}
          >
            <RatingBadge rating={m.rating} />
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 10 }}>
                {m.competition} &middot; {m.season}
                {(m.goals > 0 || m.assists > 0) && (
                  <span style={{ color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
                    {'  ·  '}
                    {m.goals > 0 && `G ${m.goals}`}
                    {m.goals > 0 && m.assists > 0 && '  '}
                    {m.assists > 0 && `A ${m.assists}`}
                  </span>
                )}
              </div>
              <BreakdownBars breakdown={m.breakdown} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

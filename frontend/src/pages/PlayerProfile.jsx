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
  const [selectedCompetition, setSelectedCompetition] = useState('');

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

  const competitions = [...new Set(matches.map((m) => m.competition))].sort();
  const filteredMatches = selectedCompetition
    ? matches.filter((m) => m.competition === selectedCompetition)
    : matches;

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
      {typeof summary.context_weighted_rating === 'number' && (
        <p style={{ color: 'var(--amber)', fontFamily: 'var(--font-mono)', fontSize: 13, marginTop: 4 }}>
          context-weighted average: {summary.context_weighted_rating.toFixed(2)}
          <span style={{ color: 'var(--text-muted)' }}> (weighs bigger tournaments and later stages more heavily)</span>
        </p>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 40, marginBottom: 4 }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, margin: 0 }}>Match history</h2>
        {competitions.length > 1 && (
          <select
            value={selectedCompetition}
            onChange={(e) => setSelectedCompetition(e.target.value)}
            style={{
              padding: '8px 12px',
              background: 'var(--surface)',
              border: '1px solid var(--line)',
              borderRadius: 6,
              color: 'var(--text)',
              fontFamily: 'var(--font-mono)',
              fontSize: 13,
            }}
          >
            <option value="">All competitions</option>
            {competitions.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {filteredMatches.map((m) => (
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
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                {m.match_date ? new Date(m.match_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Date unknown'}
                {' · '}{m.competition} &middot; {m.season}
                {m.stage && ` · ${m.stage}`}
                {typeof m.context_weight === 'number' && m.context_weight !== 1.0 && (
                  <span style={{ color: 'var(--amber)' }}> ×{m.context_weight.toFixed(2)}</span>
                )}
              </div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>
                {m.home_team} {m.home_score} – {m.away_score} {m.away_team}
                {(m.goals > 0 || m.assists > 0) && (
                  <span style={{ color: 'var(--amber)', fontFamily: 'var(--font-mono)', fontSize: 13, marginLeft: 10 }}>
                    {m.goals > 0 && `G ${m.goals}`}
                    {m.goals > 0 && m.assists > 0 && '  '}
                    {m.assists > 0 && `A ${m.assists}`}
                  </span>
                )}
              </div>
              <div style={{ marginTop: 8 }}>
                <BreakdownBars breakdown={m.breakdown} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

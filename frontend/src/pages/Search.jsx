import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import RatingBadge from '../components/RatingBadge';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [stats, setStats] = useState(null);
  const [topPerformances, setTopPerformances] = useState([]);
  const [dashError, setDashError] = useState(null);

  useEffect(() => {
    Promise.all([api.getDatasetStats(), api.getTopPerformances(8)])
      .then(([s, t]) => {
        setStats(s);
        setTopPerformances(t);
      })
      .catch(() => setDashError('Could not load dashboard data. Is the API running?'));
  }, []);

  async function handleSearch(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await api.searchPlayers(query.trim());
      setResults(data);
    } catch {
      setError('Search failed. Is the API running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Hero */}
      <div
        style={{
          borderBottom: '1px solid var(--line)',
          padding: '72px 24px 56px',
          background: 'radial-gradient(circle at 50% 0%, var(--amber-dim), transparent 60%)',
        }}
      >
        <div style={{ maxWidth: 720, margin: '0 auto', textAlign: 'center' }}>
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--amber)', fontSize: 13, letterSpacing: '0.08em', marginBottom: 12 }}>
            CONTEXT-WEIGHTED PLAYER RATINGS
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 64, fontWeight: 800, margin: '0 0 16px', lineHeight: 1 }}>
            Every touch, <span style={{ color: 'var(--amber)' }}>weighted by moment.</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 17, margin: '0 0 32px' }}>
            A late tackle in a tied game counts more than a routine one at 4-0.
            Search a player to see how it plays out.
          </p>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8 }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by player name..."
              style={{
                flex: 1,
                padding: '14px 18px',
                background: 'var(--surface)',
                border: '1px solid var(--line)',
                borderRadius: 8,
                color: 'var(--text)',
                fontSize: 16,
              }}
            />
            <button
              type="submit"
              style={{
                padding: '14px 28px',
                background: 'var(--amber)',
                border: 'none',
                borderRadius: 8,
                color: 'var(--bg)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Search
            </button>
          </form>

          {loading && <p style={{ color: 'var(--text-muted)', marginTop: 16 }}>Searching...</p>}
          {error && <p style={{ color: 'var(--negative)', marginTop: 16 }}>{error}</p>}

          {searched && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 20, textAlign: 'left' }}>
              {results.map((player) => (
                <Link
                  key={player.id}
                  to={`/players/${player.id}`}
                  style={{
                    padding: '14px 16px',
                    background: 'var(--surface)',
                    border: '1px solid var(--line)',
                    borderRadius: 8,
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{player.name}</span>
                  <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                    {player.primary_position || '—'}
                  </span>
                </Link>
              ))}
              {results.length === 0 && (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>No players found for "{query}".</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Dataset stats strip */}
      {stats && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 48,
            padding: '28px 24px',
            borderBottom: '1px solid var(--line)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {[
            ['Matches', stats.matches],
            ['Players', stats.players],
            ['Ratings computed', stats.ratings],
            ['Competitions', stats.competitions],
          ].map(([label, value]) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 600, color: 'var(--amber)' }}>{value}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Top performances */}
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '48px 24px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, marginBottom: 20 }}>
          Standout performances
        </h2>

        {dashError && <p style={{ color: 'var(--negative)' }}>{dashError}</p>}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {topPerformances.map((p, i) => (
            <Link
              key={`${p.player_id}-${i}`}
              to={`/players/${p.player_id}`}
              style={{
                padding: 16,
                background: 'var(--surface)',
                border: '1px solid var(--line)',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <RatingBadge rating={p.rating} />
              
             <div>
                <div style={{ fontWeight: 600 }}>{p.player_name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {p.home_team} {p.home_score}–{p.away_score} {p.away_team}
                </div>
                {(p.goals > 0 || p.assists > 0) && (
                  <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--amber)', marginTop: 4 }}>
                    {p.goals > 0 && `G ${p.goals}`}
                    {p.goals > 0 && p.assists > 0 && '  ·  '}
                    {p.assists > 0 && `A ${p.assists}`}
                  </div>
                )}
              
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

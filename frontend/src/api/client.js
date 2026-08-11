const BASE_URL = 'http://localhost:8000';

async function request(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  searchPlayers: (query) => request(`/players/search?q=${encodeURIComponent(query)}`),
  getPlayerSummary: (playerId) => request(`/players/${playerId}/summary`),
  getPlayerMatches: (playerId) => request(`/players/${playerId}/matches`),
  listMatches: (limit = 50, offset = 0) => request(`/matches?limit=${limit}&offset=${offset}`),
  getMatchRatings: (statsbombMatchId) => request(`/matches/${statsbombMatchId}/ratings`),
  getCompetitions: () => request(`/matches/competitions`),
  getTopPerformances: (limit = 8, competition = null) => {
    const params = new URLSearchParams({ limit });
    if (competition) params.set('competition', competition);
    return request(`/players/meta/top-performances?${params}`);
  },
  getDatasetStats: (competition = null) => {
    const params = new URLSearchParams();
    if (competition) params.set('competition', competition);
    return request(`/players/meta/stats?${params}`);
  },

};

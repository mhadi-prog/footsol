import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Search from './pages/Search';
import PlayerProfile from './pages/PlayerProfile';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Search />} />
        <Route path="/players/:playerId" element={<PlayerProfile />} />
      </Routes>
    </BrowserRouter>
  );
}

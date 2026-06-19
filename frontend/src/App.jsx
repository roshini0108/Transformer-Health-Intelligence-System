// frontend/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import TransformerDetail from './pages/TransformerDetail';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        display: 'flex', height: '100vh', overflow: 'hidden',
        background: '#0f1117', color: '#e2e8f0'
      }}>
        <Sidebar />
        <main style={{ flex: 1, overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transformers/:transformer_id" element={<TransformerDetail />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

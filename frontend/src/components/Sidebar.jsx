// frontend/src/components/Sidebar.jsx
import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getAlerts } from '../api/client';

const NAV = [
    { path: '/', icon: '⬛', label: 'Dashboard' },
    { path: '/alerts', icon: '🔔', label: 'Alerts' },
];

export default function Sidebar() {
    const location = useNavigate ? useLocation() : { pathname: '/' };
    const navigate = useNavigate();
    const [unackCount, setUnackCount] = useState(0);

    useEffect(() => {
        getAlerts(true)
            .then(r => setUnackCount(r.data.length))
            .catch(() => { });
    }, []);

    return (
        <aside style={{
            width: 200, flexShrink: 0,
            background: '#13151f',
            borderRight: '1px solid #1e2535',
            display: 'flex', flexDirection: 'column',
            padding: '0',
        }}>
            {/* Logo */}
            <div style={{
                padding: '20px 16px 16px',
                borderBottom: '1px solid #1e2535',
            }}>
                <div style={{
                    fontSize: 13, fontWeight: 700,
                    color: '#60a5fa', letterSpacing: 0.5,
                }}>
                    ⚡ APEPDCL AI
                </div>
                <div style={{ fontSize: 11, color: '#4a5568', marginTop: 3 }}>
                    Transformer Health Monitor
                </div>
            </div>

            {/* Nav items */}
            <nav style={{ padding: '8px 0', flex: 1 }}>
                {NAV.map(({ path, icon, label }) => {
                    const active = location.pathname === path;
                    return (
                        <div
                            key={path}
                            onClick={() => navigate(path)}
                            style={{
                                display: 'flex', alignItems: 'center',
                                gap: 10, padding: '9px 16px',
                                cursor: 'pointer',
                                background: active ? '#1a2035' : 'transparent',
                                borderLeft: active ? '3px solid #60a5fa' : '3px solid transparent',
                                color: active ? '#e2e8f0' : '#718096',
                                fontSize: 13,
                                fontWeight: active ? 500 : 400,
                                transition: 'all 0.15s',
                            }}
                        >
                            <span>{icon}</span>
                            <span style={{ flex: 1 }}>{label}</span>
                            {label === 'Alerts' && unackCount > 0 && (
                                <span style={{
                                    background: '#dc2626', color: 'white',
                                    fontSize: 10, fontWeight: 600,
                                    padding: '1px 6px', borderRadius: 10,
                                }}>
                                    {unackCount}
                                </span>
                            )}
                        </div>
                    );
                })}
            </nav>

            {/* Footer */}
            <div style={{
                padding: '12px 16px',
                borderTop: '1px solid #1e2535',
                fontSize: 11, color: '#4a5568',
            }}>
                <div style={{ fontWeight: 500, color: '#718096' }}>AEE Visakhapatnam</div>
                <div style={{ marginTop: 2 }}>v1.0 · APEPDCL</div>
            </div>
        </aside>
    );
}
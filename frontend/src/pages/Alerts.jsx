// frontend/src/pages/Alerts.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAlerts, acknowledgeAlert } from '../api/client';

const SEV_COLOR = { CRITICAL: '#dc2626', WARNING: '#ca8a04' };
const SEV_BG = { CRITICAL: '#1c0000', WARNING: '#1c1300' };

export default function Alerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const navigate = useNavigate();

    const load = () => {
        getAlerts(filter === 'unack')
            .then(r => { setAlerts(r.data); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { setLoading(true); load(); }, [filter]);

    const ack = async (id) => {
        await acknowledgeAlert(id);
        load();
    };

    return (
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: 20, fontWeight: 700 }}>Alerts</h1>
                    <p style={{ fontSize: 12, color: '#4a5568', marginTop: 4 }}>
                        {alerts.length} alert{alerts.length !== 1 ? 's' : ''} · sorted by severity
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    {['all', 'unack'].map(f => (
                        <button key={f}
                            onClick={() => setFilter(f)}
                            style={{
                                background: filter === f ? '#2d3748' : '#1a1f2e',
                                color: filter === f ? '#e2e8f0' : '#718096'
                            }}>
                            {f === 'all' ? 'All alerts' : 'Unacknowledged'}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div style={{ color: '#4a5568', textAlign: 'center', padding: 40 }}>Loading...</div>
            ) : alerts.length === 0 ? (
                <div style={{
                    background: '#13151f', border: '1px solid #1e2535',
                    borderRadius: 12, padding: 40, textAlign: 'center', color: '#4a5568'
                }}>
                    ✓ No alerts found
                </div>
            ) : (
                <div style={{ background: '#13151f', border: '1px solid #1e2535', borderRadius: 12, overflow: 'hidden' }}>
                    {alerts.map((a, i) => (
                        <div key={a.id} style={{
                            display: 'flex', alignItems: 'flex-start', gap: 14,
                            padding: '14px 16px',
                            borderBottom: i < alerts.length - 1 ? '1px solid #1e2535' : 'none',
                            opacity: a.acknowledged ? 0.5 : 1,
                        }}>
                            {/* Severity icon */}
                            <div style={{
                                width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                                background: SEV_BG[a.severity] || '#1a1f2e',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: 16,
                            }}>
                                {a.severity === 'CRITICAL' ? '🔴' : '🟡'}
                            </div>

                            {/* Content */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <span style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>
                                        {a.alert_type.replace(/_/g, ' ')} — {a.transformer_id}
                                    </span>
                                    <span style={{
                                        background: SEV_BG[a.severity],
                                        color: SEV_COLOR[a.severity],
                                        border: `1px solid ${SEV_COLOR[a.severity]}`,
                                        fontSize: 10, fontWeight: 600,
                                        padding: '1px 8px', borderRadius: 4,
                                    }}>{a.severity}</span>
                                    {a.acknowledged && (
                                        <span style={{
                                            fontSize: 10, color: '#16a34a',
                                            background: '#052e16', padding: '1px 8px',
                                            borderRadius: 4, border: '1px solid #16a34a'
                                        }}>
                                            ✓ ACK
                                        </span>
                                    )}
                                </div>
                                <div style={{
                                    fontSize: 12, color: '#718096', marginBottom: 4,
                                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                                }}>
                                    {a.transformer_name} · {a.district}
                                </div>
                                <div style={{ fontSize: 11, color: '#4a5568', lineHeight: 1.5 }}>
                                    {a.message}
                                </div>
                                <div style={{ fontSize: 11, color: '#4a5568', marginTop: 4 }}>
                                    {new Date(a.triggered_at).toLocaleString('en-IN')}
                                    {a.acknowledged_by && ` · Ack'd by ${a.acknowledged_by}`}
                                </div>
                            </div>

                            {/* Actions */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
                                <button onClick={() => navigate(`/transformers/${a.transformer_id}`)}
                                    style={{ fontSize: 11 }}>
                                    View →
                                </button>
                                {!a.acknowledged && (
                                    <button onClick={() => ack(a.id)}
                                        style={{
                                            fontSize: 11, background: '#052e16',
                                            color: '#16a34a', border: '1px solid #16a34a'
                                        }}>
                                        Acknowledge
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
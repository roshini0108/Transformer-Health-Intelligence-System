// frontend/src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPredictionsSummary, getTransformers, getAlerts } from '../api/client';

const RISK_COLOR = { LOW: '#16a34a', MEDIUM: '#ca8a04', HIGH: '#ea580c', CRITICAL: '#dc2626' };
const RISK_BG = { LOW: '#052e16', MEDIUM: '#1c1300', HIGH: '#1c0a00', CRITICAL: '#1c0000' };

function MetricCard({ label, value, sub, color }) {
    return (
        <div style={{
            background: '#13151f', border: '1px solid #1e2535',
            borderRadius: 12, padding: '16px 20px',
        }}>
            <div style={{ fontSize: 12, color: '#718096', marginBottom: 6 }}>{label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: color || '#e2e8f0', lineHeight: 1 }}>
                {value}
            </div>
            {sub && <div style={{ fontSize: 11, color: '#4a5568', marginTop: 6 }}>{sub}</div>}
        </div>
    );
}

function RiskBadge({ level }) {
    return (
        <span style={{
            background: RISK_BG[level] || '#1a1f2e',
            color: RISK_COLOR[level] || '#718096',
            border: `1px solid ${RISK_COLOR[level] || '#2d3748'}`,
            padding: '2px 10px', borderRadius: 6,
            fontSize: 11, fontWeight: 600,
        }}>
            {level}
        </span>
    );
}

function ScoreCircle({ score }) {
    const color = score >= 75 ? '#16a34a' : score >= 50 ? '#ca8a04' : score >= 25 ? '#ea580c' : '#dc2626';
    const r = 22, c = 2 * Math.PI * r;
    const fill = (score / 100) * c;
    return (
        <svg width="56" height="56" viewBox="0 0 56 56">
            <circle cx="28" cy="28" r={r} fill="none" stroke="#1e2535" strokeWidth="5" />
            <circle cx="28" cy="28" r={r} fill="none" stroke={color} strokeWidth="5"
                strokeDasharray={`${fill} ${c}`} strokeLinecap="round"
                transform="rotate(-90 28 28)" />
            <text x="28" y="33" textAnchor="middle"
                style={{ fontSize: 13, fontWeight: 700, fill: color }}>{score}</text>
        </svg>
    );
}

export default function Dashboard() {
    const [summary, setSummary] = useState(null);
    const [transformers, setTransformers] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        Promise.all([
            getPredictionsSummary(),
            getTransformers(),
            getAlerts(true),
        ]).then(([s, t, a]) => {
            setSummary(s.data);
            setTransformers(t.data);
            setAlerts(a.data);
            setLoading(false);
        }).catch(err => {
            console.error('API error:', err);
            setLoading(false);
        });
    }, []);

    if (loading) return (
        <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            height: '100%', color: '#4a5568'
        }}>
            Loading dashboard...
        </div>
    );

    // Sort: CRITICAL first, then by score ascending
    const sorted = [...transformers].sort((a, b) => {
        const order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
        const ao = order[a.risk_level] ?? 4;
        const bo = order[b.risk_level] ?? 4;
        if (ao !== bo) return ao - bo;
        return (a.health_score ?? 100) - (b.health_score ?? 100);
    });

    const critical = sorted.filter(t => t.risk_level === 'CRITICAL');
    const atRisk = sorted.filter(t => ['CRITICAL', 'HIGH', 'MEDIUM'].includes(t.risk_level));

    return (
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: 20, fontWeight: 700, color: '#e2e8f0' }}>
                        Overview Dashboard
                    </h1>
                    <p style={{ fontSize: 12, color: '#4a5568', marginTop: 4 }}>
                        Visakhapatnam District · {new Date().toLocaleDateString('en-IN', {
                            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
                        })}
                    </p>
                </div>
                {alerts.length > 0 && (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        background: '#1c0000', border: '1px solid #7f1d1d',
                        borderRadius: 8, padding: '8px 14px',
                    }}>
                        <div style={{
                            width: 8, height: 8, background: '#dc2626',
                            borderRadius: '50%', animation: 'pulse 1s infinite'
                        }} />
                        <span style={{ fontSize: 12, color: '#fca5a5' }}>
                            {alerts.length} unacknowledged alert{alerts.length > 1 ? 's' : ''}
                        </span>
                        <button
                            onClick={() => navigate('/alerts')}
                            style={{
                                fontSize: 11, padding: '3px 10px',
                                background: '#7f1d1d', border: 'none', color: '#fca5a5'
                            }}>
                            View →
                        </button>
                    </div>
                )}
            </div>

            {/* Metric cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                <MetricCard
                    label="Total Transformers"
                    value={summary?.total ?? transformers.length}
                    sub="Visakhapatnam dist."
                />
                <MetricCard
                    label="Healthy"
                    value={summary?.LOW ?? 0}
                    sub="Score ≥ 75"
                    color="#16a34a"
                />
                <MetricCard
                    label="Needs Attention"
                    value={(summary?.MEDIUM ?? 0) + (summary?.HIGH ?? 0)}
                    sub="Score 25–74"
                    color="#ca8a04"
                />
                <MetricCard
                    label="Critical Risk"
                    value={summary?.CRITICAL ?? 0}
                    sub="Immediate action"
                    color="#dc2626"
                />
            </div>

            {/* Two column layout */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

                {/* At-risk transformers */}
                <div style={{
                    background: '#13151f', border: '1px solid #1e2535',
                    borderRadius: 12, padding: 16,
                }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 14 }}>
                        ⚠ Transformers Needing Attention
                    </div>

                    {atRisk.length === 0 ? (
                        <div style={{ color: '#4a5568', fontSize: 12, padding: '20px 0', textAlign: 'center' }}>
                            ✓ All transformers healthy
                        </div>
                    ) : (
                        atRisk.slice(0, 8).map(t => (
                            <div
                                key={t.transformer_id}
                                onClick={() => navigate(`/transformers/${t.transformer_id}`)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 12,
                                    padding: '10px 8px',
                                    borderBottom: '1px solid #1e2535',
                                    cursor: 'pointer', borderRadius: 6,
                                    transition: 'background 0.1s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.background = '#1a1f2e'}
                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                            >
                                <ScoreCircle score={t.health_score ?? 0} />
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{
                                        fontSize: 13, fontWeight: 500, color: '#e2e8f0',
                                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                                    }}>
                                        {t.name}
                                    </div>
                                    <div style={{ fontSize: 11, color: '#4a5568', marginTop: 2 }}>
                                        {t.transformer_id} · {t.capacity_kva} kVA
                                    </div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                                    <RiskBadge level={t.risk_level} />
                                    <div style={{ fontSize: 11, color: '#4a5568' }}>
                                        {((t.failure_probability_30d ?? 0) * 100).toFixed(0)}% fail risk
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* District health breakdown */}
                <div style={{
                    background: '#13151f', border: '1px solid #1e2535',
                    borderRadius: 12, padding: 16,
                }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', marginBottom: 14 }}>
                        📊 Fleet Health Overview
                    </div>

                    {/* Risk distribution bars */}
                    {[
                        { level: 'LOW', label: 'Healthy (score ≥ 75)', count: summary?.LOW ?? 0 },
                        { level: 'MEDIUM', label: 'Medium risk (50–74)', count: summary?.MEDIUM ?? 0 },
                        { level: 'HIGH', label: 'High risk (25–49)', count: summary?.HIGH ?? 0 },
                        { level: 'CRITICAL', label: 'Critical (score < 25)', count: summary?.CRITICAL ?? 0 },
                    ].map(({ level, label, count }) => {
                        const total = summary?.total || 1;
                        const pct = (count / total) * 100;
                        return (
                            <div key={level} style={{ marginBottom: 14 }}>
                                <div style={{
                                    display: 'flex', justifyContent: 'space-between',
                                    fontSize: 12, marginBottom: 5
                                }}>
                                    <span style={{ color: '#a0aec0' }}>{label}</span>
                                    <span style={{ color: RISK_COLOR[level], fontWeight: 600 }}>
                                        {count} transformers
                                    </span>
                                </div>
                                <div style={{ height: 6, background: '#1e2535', borderRadius: 3, overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%', width: `${pct}%`,
                                        background: RISK_COLOR[level], borderRadius: 3,
                                        transition: 'width 0.6s ease',
                                    }} />
                                </div>
                            </div>
                        );
                    })}

                    {/* Summary stats */}
                    <div style={{
                        display: 'grid', gridTemplateColumns: '1fr 1fr',
                        gap: 10, marginTop: 20,
                    }}>
                        <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px' }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: '#dc2626' }}>
                                {critical.length}
                            </div>
                            <div style={{ fontSize: 11, color: '#4a5568', marginTop: 2 }}>
                                Need immediate action
                            </div>
                        </div>
                        <div style={{ background: '#0f1117', borderRadius: 8, padding: '10px 12px' }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: '#ca8a04' }}>
                                {alerts.length}
                            </div>
                            <div style={{ fontSize: 11, color: '#4a5568', marginTop: 2 }}>
                                Unacknowledged alerts
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Full transformer table */}
            <div style={{
                background: '#13151f', border: '1px solid #1e2535',
                borderRadius: 12, overflow: 'hidden',
            }}>
                <div style={{
                    padding: '14px 16px', borderBottom: '1px solid #1e2535',
                    fontSize: 13, fontWeight: 600, color: '#e2e8f0'
                }}>
                    All Transformers — Sorted by Risk
                </div>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ background: '#0f1117' }}>
                                {['Transformer ID', 'Name', 'District', 'Capacity', 'Health Score', 'Risk Level', 'Fail Prob', ''].map(h => (
                                    <th key={h} style={{
                                        padding: '10px 14px', textAlign: 'left',
                                        fontSize: 11, color: '#4a5568', fontWeight: 600,
                                        borderBottom: '1px solid #1e2535',
                                    }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((t, i) => (
                                <tr
                                    key={t.transformer_id}
                                    onClick={() => navigate(`/transformers/${t.transformer_id}`)}
                                    style={{
                                        cursor: 'pointer',
                                        borderBottom: '1px solid #1a1f2e',
                                        transition: 'background 0.1s',
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.background = '#1a1f2e'}
                                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                >
                                    <td style={{
                                        padding: '10px 14px', fontSize: 12,
                                        color: '#60a5fa', fontFamily: 'monospace'
                                    }}>
                                        {t.transformer_id}
                                    </td>
                                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#e2e8f0' }}>
                                        {t.name}
                                    </td>
                                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#718096' }}>
                                        {t.district}
                                    </td>
                                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#718096' }}>
                                        {t.capacity_kva} kVA
                                    </td>
                                    <td style={{ padding: '10px 14px' }}>
                                        {t.health_score != null ? (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <div style={{
                                                    width: 60, height: 5, background: '#1e2535',
                                                    borderRadius: 3, overflow: 'hidden',
                                                }}>
                                                    <div style={{
                                                        height: '100%',
                                                        width: `${t.health_score}%`,
                                                        background: RISK_COLOR[t.risk_level] || '#718096',
                                                        borderRadius: 3,
                                                    }} />
                                                </div>
                                                <span style={{
                                                    fontSize: 12, color: RISK_COLOR[t.risk_level],
                                                    fontWeight: 600
                                                }}>
                                                    {t.health_score}
                                                </span>
                                            </div>
                                        ) : (
                                            <span style={{ fontSize: 11, color: '#4a5568' }}>No data</span>
                                        )}
                                    </td>
                                    <td style={{ padding: '10px 14px' }}>
                                        {t.risk_level
                                            ? <RiskBadge level={t.risk_level} />
                                            : <span style={{ fontSize: 11, color: '#4a5568' }}>—</span>
                                        }
                                    </td>
                                    <td style={{ padding: '10px 14px', fontSize: 12, color: '#718096' }}>
                                        {t.failure_probability_30d != null
                                            ? `${(t.failure_probability_30d * 100).toFixed(0)}%`
                                            : '—'
                                        }
                                    </td>
                                    <td style={{ padding: '10px 14px' }}>
                                        <button
                                            onClick={e => { e.stopPropagation(); navigate(`/transformers/${t.transformer_id}`); }}
                                            style={{ fontSize: 11, padding: '3px 10px' }}
                                        >
                                            View →
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
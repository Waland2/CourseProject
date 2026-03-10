import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export function MetricRadarChart({ data, keys, height = 340 }) {
  return (
    <div className="chart-card">
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="metric" />
          <PolarRadiusAxis />
          <Legend />
          {keys.map((key) => (
            <Radar key={key.dataKey} name={key.name} dataKey={key.dataKey} fillOpacity={0.25} />
          ))}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

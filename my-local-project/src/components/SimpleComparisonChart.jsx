import { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
} from 'recharts';

function useViewportWidth() {
  const getWidth = () =>
    typeof window !== 'undefined' ? window.innerWidth : 1280;

  const [width, setWidth] = useState(getWidth);

  useEffect(() => {
    const onResize = () => setWidth(getWidth());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return width;
}

function wrapLabel(text, maxLineLength = 26) {
  if (!text) return ['—'];

  const words = String(text).split(' ');
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    const nextLine = currentLine ? `${currentLine} ${word}` : word;

    if (nextLine.length <= maxLineLength) {
      currentLine = nextLine;
    } else {
      if (currentLine) {
        lines.push(currentLine);
      }
      currentLine = word;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines;
}

function getMaxLines(data, key, maxLineLength) {
  if (!Array.isArray(data) || !data.length) return 1;

  return data.reduce((max, item) => {
    const lines = wrapLabel(item?.[key], maxLineLength).length;
    return Math.max(max, lines);
  }, 1);
}

function getYAxisWidth(data, key, viewportWidth) {
  if (!Array.isArray(data) || !data.length) {
    if (viewportWidth <= 560) return 100;
    if (viewportWidth <= 768) return 130;
    return 240;
  }

  const longest = data.reduce((max, item) => {
    const len = String(item?.[key] ?? '').length;
    return Math.max(max, len);
  }, 0);

  if (viewportWidth <= 560) return 100;
  if (viewportWidth <= 768) return 130;

  if (longest > 70) return 320;
  if (longest > 56) return 280;
  if (longest > 42) return 240;
  if (longest > 30) return 210;

  return 180;
}

function CustomYAxisTick(props) {
  const {
    x,
    y,
    payload,
    maxLineLength = 26,
    fontSize = 14,
    lineHeight = 16,
  } = props;

  const lines = wrapLabel(payload.value, maxLineLength);

  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} textAnchor="end" fill="#5b6475" fontSize={fontSize} dy={4}>
        {lines.map((line, index) => (
          <tspan key={`${line}-${index}`} x={0} dy={index === 0 ? 0 : lineHeight}>
            {line}
          </tspan>
        ))}
      </text>
    </g>
  );
}

export function SimpleComparisonChart({
  data = [],
  dataKey,
  yKey = 'name',
  height,
  valueFormatter = (value) => String(value),
}) {
  const viewportWidth = useViewportWidth();
  const isMobile = viewportWidth <= 560;
  const isTablet = viewportWidth <= 768;

  const maxLineLength = isMobile ? 12 : 26;
  const maxLines = getMaxLines(data, yKey, maxLineLength);
  const yAxisWidth = getYAxisWidth(data, yKey, viewportWidth);
  const rowHeight = Math.max(isMobile ? 36 : 48, maxLines * (isMobile ? 14 : 18) + 16);
  const calculatedHeight = Math.max(isMobile ? 220 : 240, data.length * rowHeight + 24);
  const finalHeight = height || calculatedHeight;

  return (
    <div className="chart-card">
      <div style={{ width: '100%', overflowX: 'hidden' }}>
        <div style={{ width: '100%', height: finalHeight }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{
                top: 8,
                right: isMobile ? 24 : isTablet ? 40 : 80,
                left: 8,
                bottom: 8,
              }}
              barCategoryGap={isMobile ? 10 : 16}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis
                type="number"
                axisLine={false}
                tickLine={false}
                fontSize={isMobile ? 12 : 14}
                tickFormatter={(value) => valueFormatter(Number(value))}
              />
              <YAxis
                type="category"
                dataKey={yKey}
                width={yAxisWidth}
                axisLine={false}
                tickLine={false}
                interval={0}
                tick={
                  <CustomYAxisTick
                    maxLineLength={maxLineLength}
                    fontSize={isMobile ? 12 : 14}
                    lineHeight={isMobile ? 14 : 16}
                  />
                }
              />
              <Tooltip
                formatter={(value) => [valueFormatter(Number(value)), 'Значение']}
                cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
              />
              <Bar dataKey={dataKey} radius={[0, 6, 6, 0]} maxBarSize={isMobile ? 22 : 28}>
                <LabelList
                  dataKey={dataKey}
                  position="right"
                  formatter={(value) => valueFormatter(Number(value))}
                  style={{
                    fill: '#7a6b5d',
                    fontSize: isMobile ? 12 : 14,
                  }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
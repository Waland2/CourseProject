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
  Legend,
} from 'recharts';

const DEFAULT_BAR_COLORS = ['#2563eb', '#d97706', '#16a34a', '#9333ea', '#dc2626'];

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

function wrapLabel(text, maxLineLength = 18) {
  if (!text) return [''];

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

function getMaxLines(data, xKey, maxLineLength) {
  if (!Array.isArray(data) || data.length === 0) return 1;

  return data.reduce((max, item) => {
    const lines = wrapLabel(item?.[xKey], maxLineLength).length;
    return Math.max(max, lines);
  }, 1);
}

function getYAxisWidth(data, xKey, viewportWidth) {
  if (!Array.isArray(data) || data.length === 0) {
    if (viewportWidth <= 560) return 92;
    if (viewportWidth <= 768) return 120;
    return 140;
  }

  const longest = data.reduce((max, item) => {
    const len = String(item?.[xKey] ?? '').length;
    return Math.max(max, len);
  }, 0);

  if (viewportWidth <= 560) return 92;
  if (viewportWidth <= 768) return 120;

  if (longest > 40) return 220;
  if (longest > 32) return 200;
  if (longest > 26) return 180;
  if (longest > 20) return 160;

  return 140;
}

function CustomYAxisTick(props) {
  const {
    x,
    y,
    payload,
    maxLineLength = 18,
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

export function MetricBarChart({
  data = [],
  xKey,
  bars = [],
  layout = 'horizontal',
  height,
  valueFormatter = (value) => String(value),
}) {
  const viewportWidth = useViewportWidth();
  const isHorizontal = layout === 'horizontal';
  const isMobile = viewportWidth <= 560;
  const isTablet = viewportWidth <= 768;

  const maxLineLength = isMobile ? 12 : 18;
  const maxLines = getMaxLines(data, xKey, maxLineLength);
  const yAxisWidth = getYAxisWidth(data, xKey, viewportWidth);

  const rowHeight = Math.max(isMobile ? 34 : 42, maxLines * (isMobile ? 14 : 18) + 14);
  const calculatedHeight = Math.max(isMobile ? 280 : 360, data.length * rowHeight + 32);
  const finalHeight = height || calculatedHeight;

  const minChartWidth = isHorizontal
    ? '100%'
    : Math.max(isMobile ? 360 : 520, data.length * (isMobile ? 56 : 72));

  return (
    <div style={{ width: '100%', overflowX: isHorizontal ? 'hidden' : 'auto' }}>
      <div style={{ width: '100%', minWidth: minChartWidth, height: finalHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout={isHorizontal ? 'vertical' : 'horizontal'}
            margin={{
              top: 8,
              right: isMobile ? 16 : isTablet ? 24 : 44,
              left: isHorizontal ? (isMobile ? 4 : 12) : 8,
              bottom: isHorizontal ? 8 : 24,
            }}
            barCategoryGap={isMobile ? 8 : 12}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />

            {isHorizontal ? (
              <>
                <XAxis
                  type="number"
                  tickFormatter={(value) => valueFormatter(Number(value))}
                  axisLine={false}
                  tickLine={false}
                  fontSize={isMobile ? 12 : 14}
                />
                <YAxis
                  type="category"
                  dataKey={xKey}
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
              </>
            ) : (
              <>
                <XAxis
                  type="category"
                  dataKey={xKey}
                  axisLine={false}
                  tickLine={false}
                  fontSize={isMobile ? 12 : 14}
                />
                <YAxis
                  type="number"
                  tickFormatter={(value) => valueFormatter(Number(value))}
                  axisLine={false}
                  tickLine={false}
                  fontSize={isMobile ? 12 : 14}
                />
              </>
            )}

            <Tooltip
              formatter={(value, name) => [valueFormatter(Number(value)), name]}
              cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
            />

            <Legend />

            {bars.map((bar, index) => (
              <Bar
                key={bar.dataKey}
                dataKey={bar.dataKey}
                name={bar.name}
                fill={bar.color || DEFAULT_BAR_COLORS[index % DEFAULT_BAR_COLORS.length]}
                radius={isHorizontal ? [0, 6, 6, 0] : [6, 6, 0, 0]}
                maxBarSize={isMobile ? 22 : 28}
              >

              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
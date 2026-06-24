/**
 * CircularProgress — SVG-based circular progress ring.
 *
 * Color transitions (M3 spec):
 *   > 50% → success green
 *   20–50% → warning amber
 *   < 20% → error crimson
 *
 * Props
 * ─────
 *  value      0–100 (percentage)
 *  size       pixel diameter (default 120)
 *  stroke     ring stroke width (default 10)
 *  label      centre label text (e.g. "840g")
 *  sublabel   smaller text below label (e.g. "pearls")
 */

import React from "react";

interface CircularProgressProps {
  value: number;        // 0–100
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  className?: string;
}

function getColor(value: number): string {
  if (value > 50) return "hsl(142, 71%, 35%)";   // success green
  if (value > 20) return "hsl(38, 92%, 50%)";    // warning amber
  return "hsl(354, 70%, 42%)";                   // error crimson
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  size = 120,
  stroke = 10,
  label,
  sublabel,
  className = "",
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedValue / 100) * circumference;
  const color = getColor(clampedValue);
  const centre = size / 2;

  return (
    <div
      className={`inline-flex flex-col items-center justify-center ${className}`}
      role="progressbar"
      aria-valuenow={clampedValue}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={sublabel ? `${sublabel}: ${clampedValue}%` : `${clampedValue}%`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle
          cx={centre}
          cy={centre}
          r={radius}
          fill="none"
          stroke="hsl(0, 0%, 90%)"
          strokeWidth={stroke}
        />
        {/* Progress arc */}
        <circle
          cx={centre}
          cy={centre}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${centre} ${centre})`}
          style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.3s ease" }}
        />
        {/* Centre label */}
        {label && (
          <text
            x={centre}
            y={sublabel ? centre - 6 : centre + 5}
            textAnchor="middle"
            fontSize={size * 0.14}
            fontWeight="700"
            fill="hsl(0, 0%, 10%)"
          >
            {label}
          </text>
        )}
        {sublabel && (
          <text
            x={centre}
            y={centre + 14}
            textAnchor="middle"
            fontSize={size * 0.11}
            fill="hsl(0, 0%, 45%)"
          >
            {sublabel}
          </text>
        )}
      </svg>
    </div>
  );
};

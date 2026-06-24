/**
 * CircularProgress — Premium SVG-based circular progress ring.
 *
 * Color transitions:
 *   > 50% → success green
 *   20–50% → warning amber
 *   < 20% → error crimson
 *
 * Features: smooth transitions, drop shadow, animated stroke.
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

function getTrackColor(value: number): string {
  if (value > 50) return "hsl(142, 71%, 90%)";
  if (value > 20) return "hsl(38, 92%, 90%)";
  return "hsl(354, 70%, 92%)";
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
  const trackColor = getTrackColor(clampedValue);
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
        <defs>
          <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.15" />
          </filter>
        </defs>
        
        {/* Track */}
        <circle
          cx={centre}
          cy={centre}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={stroke}
          filter="url(#shadow)"
        />
        
        {/* Progress arc with glow */}
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
          style={{ 
            transition: "stroke-dashoffset 0.5s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.3s ease",
            filter: "drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1))"
          }}
        />
        
        {/* Centre label */}
        {label && (
          <text
            x={centre}
            y={sublabel ? centre - 6 : centre + 5}
            textAnchor="middle"
            fontSize={size * 0.16}
            fontWeight="900"
            fill="hsl(0, 0%, 10%)"
            letterSpacing="-0.5"
          >
            {label}
          </text>
        )}
        
        {sublabel && (
          <text
            x={centre}
            y={centre + 16}
            textAnchor="middle"
            fontSize={size * 0.09}
            fontWeight="600"
            fill="hsl(0, 0%, 45%)"
            letterSpacing="0.3"
          >
            {sublabel}
          </text>
        )}
      </svg>
    </div>
  );
};

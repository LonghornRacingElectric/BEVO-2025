import React from "react";

// Order: BSPD, IMD, L-ESTOP, BATTERY HVIL, R-ESTOP, E-METER HVIL, MSD HVIL, TSMS, CRASH SENSOR, BOTS, BMS, F-ESTOP
const LABELS = [
  // Row 1
  "BSPD", "BMS", "IMD",
  // Row 2
  "BOTS", "L-ESTOP", "BATTERY HVIL",
  // Row 3
  "CRASH SENSOR", "F-ESTOP", "R-ESTOP",
  // Row 4
  "TSMS", "MSD HVIL", "E-METER HVIL"
];

// Refined grid positions for 800x480, matching Figma
const grid = [
  // Row 1
  { x: 140, y: 90 },   // BSPD
  { x: 400, y: 90 },   // BMS
  { x: 660, y: 90 },   // IMD
  // Row 2
  { x: 140, y: 200 },  // BOTS
  { x: 400, y: 200 },  // L-ESTOP
  { x: 660, y: 200 },  // BATTERY HVIL
  // Row 3
  { x: 140, y: 310 },  // CRASH SENSOR
  { x: 400, y: 310 },  // F-ESTOP
  { x: 660, y: 310 },  // R-ESTOP
  // Row 4
  { x: 140, y: 420 },  // TSMS
  { x: 400, y: 420 },  // MSD HVIL
  { x: 660, y: 420 },  // E-METER HVIL
];

// Horizontal lines: each row, offset so they don't overlap text
const horiz = [
  // Row 1
  { a: 0, b: 1, y: 120, x1: 60, x2: 400 },
  { a: 1, b: 2, y: 120, x1: 400, x2: 740 },
  // Row 2
  { a: 3, b: 4, y: 230, x1: 60, x2: 400 },
  { a: 4, b: 5, y: 230, x1: 400, x2: 740 },
  // Row 3
  { a: 6, b: 7, y: 340, x1: 60, x2: 400 },
  { a: 7, b: 8, y: 340, x1: 400, x2: 740 },
  // Row 4
  { a: 9, b: 10, y: 450, x1: 60, x2: 400 },
  { a: 10, b: 11, y: 450, x1: 400, x2: 740 },
];
// Vertical lines: BOTS-CRASH SENSOR, IMD-BATTERY HVIL, R-ESTOP-E-METER HVIL
const vert = [
  // BOTS to CRASH SENSOR
  { a: 3, b: 6, x: 140, y1: 200, y2: 310 },
  // IMD to BATTERY HVIL
  { a: 2, b: 5, x: 660, y1: 120, y2: 200 },
  // R-ESTOP to E-METER HVIL
  { a: 8, b: 11, x: 660, y1: 310, y2: 420 },
];

function getColor(ok: boolean) {
  return ok ? "#00FF00" : "#FF2222";
}

interface ShutdownCircuitScreenProps {
  shutdownLegs: boolean[]; // Array of booleans, length >= 12
}

const ShutdownCircuitScreen: React.FC<ShutdownCircuitScreenProps> = ({ shutdownLegs }) => {
  const width = 800;
  const height = 480;
  const glowColor = "#FF2222";
  const fontSize = 24;

  return (
    <div style={{ width, height, background: "#000", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", boxShadow: `0 0 80px 20px ${glowColor}` }}>
      <svg width={width} height={height} style={{ display: "block" }}>
        {/* Horizontal lines */}
        {horiz.map((line, i) => (
          <line
            key={"h"+i}
            x1={line.x1}
            y1={line.y}
            x2={line.x2}
            y2={line.y}
            stroke={getColor(!!shutdownLegs[line.a] && !!shutdownLegs[line.b])}
            strokeWidth={12}
            opacity={1}
            style={{ filter: `drop-shadow(0 0 24px ${getColor(!!shutdownLegs[line.a] && !!shutdownLegs[line.b])})` }}
          />
        ))}
        {/* Vertical lines */}
        {vert.map((line, i) => (
          <line
            key={"v"+i}
            x1={line.x}
            y1={line.y1}
            x2={line.x}
            y2={line.y2}
            stroke={getColor(!!shutdownLegs[line.a] && !!shutdownLegs[line.b])}
            strokeWidth={12}
            opacity={1}
            style={{ filter: `drop-shadow(0 0 24px ${getColor(!!shutdownLegs[line.a] && !!shutdownLegs[line.b])})` }}
          />
        ))}
        {/* Draw labels */}
        {grid.map((pos, i) => (
          <text
            key={i}
            x={pos.x}
            y={pos.y}
            textAnchor="middle"
            fontSize={fontSize}
            fill={getColor(!!shutdownLegs[i])}
            fontWeight="bold"
            fontFamily="monospace, 'Menlo', 'Consolas', 'Courier New', Courier"
            letterSpacing={2}
            style={{ textShadow: `0 0 32px ${getColor(!!shutdownLegs[i])}` }}
            alignmentBaseline="middle"
            dominantBaseline="middle"
          >
            {LABELS[i]}
          </text>
        ))}
      </svg>
    </div>
  );
};

export default ShutdownCircuitScreen; 
import React, { useMemo, useEffect, useRef } from 'react';
import './Speedometer.css';

interface SpeedometerProps {
    progress: number;
    size?: number;
    strokeWidth?: number;
    numTicks?: number;
}

const Speedometer: React.FC<SpeedometerProps> = ({
    progress,
    size = 200,
    strokeWidth = 20,
    numTicks = 10,
}) => {
    const { PI, cos, sin } = Math;
    const cx = size / 2;
    const cy = size / 2;
    const r = (size - strokeWidth) / 2;

    const startAngle = -PI * 0.25;
    const endAngle = PI + PI * 0.25;

    const x1 = cx - r * cos(startAngle);
    const y1 = cy - r * sin(startAngle);
    const x2 = cx - r * cos(endAngle);
    const y2 = cy - r * sin(endAngle);

    const d = `M ${x1} ${y1} A ${r} ${r} 0 1 1 ${x2} ${y2}`;
    const circumference = useMemo(() => r * (PI + 0.5 * PI), [r]);
    const strokeDashoffset = useMemo(
        () => circumference - (progress / 100) * circumference,
        [progress, circumference]
    );

    const progressRef = useRef<SVGPathElement>(null);

    useEffect(() => {
        if (progressRef.current) {
            progressRef.current.style.transition = "stroke-dashoffset .15s ease-in-out";
            progressRef.current.style.strokeDashoffset = `${strokeDashoffset}`;
        }
    }, [strokeDashoffset]);

    const ticks = useMemo(() => {
        const tickLength = 10;
        const tickWidth = 2;
        const tickOffset = r + tickLength / 2;

        return Array.from({ length: numTicks + 1}).map((_, i) => {
            const angle = startAngle + ((endAngle - startAngle) / numTicks) * i;
            const xStart = cx - (r - tickOffset) * cos(angle);
            const yStart = cy - (r - tickOffset) * sin(angle);
            const xEnd = cx - (r + tickOffset) * cos(angle);
            const yEnd = cy - (r + tickOffset) * sin(angle);

            return (
                <line
                    key={i}
                    x1={xStart}
                    y1={yStart}
                    x2={xEnd}
                    y2={yEnd}
                    stroke="#000"
                    strokeWidth={tickWidth}
                />
            );
        });
    }, [numTicks, startAngle, endAngle, cx, cy, r]);

    const tickNumbers = useMemo(() => {
        const numberOffset = r - 25;
        return Array.from({ length: numTicks + 1}).map((_, i) => {
            const angle = startAngle + ((endAngle - startAngle) / numTicks * i);
            const x = cx - numberOffset * cos(angle);
            const y = cy - numberOffset * sin(angle);
            const value = Math.round((i / numTicks) * 100);

            return (
                <text
                    key={i}
                    x={x}
                    y={y}
                    textAnchor="middle"
                    alignmentBaseline="middle"
                    fontSize="12"
                    fill="white"
                >
                    {value}
                </text>
            );
        });
    }, [numTicks, startAngle, endAngle, cx, cy, r])

    const MAr = r * 0.6;
    const MAx1 = cx - MAr * cos(startAngle);
    const MAy1 = cy - MAr * sin(startAngle);
    const MAx2 = cx - MAr * cos(endAngle);
    const MAy2 = cy - MAr * sin(endAngle);

    const MAd = `M ${MAx1} ${MAy1} A ${MAr} ${MAr} 0 1 1 ${MAx2} ${MAy2}`;

    return (
        <div className="speedometer-container">
            <svg width={size} height={size}>
                {/* Background track */}
                <path
                    fill="none"
                    stroke="#e2e2e8"
                    strokeWidth={strokeWidth}
                    strokeDasharray={`${circumference} ${circumference}`}
                    d={d}
                />
                {/* Progress track */}
                <path
                    ref={progressRef}
                    fill="none"
                    stroke="url(#grad)"
                    strokeWidth={strokeWidth}
                    strokeDasharray={`${circumference} ${circumference}`}
                    strokeDashoffset={circumference} // Start with no progress
                    d={d}
                />
                {/* Ticks */}
                {ticks}
                {/* Numbers */}
                {tickNumbers}
                {/* Marker (needle) */}
                <g transform={`rotate(${(progress / 100) * 270 - 135} ${cx} ${cy})`} style={{ transition: "transform .1s ease-in-out" }}>
                    <line
                        x1={cx}
                        y1={cy - (r - 15)} // Needle base near center
                        x2={cx}
                        y2={cy - (r + 15)} // Needle tip near edge
                        stroke="#555555"
                        strokeWidth={8}
                    />
                </g>
                {/* Value */}
                <circle cx={cx} cy={cy} r={size / 6} fill="#333F48" />
                <path
                    fill="none"
                    stroke="#BF5700"
                    strokeWidth={5}
                    d={MAd}
                />
                <text
                    x={cx}
                    y={cy+5}
                    textAnchor="middle"
                    alignmentBaseline="middle"
                    fontSize="48"
                    fill="white"
                    fontWeight="bold"
                >
                    {Math.round(progress)}
                </text>
                {/* Gradient definition */}
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0" stopColor="green" />
                        <stop offset="0.5" stopColor="yellow" />
                        <stop offset="1" stopColor="red" />
                    </linearGradient>
                </defs>
            </svg>
        </div>
    );
};

export default Speedometer;
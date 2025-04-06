import React from "react";
import "./StatItem.css";

interface StatItemProps {
    label: string;
    value: string | number;
    color?: string;
    className?: string;
}

function StatItem({ label, value, color, className = "" }: StatItemProps) {
    return (
        <div className={`stat-item ${className || "".trim()}`}>
            <span className="label">{label}</span>
            <span className="value" style={{ color }}>{value}</span>
        </div>
    );
}

export default StatItem;
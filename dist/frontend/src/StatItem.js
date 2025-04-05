"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
require("./StatItem.css");
function StatItem({ label, value, color, className = "" }) {
    return (<div className={`stat-item ${className || "".trim()}`}>
            <span className="label">{label}</span>
            <span className="value" style={{ color }}>{value}</span>
        </div>);
}
exports.default = StatItem;

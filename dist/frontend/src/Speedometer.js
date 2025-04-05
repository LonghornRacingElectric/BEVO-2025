"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
require("./Speedometer.css");
const Speedometer = ({ speed }) => {
    return (<div className="speedometer">
            <div className="needle" style={{ "--score": speed }}>
                <span className="score">{speed}</span>
            </div>
        </div>);
};
exports.default = Speedometer;

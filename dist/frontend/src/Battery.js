"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
require("./Battery.css");
const Battery = ({ charge }) => {
    let batteryColor = "green";
    if (charge <= 20)
        batteryColor = "red";
    else if (charge <= 50)
        batteryColor = "yellow";
    return (<div className="battery-container">
            <div className="battery">
                <div className="battery-level" style={{
            width: `${charge}%`,
            backgroundColor: batteryColor,
        }}></div>
            </div>
            <span className="battery-text">{charge}%</span>
        </div>);
};
exports.default = Battery;

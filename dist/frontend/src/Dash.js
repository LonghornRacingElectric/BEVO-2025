"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importStar(require("react"));
// import './Dash.css';
require("bootstrap/dist/css/bootstrap.min.css");
require("./Dash.css");
const StatItem_1 = __importDefault(require("./StatItem"));
const react_bootstrap_1 = require("react-bootstrap");
const websocket_1 = __importDefault(require("./websocket"));
const Battery_1 = __importDefault(require("./Battery"));
const Speedometer_1 = __importDefault(require("./Speedometer"));
function Dash() {
    const { data, isConnected } = (0, websocket_1.default)('ws://localhost:8001/');
    const [charge, setCharge] = (0, react_1.useState)(100);
    const [speed, setSpeed] = (0, react_1.useState)(0);
    (0, react_1.useEffect)(() => {
        const interval = setInterval(() => {
            setCharge(prevCharge => (prevCharge > 0 ? prevCharge - 1 : 0));
        }, 1000);
        return () => clearInterval(interval);
    }, []);
    (0, react_1.useEffect)(() => {
        const interval = setInterval(() => {
            setSpeed((prevSpeed) => (prevSpeed < 120 ? prevSpeed + 5 : 0));
        }, 1000);
        return () => clearInterval(interval);
    }, []);
    return (<react_bootstrap_1.Container fluid className="Dash">
      <react_bootstrap_1.Row className="justify-content-center text-center">
        <react_bootstrap_1.Col xs={6} className="left">
          <Speedometer_1.default speed={speed}/>
        </react_bootstrap_1.Col>
        
        <react_bootstrap_1.Col xs={3} className="center">
          <StatItem_1.default label="Speed" value="39" className="large-stat"/>
          <StatItem_1.default label="Power Draw" value="73 kW"/>
          <Battery_1.default charge={charge}/>
        </react_bootstrap_1.Col>

        <react_bootstrap_1.Col xs={3} className="right">
          <StatItem_1.default label="TC LONG" value="5"/>
          <StatItem_1.default label="LV SOC" value="70%"/>
          <StatItem_1.default label="Lap Energy" value="378 Wh"/>
          <StatItem_1.default label="Target Energy" value="350 Wh"/>
        </react_bootstrap_1.Col>
      </react_bootstrap_1.Row>

      {/* <div className="bottom-metric">
          <StatItem label="Song Playing" color="#bf5700" value="TEXAS FIGHT" />
        </div> */}
    </react_bootstrap_1.Container>);
}
exports.default = Dash;

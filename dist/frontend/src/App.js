"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const logo_svg_1 = __importDefault(require("./logo.svg"));
require("./App.css");
const websocket_1 = __importDefault(require("./websocket"));
function toHexString(arr) {
    let str = "";
    for (let i = 0; i++; i < arr.length) {
        str += arr[i] + " ";
    }
    console.log(arr);
    return str;
}
function App() {
    const { data, isConnected } = (0, websocket_1.default)('ws://localhost:8001/');
    return (<div className="App">
      <header className="App-header">
        <img src={logo_svg_1.default} className="App-logo" alt="logo"/>
        <p>
          {isConnected ? 'Connected' : 'Disconnected'}
          <div>
          {data ? data.id : 0} | {data ? data.timestamp : 0} | 
          {data ? toHexString(data.data) : 0}
          </div>
        </p>
        <a className="App-link" href="https://reactjs.org" target="_blank" rel="noopener noreferrer">
        </a>
      </header>
    </div>);
}
exports.default = App;

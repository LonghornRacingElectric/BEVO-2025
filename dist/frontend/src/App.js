"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const logo_svg_1 = __importDefault(require("./logo.svg"));
require("./App.css");
const websocket_1 = __importDefault(require("./websocket"));
function App() {
    const { data, isConnected } = (0, websocket_1.default)('ws://localhost:8001/');
    return (<div className="App">
      <header className="App-header">
        <img src={logo_svg_1.default} className="App-logo" alt="logo"/>
        <p>
          {isConnected ? 'Connected' : 'Disconnected'}
          {data}
          {/* Edit <code>src/App.tsx</code> and save to reload. */}
        </p>
        <a className="App-link" href="https://reactjs.org" target="_blank" rel="noopener noreferrer">
        </a>
      </header>
    </div>);
}
exports.default = App;

import React from 'react';
import logo from './logo.svg';
import './App.css';
import useWebSocket from "./websocket";



function App() {
  const { data, isConnected } = useWebSocket('ws://localhost:8001/');

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          {isConnected ? 'Connected' : 'Disconnected'}
          {data}
          {/* Edit <code>src/App.tsx</code> and save to reload. */}
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
        </a>
      </header>
    </div>
  );
}

export default App;

import React from 'react';
import logo from './logo.svg';
import './App.css';
import useWebSocket from "./websocket";

function toHexString(arr: number[]){
  let str : string = "";
  for(let i = 0; i ++; i < arr.length){
    str += arr[i] + " ";
  }
  console.log(arr);
  return str
}

function App() {
  const { data, isConnected } = useWebSocket('ws://localhost:8001/');

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          {isConnected ? 'Connected' : 'Disconnected'}
          <div>
          {data?data.id:0} | {data?data.timestamp:0} | 
          {data?toHexString(data.data):0}
          </div>
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

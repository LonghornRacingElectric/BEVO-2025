import React from "react";
// import './Dash.css';

import "bootstrap/dist/css/bootstrap.min.css";
import "./Dash.css";
import { Container, Row, Col } from "react-bootstrap";
import useWebSocket from "./websocket";

function Dash() {
  const { data, isConnected } = useWebSocket('ws://localhost:8001/');

  return (
    <div className="Dash">
      <Container>
        <Row>
          <Col>
            <div className="Tile">
                <div className="param">Lap:</div>
                <div className="val">{3}</div>
            </div>
          </Col>
          <Col>
            <div className="Tile">
                <div className="param">Speed:</div>
                <div className="val">{100}</div>
            </div>
          </Col>
          <Col>
          <div className="Tile">
                <div className="param"></div>
                <div className="val">D</div>
            </div>
          </Col>
        </Row>
        <Row>
        <Col>
            <div className="Tile">
                <div className="param">SOC:</div>
                <div className="val">{"82%"}</div>
            </div>
          </Col>
          <Col>
            <div className="Tile">
                <div className="param">param</div>
                <div className="val">{data?(data.timestamp/100).toFixed(2):0}</div>
            </div>
          </Col>
          <Col>
          <div className="Tile">
                <div className="param">param</div>
                <div className="val">{"FF"}</div>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default Dash;

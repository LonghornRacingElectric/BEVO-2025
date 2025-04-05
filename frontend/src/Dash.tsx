import React, { useEffect, useState } from "react";
// import './Dash.css';

import "bootstrap/dist/css/bootstrap.min.css";
import "./Dash.css";
import StatItem from "./StatItem";
import { Container, Row, Col } from "react-bootstrap";
import useWebSocket from "./websocket";
import Battery from "./Battery";
import Speedometer from "./Speedometer";

function Dash() {
  const { data, isConnected } = useWebSocket('ws://localhost:8001/');
  const [charge, setCharge] = useState(100);
  const [draw, setDraw] = useState(0);
  const [speed, setSpeed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCharge(prevCharge => (prevCharge > 0 ? prevCharge - 1 : 0))
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setDraw((prevDraw) => (prevDraw < 100 ? prevDraw + 1 : 0));
    }, 100);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setSpeed(prevSpeed => (prevSpeed <100 ? prevSpeed + 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [])

  return (
    <Container fluid className="Dash">
      <Row className="justify-content-center text-center">
        <Col xs={6} className="left">
          <Speedometer progress={draw} size={400} strokeWidth={20}/>
        </Col>
        
        <Col xs={4} className="center">
          <StatItem label="Speed" value={speed} className="large-stat" />
          <StatItem label="Power Draw" value="73 kW" />
        </Col>

        <Col xs={2} className="right">
          <Battery charge={charge}/>
        </Col>
      </Row>

      {/* <div className="bottom-metric">
        <StatItem label="Song Playing" color="#bf5700" value="TEXAS FIGHT" />
      </div> */}
    </Container>
  );
}

export default Dash;

import React, { useEffect, useState, useCallback } from "react";
// import './Dash.css';

import "bootstrap/dist/css/bootstrap.min.css";
import "./Dash.css";
import StatItem from "./StatItem";
import { Container, Row, Col } from "react-bootstrap";
import useWebSocket from "./websocket";
import Battery from "./Battery";
import Speedometer from "./Speedometer";
import ShutdownCircuitScreen from "./ShutdownCircuitScreen";

function Dash() {
  const { data, isConnected } = useWebSocket("ws://localhost:8001/");
  const [charge, setCharge] = useState(100);
  const [draw, setDraw] = useState(0);
  const [speed, setSpeed] = useState(0);
  const [packSoc, setPackSoc] = useState(0);
  const [maxCellTemp, setMaxCellTemp] = useState(0);
  const [showShutdown, setShowShutdown] = useState(false);

  // Listen for Enter key to toggle screens
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Enter") setShowShutdown((s) => !s);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (data?.timestamp !== undefined) {
      setDraw((data.timestamp / 10) % 100);
    } else {
      setDraw(0);
    }
  }, [data?.timestamp]);

  useEffect(() => {
    // Update speed from wheel speed data
    if (data?.data?.dynamics?.flw_speed !== undefined) {
      setSpeed(Math.round(data.data.dynamics.flw_speed));
    } else {
      setSpeed(0);
    }
  }, [data?.data?.dynamics?.flw_speed]);

  useEffect(() => {
    if (data?.data?.pack?.hv_soc !== undefined) {
      const soc = Math.round(data.data.pack.hv_soc);
      setPackSoc(soc);
      setCharge(soc); // Set charge to packSoc
    } else {
      setPackSoc(0);
      setCharge(0);
    }
  }, [data?.data?.pack?.hv_soc]);

  useEffect(() => {
    // Update max cell temp from battery data
    if (data?.data?.pack?.avg_cell_temp !== undefined) {
      setMaxCellTemp(Math.round(data.data.pack.avg_cell_temp));
    } else if (
      data?.data?.pack?.cell_top_temp !== undefined &&
      data?.data?.pack?.cell_bottom_temp !== undefined
    ) {
      setMaxCellTemp(
        Math.max(
          Math.round(data.data.pack.cell_top_temp),
          Math.round(data.data.pack.cell_bottom_temp)
        )
      );
    } else {
      setMaxCellTemp(0);
    }
  }, [
    data?.data?.pack?.avg_cell_temp,
    data?.data?.pack?.cell_top_temp,
    data?.data?.pack?.cell_bottom_temp,
  ]);

  // Gather shutdown legs 1-12 from telemetry
  const shutdownLegs = Array.from({ length: 12 }, (_, i) => {
    return !!data?.data?.diagnostics_low?.[`shutdown_leg${i + 1}`];
  });

  if (showShutdown) {
    return <ShutdownCircuitScreen shutdownLegs={shutdownLegs} />;
  }

  return (
    <Container fluid className="Dash">
      <Row className="justify-content-center text-center">
        <Col xs={6} className="left">
          <Speedometer progress={draw} size={400} strokeWidth={20} />
        </Col>

        <Col xs={4} className="center">
          <StatItem label="Speed" value={`${speed}`} className="large-stat" />
          <StatItem label="Pack SoC" value={`${packSoc}%`} />
          <StatItem label="Max Cell Temp" value={`${maxCellTemp}°C`} />
        </Col>

        <Col xs={2} className="right">
          <Battery charge={charge} />
        </Col>
      </Row>

      {/* <div className="bottom-metric">
        <StatItem label="Song Playing" color="#bf5700" value="TEXAS FIGHT" />
      </div> */}
    </Container>
  );
}

export default Dash;

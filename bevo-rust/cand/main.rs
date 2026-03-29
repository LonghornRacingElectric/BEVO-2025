/// cand — CAN daemon for Angelique
///
/// Reads CAN frames from the bus (or a UDP mock socket), decodes them into the
/// `AngeliqueSensorData` protobuf, and serves the serialised message to any
/// connected Unix-socket clients (e.g. `publishd`) at a configurable rate.
///
/// Environment variables:
///   CAND_USE_MOCK=1            – Use the UDP mock socket instead of a real CAN bus.
///   CAND_CAN_INTERFACE=<iface> – CAN interface name (default: "can0").
///   CAND_PUBLISH_HZ=<hz>       – Publish rate in Hz (default: 100).

use anyhow::Result;
use prost::Message;
use socketcan::{CanSocket, EmbeddedFrame, Id, Socket};
use std::collections::HashMap;
use std::io::Write;
use std::net::UdpSocket;
use std::os::unix::net::{UnixListener, UnixStream};
use std::path::Path;
use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use sensor_proto::proto::angelique::AngeliqueSensorData;
use sensor_proto::set_vec_index_f32;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/// UDP address used for the mock CAN source.
const MOCK_ADDR: &str = "127.0.0.1:5005";
/// Unix socket path for IPC with publishd / dashd.
const SOCKET_PATH: &str = "/tmp/BEVO_cand.sock";
/// Semaphore written by publishd when it has determined the initial packet_id.
const STARTUP_SEMAPHORE_PATH: &str = "/tmp/BEVO_publishd_ready";
/// Default real CAN interface.
const CAN_INTERFACE: &str = "can0";
/// Default IPC publish rate.
const DEFAULT_PUBLISH_HZ: u64 = 100;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

#[derive(Debug)]
struct RawCanMessage {
    id: u32,
    payload: Vec<u8>,
}

// ---------------------------------------------------------------------------
// Cell aggregator
// ---------------------------------------------------------------------------

/// Mirrors the Python `CellDataAggregator`.
///
/// Accumulates 4-value uint16 frames from CAN IDs in the cell voltage
/// (0x370–0x392) and temperature (0x470–0x486) ranges, then exposes the
/// full aggregated list and a running average.
struct CellAggregator {
    voltages: HashMap<u32, [u16; 4]>,
    temperatures: HashMap<u32, [u16; 4]>,
}

impl CellAggregator {
    fn new() -> Self {
        Self {
            voltages: HashMap::new(),
            temperatures: HashMap::new(),
        }
    }

    /// Parse the first 8 bytes of a CAN payload into four unsigned 16-bit
    /// little-endian values.
    fn parse_4xu16(payload: &[u8]) -> Option<[u16; 4]> {
        if payload.len() < 8 {
            return None;
        }
        Some([
            u16::from_le_bytes([payload[0], payload[1]]),
            u16::from_le_bytes([payload[2], payload[3]]),
            u16::from_le_bytes([payload[4], payload[5]]),
            u16::from_le_bytes([payload[6], payload[7]]),
        ])
    }

    /// Process a voltage frame (0x370–0x392).
    ///
    /// Returns `(all_voltages_in_volts, average_voltage)` using all frames
    /// received so far.
    fn process_voltage(&mut self, can_id: u32, payload: &[u8]) -> Option<(Vec<f32>, f32)> {
        let vals = Self::parse_4xu16(payload)?;
        self.voltages.insert(can_id, vals);

        let all: Vec<f32> = self
            .voltages
            .values()
            .flat_map(|v| v.iter().map(|&x| x as f32 * 0.0001))
            .collect();

        let avg = if all.is_empty() {
            0.0
        } else {
            all.iter().sum::<f32>() / all.len() as f32
        };
        Some((all, avg))
    }

    /// Process a temperature frame (0x470–0x486).
    ///
    /// Returns `(all_temps_in_celsius, average_temp)` using all frames
    /// received so far.  Temperatures are stored as integers (truncated).
    fn process_temperature(&mut self, can_id: u32, payload: &[u8]) -> Option<(Vec<i32>, f32)> {
        let vals = Self::parse_4xu16(payload)?;
        self.temperatures.insert(can_id, vals);

        let all_temps: Vec<i32> = self
            .temperatures
            .values()
            .flat_map(|v| v.iter().map(|&x| (x as f32 * 0.1) as i32))
            .collect();

        let avg = if all_temps.is_empty() {
            0.0
        } else {
            all_temps.iter().sum::<i32>() as f32 / all_temps.len() as f32
        };
        Some((all_temps, avg))
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

fn main() -> Result<()> {
    let use_mock = matches!(
        std::env::var("CAND_USE_MOCK")
            .ok()
            .as_deref()
            .map(|v| v.to_ascii_lowercase()),
        Some(v) if v == "1" || v == "true" || v == "yes"
    );
    let can_interface =
        std::env::var("CAND_CAN_INTERFACE").unwrap_or_else(|_| CAN_INTERFACE.to_string());
    let publish_hz = std::env::var("CAND_PUBLISH_HZ")
        .ok()
        .and_then(|v| v.parse::<u64>().ok())
        .filter(|&v| v > 0)
        .unwrap_or(DEFAULT_PUBLISH_HZ);

    // In real mode we wait for publishd to finish its MQTT handshake and write
    // the startup semaphore so we start from the correct packet_id.
    let initial_packet_id = if use_mock {
        1
    } else {
        wait_for_publishd_ready()?
    };

    let sensor_data_cache = Arc::new(Mutex::new(AngeliqueSensorData::default()));
    let (raw_tx, raw_rx) = mpsc::channel::<RawCanMessage>();

    // Thread 1 – CAN reader
    let can_iface_clone = can_interface.clone();
    let reader_tx = raw_tx;
    thread::spawn(move || {
        if let Err(e) = can_reader_loop(reader_tx, use_mock, can_iface_clone) {
            eprintln!("[CAND-CAN] fatal: {:?}", e);
        }
    });

    // Thread 2 – frame decoder / proto updater
    let processing_cache = Arc::clone(&sensor_data_cache);
    thread::spawn(move || {
        can_processing_loop(processing_cache, raw_rx);
    });

    // Thread 3 – IPC server (sends proto to publishd / dashd)
    let ipc_cache = Arc::clone(&sensor_data_cache);
    thread::spawn(move || {
        if let Err(e) = ipc_server_loop(ipc_cache, publish_hz, initial_packet_id) {
            eprintln!("[CAND-IPC] fatal: {:?}", e);
        }
    });

    if use_mock {
        println!("[CAND] started in MOCK mode ({}) @ {} Hz", MOCK_ADDR, publish_hz);
    } else {
        println!(
            "[CAND] started in REAL mode ({}) @ {} Hz",
            can_interface, publish_hz
        );
    }

    loop {
        thread::park();
    }
}

// ---------------------------------------------------------------------------
// Startup semaphore
// ---------------------------------------------------------------------------

/// Block until `publishd` writes its startup semaphore, then return the
/// initial packet_id it determined during the MQTT handshake.
fn wait_for_publishd_ready() -> Result<u64> {
    println!(
        "[CAND] waiting for publishd semaphore at {}",
        STARTUP_SEMAPHORE_PATH
    );
    loop {
        if Path::new(STARTUP_SEMAPHORE_PATH).exists() {
            if let Ok(contents) = std::fs::read_to_string(STARTUP_SEMAPHORE_PATH) {
                if let Ok(packet_id) = contents.trim().parse::<u64>() {
                    println!("[CAND] publishd ready; starting from packet_id={}", packet_id);
                    return Ok(packet_id.max(1));
                }
            }
        }
        thread::sleep(Duration::from_millis(100));
    }
}

// ---------------------------------------------------------------------------
// CAN reader loop
// ---------------------------------------------------------------------------

/// Continuously read CAN frames from a real SocketCAN interface or a UDP mock
/// socket, forwarding each frame as a `RawCanMessage` to the processing thread.
fn can_reader_loop(
    raw_tx: Sender<RawCanMessage>,
    use_mock: bool,
    can_interface: String,
) -> Result<()> {
    if use_mock {
        // Each UDP datagram is 12 bytes: 4-byte little-endian CAN ID + 8-byte payload.
        let socket = UdpSocket::bind(MOCK_ADDR)?;
        let mut buf = [0u8; 12];
        loop {
            socket.recv_from(&mut buf)?;
            let id = u32::from_le_bytes(buf[0..4].try_into().unwrap());
            let payload = buf[4..12].to_vec();
            if raw_tx.send(RawCanMessage { id, payload }).is_err() {
                return Ok(());
            }
        }
    } else {
        let socket = CanSocket::open(&can_interface)?;
        loop {
            let frame = socket.read_frame()?;
            if let Id::Standard(id) = frame.id() {
                let payload = frame.data().to_vec();
                if raw_tx
                    .send(RawCanMessage {
                        id: id.as_raw() as u32,
                        payload,
                    })
                    .is_err()
                {
                    return Ok(());
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// CAN processing loop
// ---------------------------------------------------------------------------

/// Decode CAN frames and update the shared `AngeliqueSensorData` cache.
fn can_processing_loop(
    data_cache: Arc<Mutex<AngeliqueSensorData>>,
    raw_rx: Receiver<RawCanMessage>,
) {
    let mut cell_agg = CellAggregator::new();
    while let Ok(msg) = raw_rx.recv() {
        let mut locked = data_cache.lock().unwrap();
        process_can_frame(&mut locked, msg.id, &msg.payload, &mut cell_agg);
    }
}

// ---------------------------------------------------------------------------
// CAN frame decoder
// ---------------------------------------------------------------------------

/// Translate one CAN frame into protobuf field updates.
///
/// Mirrors the Python `CAN_MAPPING` in `telemd/core/field_mappings.py` and the
/// `CellDataAggregator` logic.  Field number comments use the symbolic names
/// from `telemd/core/angelique_can.json`.
fn process_can_frame(
    data: &mut AngeliqueSensorData,
    can_id: u32,
    payload: &[u8],
    cell_agg: &mut CellAggregator,
) {
    // --- Cell voltages: HVC_VCU_CELL_VOLTAGES_START(0x370) – HVC_VCU_CELL_VOLTAGES_END(0x392) ---
    if (0x370..=0x392).contains(&can_id) {
        if let Some((all_v, avg_v)) = cell_agg.process_voltage(can_id, payload) {
            data.diagnostics
                .get_or_insert_with(Default::default)
                .cells_v = all_v;
            data.pack.get_or_insert_with(Default::default).avg_cell_v = avg_v;
        }
        return;
    }

    // --- Cell temperatures: HVC_VCU_CELL_TEMPS_START(0x470) – HVC_VCU_CELL_TEMPS_END(0x486) ---
    if (0x470..=0x486).contains(&can_id) {
        if let Some((all_t, avg_t)) = cell_agg.process_temperature(can_id, payload) {
            data.thermal
                .get_or_insert_with(Default::default)
                .cells_temp = all_t;
            data.pack
                .get_or_insert_with(Default::default)
                .avg_cell_temp = avg_t;
        }
        return;
    }

    match can_id {
        // INV_TEMP1_DATA – inverter temperature (mean of three signed 16-bit values, bytes 0-5)
        0x0A0 => {
            if payload.len() >= 6 {
                let v0 = i16::from_le_bytes([payload[0], payload[1]]) as f32;
                let v1 = i16::from_le_bytes([payload[2], payload[3]]) as f32;
                let v2 = i16::from_le_bytes([payload[4], payload[5]]) as f32;
                let mean = (v0 + v1 + v2) / 3.0;
                data.thermal
                    .get_or_insert_with(Default::default)
                    .inverter_temp = mean as i32;
            }
        }

        // INV_TEMP3_DATA – motor temperature (signed 16-bit, bytes 4-5, ×0.1 → °C)
        0x0A2 => {
            if payload.len() >= 6 {
                let v = i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.1;
                data.thermal
                    .get_or_insert_with(Default::default)
                    .motor_temp = v as i32;
            }
        }

        // INV_MOTOR_POSITIONS – motor RPM (signed 16-bit, bytes 2-3)
        0x0A5 => {
            if payload.len() >= 4 {
                let rpm = i16::from_le_bytes([payload[2], payload[3]]) as i32;
                data.dynamics
                    .get_or_insert_with(Default::default)
                    .inverter_rpm = rpm;
            }
        }

        // INV_CURRENT – inverter DC current (signed 16-bit, bytes 6-7, ×0.1 → A)
        0x0A6 => {
            if payload.len() >= 8 {
                let v = i16::from_le_bytes([payload[6], payload[7]]) as f32 * 0.1;
                data.dynamics
                    .get_or_insert_with(Default::default)
                    .inverter_c = v;
            }
        }

        // INV_VOLTAGE – inverter DC voltage (signed 16-bit, bytes 0-1, ×0.1 → V)
        0x0A7 => {
            if payload.len() >= 2 {
                let v = i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.1;
                data.dynamics
                    .get_or_insert_with(Default::default)
                    .inverter_v = v;
            }
        }

        // VCU_INV_COMMAND – torque request (bytes 0-1) and actual torque (bytes 2-3),
        //                   both signed 16-bit ×0.1 → N·m
        0x0C0 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                dyn_.torque_request =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.1;
            }
            if payload.len() >= 4 {
                dyn_.inverter_torque =
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.1;
            }
        }

        // HVC_VCU_PACK_STATUS
        //   bytes 0-1: HV pack voltage   (uint16 ×0.01 → V)
        //   bytes 2-3: HV pack current   (int16  ×0.01 → A)
        //   bytes 4-5: HV state of charge (uint16 ×0.01 → %)
        //   bytes 6-7: pack temp max/min  (uint8 each, no proto field – skipped)
        0x220 => {
            if payload.len() >= 2 {
                data.pack.get_or_insert_with(Default::default).hv_pack_v =
                    u16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01;
            }
            if payload.len() >= 4 {
                data.pack.get_or_insert_with(Default::default).hv_c =
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01;
            }
            if payload.len() >= 6 {
                data.diagnostics
                    .get_or_insert_with(Default::default)
                    .hv_charge_state =
                    u16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01;
            }
        }

        // HVC_VCU_CONTACTOR_STATUS – contactor state (uint8, byte 0)
        0x420 => {
            if !payload.is_empty() {
                data.pack
                    .get_or_insert_with(Default::default)
                    .contactor_state = payload[0] as i32;
            }
        }

        // PDU_VCU_THERMAL – cooling system
        //   bytes 0-1: flow rate          (int16 ×0.1 → L/min, stored as i32)
        //   byte  2:   water motor temp   (int8  → °C)
        //   byte  3:   water inverter temp (int8 → °C)
        //   byte  4:   water radiator temp (int8 → °C)
        //   byte  5:   radiator fan RPM   (int8, stored as i64)
        0x230 => {
            let therm = data.thermal.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                therm.flow_rate =
                    (i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.1) as i32;
            }
            if payload.len() >= 3 {
                therm.water_motor_temp = payload[2] as i8 as i32;
            }
            if payload.len() >= 4 {
                therm.water_inverter_temp = payload[3] as i8 as i32;
            }
            if payload.len() >= 5 {
                therm.water_rad_temp = payload[4] as i8 as i32;
            }
            if payload.len() >= 6 {
                therm.rad_fan_rpm = payload[5] as i8 as i64;
            }
        }

        // PDU_VCU_LVBAT – LV battery
        //   bytes 0-1: LV voltage    (int16 ×0.01 → V)
        //   bytes 2-3: LV SoC        (uint16 ×0.01 → %)
        //   bytes 4-5: LV current    (int16 ×0.01 → A)
        0x330 => {
            if payload.len() >= 2 {
                data.pack.get_or_insert_with(Default::default).lv_v =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01;
            }
            if payload.len() >= 4 {
                data.diagnostics
                    .get_or_insert_with(Default::default)
                    .lv_charge_state =
                    u16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01;
            }
            if payload.len() >= 6 {
                data.pack.get_or_insert_with(Default::default).lv_c =
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01;
            }
        }

        // Wheel speeds – all signed 16-bit ×0.0025 → m/s
        // UNSFR_VCU_MAGNET – front-right wheel speed
        0x340 => {
            if payload.len() >= 2 {
                data.dynamics.get_or_insert_with(Default::default).frw_speed =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.0025;
            }
        }
        // UNSFL_VCU_MAGNET – front-left wheel speed
        0x344 => {
            if payload.len() >= 2 {
                data.dynamics.get_or_insert_with(Default::default).flw_speed =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.0025;
            }
        }
        // UNSBR_VCU_MAGNET – back-right wheel speed
        0x348 => {
            if payload.len() >= 2 {
                data.dynamics.get_or_insert_with(Default::default).brw_speed =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.0025;
            }
        }
        // UNSBL_VCU_MAGNET – back-left wheel speed
        0x34C => {
            if payload.len() >= 2 {
                data.dynamics.get_or_insert_with(Default::default).blw_speed =
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.0025;
            }
        }

        // HVC_VCU_IMU_ACCEL – HVC body acceleration → body2_accel[0..2]
        // Each axis: signed 16-bit ×0.01 → g
        0x221 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.body2_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.body2_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.body2_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // HVC_VCU_IMU_GYRO – HVC gyro → body2_gyro[0..2]
        0x222 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.body2_gyro,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.body2_gyro,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.body2_gyro,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // PDU_VCU_IMU_ACCEL – PDU body acceleration → body3_accel[0..2]
        0x231 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.body3_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.body3_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.body3_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // PDU_VCU_IMU_GYRO – PDU gyro → body3_gyro[0..2]
        0x232 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.body3_gyro,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.body3_gyro,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.body3_gyro,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // UNSFR_VCU_IMU – front-right unsprung acceleration → frw_accel[0..2]
        0x341 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.frw_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.frw_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.frw_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // UNSFL_VCU_IMU – front-left unsprung acceleration → flw_accel[0..2]
        0x345 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.flw_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.flw_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.flw_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // UNSBR_VCU_IMU – back-right unsprung acceleration → brw_accel[0..2]
        0x349 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.brw_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.brw_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.brw_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // UNSBL_VCU_IMU – back-left unsprung acceleration → blw_accel[0..2]
        0x34D => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 2 {
                set_vec_index_f32(
                    &mut dyn_.blw_accel,
                    0,
                    i16::from_le_bytes([payload[0], payload[1]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 4 {
                set_vec_index_f32(
                    &mut dyn_.blw_accel,
                    1,
                    i16::from_le_bytes([payload[2], payload[3]]) as f32 * 0.01,
                );
            }
            if payload.len() >= 6 {
                set_vec_index_f32(
                    &mut dyn_.blw_accel,
                    2,
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01,
                );
            }
        }

        // GPS position
        //   bytes 0-3: latitude   (signed int32 ×1e-7 → °, stored as gps[1])
        //   bytes 4-7: longitude  (signed int32 ×1e-7 → °, stored as gps[0])
        //
        // Note: the proto field `dynamics.gps` maps to CSV columns
        // ["Longitude", "Latitude"] at indices [0, 1] respectively, matching
        // the Python CSV_PROTBUF_MAPPING convention.
        0x600 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 4 {
                let lat = i32::from_le_bytes([payload[0], payload[1], payload[2], payload[3]])
                    as f32
                    * 1e-7;
                set_vec_index_f32(&mut dyn_.gps, 1, lat);
            }
            if payload.len() >= 8 {
                let lon = i32::from_le_bytes([payload[4], payload[5], payload[6], payload[7]])
                    as f32
                    * 1e-7;
                set_vec_index_f32(&mut dyn_.gps, 0, lon);
            }
        }

        // GPS velocity and heading
        //   bytes 0-3: ground speed  (signed int32 ×0.001 → m/s)
        //   bytes 4-5: heading       (signed int16 ×0.01  → °)
        0x601 => {
            let dyn_ = data.dynamics.get_or_insert_with(Default::default);
            if payload.len() >= 4 {
                dyn_.gps_velocity =
                    i32::from_le_bytes([payload[0], payload[1], payload[2], payload[3]]) as f32
                        * 0.001;
            }
            if payload.len() >= 6 {
                dyn_.gps_heading =
                    i16::from_le_bytes([payload[4], payload[5]]) as f32 * 0.01;
            }
        }

        _ => {}
    }
}

// ---------------------------------------------------------------------------
// IPC server loop
// ---------------------------------------------------------------------------

/// Serialise the current proto snapshot at `publish_hz` and broadcast it to
/// all connected Unix-socket clients (length-prefixed with a 4-byte big-endian
/// frame length, identical to the lhre-2026 protocol).
fn ipc_server_loop(
    sensor_data: Arc<Mutex<AngeliqueSensorData>>,
    publish_hz: u64,
    initial_packet_id: u64,
) -> Result<()> {
    let _ = std::fs::remove_file(SOCKET_PATH);
    let listener = UnixListener::bind(SOCKET_PATH)?;
    let clients: Arc<Mutex<Vec<UnixStream>>> = Arc::new(Mutex::new(Vec::new()));
    let publish_interval = Duration::from_secs_f64(1.0 / publish_hz as f64);
    let mut next_packet_id = initial_packet_id.max(1);

    // Accept new clients in a background thread.
    let clients_accept = Arc::clone(&clients);
    thread::spawn(move || {
        for stream in listener.incoming() {
            if let Ok(s) = stream {
                clients_accept.lock().unwrap().push(s);
            }
        }
    });

    loop {
        // Stamp packet_id and wall-clock time into the proto.
        {
            let mut d = sensor_data.lock().unwrap();
            if next_packet_id > i64::MAX as u64 {
                eprintln!("[CAND] packet_id overflow: {} exceeds i64::MAX; clamping", next_packet_id);
            }
            d.packet_id = next_packet_id.min(i64::MAX as u64) as i64;
            d.time = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_millis() as i64;
        }

        let cycle_start = Instant::now();

        // Serialise.
        let mut buffer = Vec::new();
        {
            sensor_data.lock().unwrap().encode(&mut buffer).ok();
        }

        // Broadcast: 4-byte big-endian length then payload.
        let frame_len = (buffer.len() as u32).to_be_bytes();
        clients.lock().unwrap().retain_mut(|stream| {
            stream
                .write_all(&frame_len)
                .and_then(|_| stream.write_all(&buffer))
                .is_ok()
        });

        next_packet_id = next_packet_id.saturating_add(1);

        // Sleep for the remainder of the publish interval.
        let elapsed = cycle_start.elapsed();
        if elapsed < publish_interval {
            thread::sleep(publish_interval - elapsed);
        }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn make_proto() -> AngeliqueSensorData {
        AngeliqueSensorData::default()
    }

    fn dummy_agg() -> CellAggregator {
        CellAggregator::new()
    }

    #[test]
    fn test_inverter_rpm() {
        let mut data = make_proto();
        let payload: Vec<u8> = [0u8, 0u8, 0xE8u8, 0x03u8, 0u8, 0u8, 0u8, 0u8].to_vec(); // bytes 2-3 = 1000
        process_can_frame(&mut data, 0x0A5, &payload, &mut dummy_agg());
        assert_eq!(data.dynamics.unwrap().inverter_rpm, 1000);
    }

    #[test]
    fn test_inverter_v() {
        let mut data = make_proto();
        // 300.0 V → raw = 3000 = 0x0BB8 LE
        let mut payload = vec![0u8; 2];
        let raw: i16 = 3000;
        payload[0..2].copy_from_slice(&raw.to_le_bytes());
        process_can_frame(&mut data, 0x0A7, &payload, &mut dummy_agg());
        let v = data.dynamics.unwrap().inverter_v;
        assert!((v - 300.0).abs() < 1e-3, "expected 300.0, got {}", v);
    }

    #[test]
    fn test_torque_command() {
        let mut data = make_proto();
        let mut payload = vec![0u8; 4];
        let req: i16 = 200; // 20.0 N·m
        let actual: i16 = 150; // 15.0 N·m
        payload[0..2].copy_from_slice(&req.to_le_bytes());
        payload[2..4].copy_from_slice(&actual.to_le_bytes());
        process_can_frame(&mut data, 0x0C0, &payload, &mut dummy_agg());
        let dyn_ = data.dynamics.unwrap();
        assert!((dyn_.torque_request - 20.0).abs() < 1e-3);
        assert!((dyn_.inverter_torque - 15.0).abs() < 1e-3);
    }

    #[test]
    fn test_wheel_speeds() {
        let raw: i16 = 4000; // 4000 × 0.0025 = 10.0 m/s
        let payload: Vec<u8> = raw.to_le_bytes().to_vec();

        let cases: &[(u32, fn(&sensor_proto::proto::angelique::AngeliqueDynamics) -> f32)] = &[
            (0x340, |d| d.frw_speed),
            (0x344, |d| d.flw_speed),
            (0x348, |d| d.brw_speed),
            (0x34C, |d| d.blw_speed),
        ];
        for &(can_id, field_fn) in cases {
            let mut data = make_proto();
            process_can_frame(&mut data, can_id, &payload, &mut dummy_agg());
            let speed = field_fn(data.dynamics.as_ref().unwrap());
            assert!(
                (speed - 10.0).abs() < 1e-3,
                "CAN 0x{:03X}: expected 10.0 m/s, got {}",
                can_id,
                speed
            );
        }
    }

    #[test]
    fn test_cell_voltage_aggregation() {
        let mut data = make_proto();
        let mut agg = CellAggregator::new();
        // One frame with values 10000 each → 10000 × 0.0001 = 1.0 V each
        let payload: Vec<u8> = {
            let raw: u16 = 10000;
            let b = raw.to_le_bytes();
            vec![b[0], b[1], b[0], b[1], b[0], b[1], b[0], b[1]]
        };
        process_can_frame(&mut data, 0x370, &payload, &mut agg);
        let diag = data.diagnostics.unwrap();
        assert_eq!(diag.cells_v.len(), 4);
        for v in &diag.cells_v {
            assert!((v - 1.0).abs() < 1e-4, "expected 1.0 V, got {}", v);
        }
        let avg = data.pack.unwrap().avg_cell_v;
        assert!((avg - 1.0).abs() < 1e-4);
    }

    #[test]
    fn test_cell_temp_aggregation() {
        let mut data = make_proto();
        let mut agg = CellAggregator::new();
        // Raw value 250 → 250 × 0.1 = 25 °C
        let raw: u16 = 250;
        let b = raw.to_le_bytes();
        let payload = vec![b[0], b[1], b[0], b[1], b[0], b[1], b[0], b[1]];
        process_can_frame(&mut data, 0x470, &payload, &mut agg);
        let therm = data.thermal.unwrap();
        assert_eq!(therm.cells_temp.len(), 4);
        for t in &therm.cells_temp {
            assert_eq!(*t, 25, "expected 25 °C, got {}", t);
        }
    }

    #[test]
    fn test_hvc_imu_accel() {
        let mut data = make_proto();
        let mut payload = vec![0u8; 6];
        let ax: i16 = 100; // 1.0 g
        let ay: i16 = 200; // 2.0 g
        let az: i16 = -50; // -0.5 g
        payload[0..2].copy_from_slice(&ax.to_le_bytes());
        payload[2..4].copy_from_slice(&ay.to_le_bytes());
        payload[4..6].copy_from_slice(&az.to_le_bytes());
        process_can_frame(&mut data, 0x221, &payload, &mut dummy_agg());
        let accel = data.dynamics.unwrap().body2_accel;
        assert_eq!(accel.len(), 3);
        assert!((accel[0] - 1.0).abs() < 1e-3);
        assert!((accel[1] - 2.0).abs() < 1e-3);
        assert!((accel[2] - (-0.5)).abs() < 1e-3);
    }

    #[test]
    fn test_gps_position() {
        let mut data = make_proto();
        // Latitude 30.2849° N → raw = 302849000
        // Longitude -97.7341° W → raw = -977341000
        let lat_raw: i32 = 302_849_000;
        let lon_raw: i32 = -977_341_000_i32;
        let mut payload = vec![0u8; 8];
        payload[0..4].copy_from_slice(&lat_raw.to_le_bytes());
        payload[4..8].copy_from_slice(&lon_raw.to_le_bytes());
        process_can_frame(&mut data, 0x600, &payload, &mut dummy_agg());
        let gps = data.dynamics.unwrap().gps;
        assert_eq!(gps.len(), 2);
        // gps[0] = longitude, gps[1] = latitude
        assert!((gps[1] - 30.2849).abs() < 0.001, "lat: {}", gps[1]);
        assert!((gps[0] - (-97.7341)).abs() < 0.001, "lon: {}", gps[0]);
    }

    #[test]
    fn test_gps_velocity_heading() {
        let mut data = make_proto();
        // 5.0 m/s → raw = 5000; heading 90.0° → raw = 9000
        let v_raw: i32 = 5000i32;
        let h_raw: i16 = 9000i16;
        let mut payload = vec![0u8; 6];
        payload[0..4].copy_from_slice(&v_raw.to_le_bytes());
        payload[4..6].copy_from_slice(&h_raw.to_le_bytes());
        process_can_frame(&mut data, 0x601, &payload, &mut dummy_agg());
        let dyn_ = data.dynamics.unwrap();
        assert!((dyn_.gps_velocity - 5.0).abs() < 1e-3);
        assert!((dyn_.gps_heading - 90.0).abs() < 1e-3);
    }

    #[test]
    fn test_hv_pack_status() {
        let mut data = make_proto();
        // hv_pack_v = 400.0 V → raw 40000 uint16
        // hv_c = -50.0 A → raw -5000 int16
        // hv_charge_state = 80.0% → raw 8000 uint16
        let mut payload = vec![0u8; 6];
        payload[0..2].copy_from_slice(&(40000u16).to_le_bytes());
        payload[2..4].copy_from_slice(&(-5000i16).to_le_bytes());
        payload[4..6].copy_from_slice(&(8000u16).to_le_bytes());
        process_can_frame(&mut data, 0x220, &payload, &mut dummy_agg());
        let pack = data.pack.unwrap();
        assert!((pack.hv_pack_v - 400.0).abs() < 0.01);
        assert!((pack.hv_c - (-50.0)).abs() < 0.01);
        let diag = data.diagnostics.unwrap();
        assert!((diag.hv_charge_state - 80.0).abs() < 0.01);
    }

    #[test]
    fn test_inverter_temp_mean() {
        let mut data = make_proto();
        // Three int16 values: 30, 40, 50 → mean = 40
        let mut payload = vec![0u8; 6];
        payload[0..2].copy_from_slice(&(30i16).to_le_bytes());
        payload[2..4].copy_from_slice(&(40i16).to_le_bytes());
        payload[4..6].copy_from_slice(&(50i16).to_le_bytes());
        process_can_frame(&mut data, 0x0A0, &payload, &mut dummy_agg());
        assert_eq!(data.thermal.unwrap().inverter_temp, 40);
    }

    #[test]
    fn test_lv_bat() {
        let mut data = make_proto();
        // lv_v = 12.50 V → raw 1250; lv_soc = 75.00% → raw 7500 uint16; lv_c = 2.00 A → raw 200
        let mut payload = vec![0u8; 6];
        payload[0..2].copy_from_slice(&(1250i16).to_le_bytes());
        payload[2..4].copy_from_slice(&(7500u16).to_le_bytes());
        payload[4..6].copy_from_slice(&(200i16).to_le_bytes());
        process_can_frame(&mut data, 0x330, &payload, &mut dummy_agg());
        let pack = data.pack.unwrap();
        assert!((pack.lv_v - 12.5).abs() < 0.01);
        assert!((pack.lv_c - 2.0).abs() < 0.01);
        let diag = data.diagnostics.unwrap();
        assert!((diag.lv_charge_state - 75.0).abs() < 0.01);
    }
}

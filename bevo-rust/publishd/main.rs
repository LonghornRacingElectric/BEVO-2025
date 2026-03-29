/// publishd — MQTT publish daemon for Angelique
///
/// Connects to the MQTT broker as "BEVO-Angelique", optionally synchronises the
/// initial packet_id with the server, then writes a startup semaphore file so
/// that `cand` knows which packet_id to start from.  After startup it reads
/// length-prefixed protobuf frames from the Unix socket written by `cand` and
/// forwards them to the MQTT broker on the "angelique" topic.
///
/// Environment variables:
///   PUBLISHD_MQTT_HOST=<host>               – Broker hostname/IP (default: 192.168.1.109).
///   PUBLISHD_MQTT_PORT=<port>               – Broker port (default: 1883).
///   PUBLISHD_MQTT_CLIENT_ID=<id>            – MQTT client ID (default: "BEVO-Angelique").
///   PUBLISHD_CLIENT_ANNOUNCE_ID=<id>        – Payload sent on client-connections (default: MQTT_CLIENT_ID).
///   PUBLISHD_REQUIRE_SERVER_PACKET_ID=1     – Block until the server returns a packet_id.

use anyhow::Result;
use rumqttc::{Client, Event, Incoming, MqttOptions, QoS};
use serde_json::Value;
use std::io::Read;
use std::os::unix::net::UnixStream;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::mpsc::{self, SyncSender, TrySendError};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const IPC_SOCKET_PATH: &str = "/tmp/BEVO_cand.sock";
const STARTUP_SEMAPHORE_PATH: &str = "/tmp/BEVO_publishd_ready";

const MQTT_HOST: &str = "192.168.1.109";
const MQTT_PORT: u16 = 1883;
const MQTT_CLIENT_ID: &str = "BEVO-Angelique";
const MQTT_ANNOUNCE_CLIENT_ID: &str = "BEVO-Angelique";
const MQTT_TOPIC_PUBLISH: &str = "angelique";
const MQTT_TOPIC_SERVER_COMMUNICATION: &str = "server-communication";
const MQTT_TOPIC_CLIENT_CONNECTIONS: &str = "client-connections";

/// Capacity of the outbound serialised-bytes queue.  Frames are dropped (with
/// a warning) when the queue is full, preventing back-pressure on the encoder.
const MQTT_OUTBOUND_QUEUE_CAPACITY: usize = 2048;
const INITIAL_PACKET_ID_REQUEST_TIMEOUT_SECS: u64 = 12;
const INITIAL_PACKET_ID_REQUEST_INTERVAL_MS: u64 = 500;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn env_or_default(name: &str, default: &str) -> String {
    std::env::var(name).unwrap_or_else(|_| default.to_string())
}

/// Returns `true` if `PUBLISHD_REQUIRE_SERVER_PACKET_ID` is set to a truthy value.
fn should_require_server_packet_id() -> bool {
    matches!(
        std::env::var("PUBLISHD_REQUIRE_SERVER_PACKET_ID")
            .ok()
            .as_deref()
            .map(|v| v.to_ascii_lowercase()),
        Some(v) if v == "1" || v == "true" || v == "yes"
    )
}

fn get_announce_client_id(client_id: &str) -> String {
    env_or_default("PUBLISHD_CLIENT_ANNOUNCE_ID", client_id)
}

// ---------------------------------------------------------------------------
// MqttClient
// ---------------------------------------------------------------------------

struct MqttClient {
    client: Arc<Mutex<Client>>,
    outbound_tx: SyncSender<Vec<u8>>,
    packet_id: Arc<AtomicU64>,
    /// Set to `true` once a `packet_id` has been received from the server.
    initialized: Arc<std::sync::atomic::AtomicBool>,
}

impl MqttClient {
    fn new(host: &str, port: u16, client_id: &str) -> Result<Self> {
        let mut mqtt_options = MqttOptions::new(client_id, host, port);
        mqtt_options.set_keep_alive(Duration::from_secs(20));

        let (client, mut connection) = Client::new(mqtt_options, 64);
        let client = Arc::new(Mutex::new(client));
        let packet_id = Arc::new(AtomicU64::new(0));
        let initialized = Arc::new(std::sync::atomic::AtomicBool::new(false));
        let (outbound_tx, outbound_rx) = mpsc::sync_channel::<Vec<u8>>(MQTT_OUTBOUND_QUEUE_CAPACITY);

        // Subscribe to the server-communication topic.
        {
            let locked = client.lock().expect("mqtt client mutex poisoned");
            locked.subscribe(MQTT_TOPIC_SERVER_COMMUNICATION, QoS::AtMostOnce)?;
        }

        // Outbound publish thread: drains the channel and forwards to broker.
        let publish_client = Arc::clone(&client);
        thread::spawn(move || {
            while let Ok(payload) = outbound_rx.recv() {
                let result = publish_client
                    .lock()
                    .expect("mqtt client mutex poisoned")
                    .publish(MQTT_TOPIC_PUBLISH, QoS::AtMostOnce, false, payload);
                if let Err(e) = result {
                    eprintln!("[PUBLISHD] mqtt publish error: {e}");
                }
            }
        });

        // Event loop thread: drives the MQTT connection and handles incoming messages.
        let packet_id_loop = Arc::clone(&packet_id);
        let initialized_loop = Arc::clone(&initialized);
        thread::spawn(move || {
            for event in connection.iter() {
                match event {
                    Ok(Event::Incoming(Incoming::Publish(p))) => {
                        if p.topic == MQTT_TOPIC_SERVER_COMMUNICATION {
                            handle_server_message(&packet_id_loop, &initialized_loop, &p.payload);
                        }
                    }
                    Ok(Event::Incoming(Incoming::Disconnect)) => break,
                    Ok(_) => {}
                    Err(e) => {
                        eprintln!("[PUBLISHD] mqtt connection error: {e}");
                        thread::sleep(Duration::from_millis(200));
                    }
                }
            }
        });

        Ok(Self {
            client,
            outbound_tx,
            packet_id,
            initialized,
        })
    }

    /// Enqueue a serialised protobuf payload for publishing.  Returns an error
    /// only if the channel has been disconnected (fatal).
    fn publish_sensor_bytes(&self, payload: &[u8]) -> Result<()> {
        match self.outbound_tx.try_send(payload.to_vec()) {
            Ok(_) => Ok(()),
            Err(TrySendError::Full(_)) => {
                eprintln!("[PUBLISHD] outbound queue full; dropping frame");
                Ok(())
            }
            Err(TrySendError::Disconnected(_)) => {
                anyhow::bail!("[PUBLISHD] outbound queue disconnected")
            }
        }
    }

    fn packet_id(&self) -> u64 {
        self.packet_id.load(Ordering::Relaxed)
    }

    /// Poll the broker by re-publishing the announce client_id until the server
    /// responds with a `packet_id`, or the timeout elapses.
    fn request_initial_packet_id_or_default(&self, announce_client_id: &str, default: u64) -> u64 {
        let deadline =
            Instant::now() + Duration::from_secs(INITIAL_PACKET_ID_REQUEST_TIMEOUT_SECS);

        while Instant::now() < deadline {
            if self.initialized.load(Ordering::Relaxed) {
                return self.packet_id();
            }

            println!(
                "[PUBLISHD] requesting packet_id on '{}' with client_id '{}'",
                MQTT_TOPIC_CLIENT_CONNECTIONS, announce_client_id
            );

            let result = self
                .client
                .lock()
                .expect("mqtt client mutex poisoned")
                .publish(
                    MQTT_TOPIC_CLIENT_CONNECTIONS,
                    QoS::AtMostOnce,
                    false,
                    announce_client_id.as_bytes().to_vec(),
                );
            if let Err(e) = result {
                eprintln!("[PUBLISHD] packet_id request publish error: {e}");
            }

            thread::sleep(Duration::from_millis(INITIAL_PACKET_ID_REQUEST_INTERVAL_MS));
        }

        eprintln!(
            "[PUBLISHD] no server packet_id within {}s; defaulting to {}",
            INITIAL_PACKET_ID_REQUEST_TIMEOUT_SECS, default
        );
        default
    }
}

// ---------------------------------------------------------------------------
// Server message handler
// ---------------------------------------------------------------------------

/// Parse an incoming `server-communication` payload and update `packet_id` if
/// the message contains a newer value.
fn handle_server_message(
    packet_id: &Arc<AtomicU64>,
    initialized: &Arc<std::sync::atomic::AtomicBool>,
    payload: &[u8],
) {
    let Ok(message) = serde_json::from_slice::<Value>(payload) else {
        return;
    };

    if let Some(server_id) = message.get("packet_id").and_then(Value::as_u64) {
        let candidate = server_id.saturating_add(1);
        loop {
            let current = packet_id.load(Ordering::Relaxed);
            if candidate <= current {
                break;
            }
            if packet_id
                .compare_exchange(current, candidate, Ordering::Relaxed, Ordering::Relaxed)
                .is_ok()
            {
                initialized.store(true, Ordering::Relaxed);
                println!(
                    "[PUBLISHD] updated packet_id to {} from server-communication",
                    candidate
                );
                break;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Startup semaphore
// ---------------------------------------------------------------------------

/// Write the initial packet_id to the semaphore file atomically so that `cand`
/// can read it and start from the correct sequence number.
fn write_startup_semaphore(packet_id: u64) -> Result<()> {
    let tmp = format!("{}.tmp", STARTUP_SEMAPHORE_PATH);
    std::fs::write(&tmp, packet_id.to_string())?;
    std::fs::rename(tmp, STARTUP_SEMAPHORE_PATH)?;
    Ok(())
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

fn main() -> Result<()> {
    // Remove any stale semaphore from a previous run.
    let _ = std::fs::remove_file(STARTUP_SEMAPHORE_PATH);

    let mqtt_host = env_or_default("PUBLISHD_MQTT_HOST", MQTT_HOST);
    let mqtt_port = std::env::var("PUBLISHD_MQTT_PORT")
        .ok()
        .and_then(|v| v.parse::<u16>().ok())
        .unwrap_or(MQTT_PORT);
    let mqtt_client_id = env_or_default("PUBLISHD_MQTT_CLIENT_ID", MQTT_CLIENT_ID);
    let announce_client_id = get_announce_client_id(MQTT_ANNOUNCE_CLIENT_ID);

    let mqtt = MqttClient::new(&mqtt_host, mqtt_port, &mqtt_client_id)?;
    println!(
        "[PUBLISHD] connected to {}:{} as '{}'",
        mqtt_host, mqtt_port, mqtt_client_id
    );

    let require_server_packet_id = should_require_server_packet_id();
    println!(
        "[PUBLISHD] require_server_packet_id={} \
         (set PUBLISHD_REQUIRE_SERVER_PACKET_ID=1 to enable handshake)",
        require_server_packet_id
    );

    let initial_packet_id = if require_server_packet_id {
        println!(
            "[PUBLISHD] requesting initial packet_id with announce client_id '{}'",
            announce_client_id
        );
        mqtt.request_initial_packet_id_or_default(&announce_client_id, 1)
    } else {
        1
    };

    write_startup_semaphore(initial_packet_id)?;
    println!(
        "[PUBLISHD] startup complete; initial packet_id={}",
        initial_packet_id
    );

    // Main loop: connect to the cand Unix socket and forward frames to MQTT.
    loop {
        match UnixStream::connect(IPC_SOCKET_PATH) {
            Ok(mut stream) => {
                println!("[PUBLISHD] connected to cand IPC socket");
                loop {
                    // Each message is prefixed with a 4-byte big-endian length.
                    let mut len_buf = [0u8; 4];
                    if stream.read_exact(&mut len_buf).is_err() {
                        break;
                    }
                    let msg_len = u32::from_be_bytes(len_buf) as usize;

                    let mut msg_buf = vec![0u8; msg_len];
                    if stream.read_exact(&mut msg_buf).is_err() {
                        break;
                    }

                    if let Err(e) = mqtt.publish_sensor_bytes(&msg_buf) {
                        eprintln!("[PUBLISHD] publish error: {e}");
                    }
                }
                eprintln!("[PUBLISHD] cand IPC connection lost; reconnecting…");
            }
            Err(_) => {
                // cand not yet up; wait briefly and retry.
                let _ = mqtt.packet_id(); // keep event loop ticking
                thread::sleep(Duration::from_millis(500));
            }
        }
    }
}

use std::env;
use std::path::PathBuf;

fn main() {
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string());
    let proto_path = PathBuf::from(&manifest_dir)
        .join("proto/template.proto")
        .to_string_lossy()
        .to_string();
    let proto_dir = PathBuf::from(&manifest_dir)
        .join("proto")
        .to_string_lossy()
        .to_string();

    let mut config = prost_build::Config::new();
    config.include_file("_.rs");
    config
        .compile_protos(&[proto_path], &[proto_dir])
        .unwrap();
}

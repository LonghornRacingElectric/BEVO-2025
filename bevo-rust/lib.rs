#![recursion_limit = "1024"]

/// Compiled protobuf types for the Angelique sensor data schema.
pub mod proto {
    include!(concat!(env!("OUT_DIR"), "/_.rs"));
}

/// Resize a `Vec<f32>` to fit index `i` and assign `val`.
pub fn set_vec_index_f32(v: &mut Vec<f32>, i: usize, val: f32) {
    if v.len() <= i {
        v.resize(i + 1, 0.0);
    }
    v[i] = val;
}

/// Resize a `Vec<i32>` to fit index `i` and assign `val`.
pub fn set_vec_index_i32(v: &mut Vec<i32>, i: usize, val: i32) {
    if v.len() <= i {
        v.resize(i + 1, 0);
    }
    v[i] = val;
}

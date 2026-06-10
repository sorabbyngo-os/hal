//! hal — Sorabbyngo OS Hardware Abstraction Layer

mod sensors;
mod events;
mod camera;
mod audio;
mod location;
mod power;
mod ambient;

use anyhow::Result;
use tracing::info;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    info!("hal starting");
    Ok(())
}

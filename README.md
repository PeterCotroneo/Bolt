# Bolt

Watch **live lightning strikes** on your map. Bolt streams real-time lightning
into QGIS and shows strikes flash onto the map as they happen, then fade over a
minute — track your current map view, or draw an area to watch. Live only; no
history replay.

Bolt is one of four sibling plugins built on the same live-tracking engine — a
pluggable data-source layer, a moving/expiring-point map layer, clustering and
identify — covering **sea, sky, space and storms**:

- [Wake](https://github.com/PeterCotroneo/Wake) — marine vessels (AIS)
- [Contrail](https://github.com/PeterCotroneo/Contrail) — aircraft (ADS-B)
- [Zenith](https://github.com/PeterCotroneo/Zenith) — satellites (SGP4)
- **Bolt** — lightning (this one)

## Features

- **Real-time and global** — strikes appear as they are detected, anywhere on Earth.
- **Free and keyless** — no account, no API key.
- **Age-coloured** — each strike flashes bright, then fades yellow → orange → dim over about a minute, so the map shows where storms are active *right now*.
- **Area-based** — watch your map view or a drawn box; strikes outside it are dropped.
- **Cluster badges** — busy storm cells collapse into a counted marker; zoom in and they fan out.
- **Identify** a strike for its time and the number of detectors that reported it.
- **No extra dependencies** — uses Qt's built-in WebSocket, so it installs cleanly from the QGIS plugin repository.

## Data source and attribution

Lightning comes from the **[Blitzortung.org](https://www.blitzortung.org/)**
volunteer lightning-detection network — a community of operators running
receivers around the world. The data is **free for non-commercial use**, and
Bolt keeps the attribution visible in its panel.

Please respect Blitzortung's community: this is volunteer-run infrastructure.
Coverage is best where operators are dense (Europe, North America, Japan,
Australia) and thinner elsewhere.

## Install

1. Download this repository as a ZIP (or clone it).
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**, and select the zipped `bolt/` folder, or copy `bolt/` into your QGIS plugins directory.
3. Enable **Bolt**. A **Bolt** panel appears on the right.

## Usage

1. Choose the **Source** (Blitzortung — keyless, no configuration).
2. Choose **Track the current map view** or **Draw an area on the map**.
3. Click **Start tracking**. Strikes flash onto the map in real time and fade over a minute. Pan to an active storm to watch it light up.

## Credits

Lightning data © [Blitzortung.org](https://www.blitzortung.org/) and its
contributors, used under their non-commercial terms.

## License

GPL-2.0-or-later.

# Bolt

> ⚠️ **Personal project — not an official or vetted QGIS plugin.**
> Bolt is shared here as a personal, non-commercial, educational tool. It is
> **not** published on the QGIS plugin repository and has not been reviewed by
> anyone. It connects to the **Blitzortung.org** network, whose data is reserved
> for project **participants** and for **private, non-commercial** use. **If you
> install Bolt, you are responsible for reviewing and complying with
> [Blitzortung's terms](https://www.blitzortung.org/)** — and are encouraged to
> [contribute a station](https://www.blitzortung.org/en/cover_your_area.php) to
> the network. Bolt is not affiliated with or endorsed by Blitzortung.org, and is
> **not** for storm-warning, overvoltage, or risk-analysis use.

Watch **live lightning detections** on your map. Bolt streams real-time
**detections from the Blitzortung.org volunteer sensor network** into QGIS and
shows them flash onto the map as they happen, then fade over a minute — track
your current map view, or draw an area to watch. Live only; no history replay.

Bolt is one of four sibling plugins built on the same live-tracking engine — a
pluggable data-source layer, a moving/expiring-point map layer, clustering and
identify — covering **sea, sky, space and storms**:

- [Wake](https://github.com/PeterCotroneo/Wake) — marine vessels (AIS)
- [Contrail](https://github.com/PeterCotroneo/Contrail) — aircraft (ADS-B)
- [Zenith](https://github.com/PeterCotroneo/Zenith) — satellites (SGP4)
- **Bolt** — lightning (this one)

![Bolt showing live lightning detections over the Caribbean and Gulf, clustered and coloured by age](docs/img/01-caribbean-storms.jpg)

## Features

- **Live detections** — lightning **detections** from the Blitzortung sensor network appear as they are reported, in near real time.
- **Free and keyless** — no account, no API key.
- **Age-coloured** — each detection flashes bright, then fades white → yellow → orange → red over about a minute, so the map shows where storms are active *right now*.
- **Cluster badges** — busy storm cells collapse into a counted marker, coloured by the freshest detection; zoom in and they fan out.
- **Coverage-aware** — these are *detections*, not ground truth. An area with no markers may mean **no lightning** *or* **no sensor coverage** there. Coverage is best where operators are dense (Europe, North America, Japan, Australia) and thinner elsewhere.
- **Click for detail** — Identify any detection for its time (UTC) and how many detectors reported it.
- **Area-based** — watch your map view or a drawn box; detections outside it are dropped.
- **No extra dependencies** — uses Qt's built-in WebSocket, so it installs cleanly.

## Data source, attribution and terms

Detections come from the **[Blitzortung.org](https://www.blitzortung.org/)**
volunteer network — a community of operators running receivers around the world.
Bolt keeps the attribution visible in its panel.

**Please read Blitzortung's terms before installing or using Bolt.** Blitzortung
reserves raw-data access for **project participants** and for **private,
non-commercial** use, and their policy for external projects asks that
applications retrieve data from a **separate server**, not directly from
Blitzortung's own servers. Bolt connects directly, so it is offered here as a
**personal / reference tool only** — not as a distributed product and not on the
QGIS plugin repository. All data remains under **CC BY-SA 4.0**; Bolt keeps the
attribution visible. This is volunteer-run infrastructure — please respect the
community and consider running a station.

## Install

Bolt is **not** on the QGIS plugin repository (see the note at the top). To try
it for personal use:

1. Download **`Bolt.zip`** from this repository (or clone it and zip the `bolt/` folder).
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**, and select `Bolt.zip`.
3. Enable **Bolt**. A **Bolt** panel appears on the right.

By installing, you accept responsibility for using the Blitzortung feed within
their terms.

## Usage

1. Choose the **Source** (Blitzortung — keyless, no configuration).
2. Choose **Track the current map view** or **Draw an area on the map**.
3. Click **Start tracking**. Strikes flash onto the map in real time and fade over a minute. Pan to an active storm to watch it light up.

## Credits

Lightning data © [Blitzortung.org](https://www.blitzortung.org/) and its
contributors, used under their non-commercial terms.

## License

GPL-2.0-or-later.

# Transit Query Service

A containerized transit data query service built with PostgreSQL, Python, and Docker Compose. Models a real transit system — lines, stops, trips, and stop events — with a relational schema and query layer for analyzing schedules and ridership patterns.

## Stack

`Python` `PostgreSQL` `Docker` `Docker Compose` `SQL`

## Structure
```

├── schema.sql            # Relational schema: lines, stops, trips, stop_events
├── load_data.py          # Loads CSV transit data into PostgreSQL
├── queries.py            # Query layer for schedule and ridership analysis
├── docker-compose.yaml   # Multi-container setup (app + database)
├── Dockerfile
├── build.sh              # Build script
├── run.sh                # Run script
├── test.sh               # Test script
└── data/                 # Transit CSV datasets (lines, stops, line_stops, trips, stop_events)
```

## Getting Started

**Requirements:** Docker and Docker Compose

Build and start the containers:

```bash
docker-compose up --build
```

Load the transit data:

```bash
python load_data.py
```

Run queries:

```bash
python queries.py
```

Or use the provided shell scripts:

```bash
./build.sh
./run.sh
./test.sh
```

## Data Model

Five entities model a complete transit network:

| Table | Description |
|---|---|
| `lines` | Transit routes/lines |
| `stops` | Individual stop locations |
| `line_stops` | Mapping of stops to lines with sequence order |
| `trips` | Scheduled trips on a line |
| `stop_events` | Actual arrival/departure events per trip and stop |

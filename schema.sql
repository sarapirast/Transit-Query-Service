-- stable - natural
-- may change - surrogate


CREATE TABLE IF NOT EXISTS lines (
    line_id SERIAL PRIMARY KEY,  -- or use line_name as natural key?
    line_name VARCHAR(50) NOT NULL UNIQUE,
    vehicle_type VARCHAR(10) CHECK (vehicle_type IN ('rail', 'bus'))
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id SERIAL PRIMARY KEY,
    stop_name VARCHAR(100) NOT NULL UNIQUE,
    latitude DECIMAL(9,6) CHECK (latitude BETWEEN -90 AND 90), --90 South to 90 North, expressed as -90 to +90 in decimal degrees
    longitude DECIMAL(9,6) CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS line_stops (
    line_id INT NOT NULL,
    stop_id INT NOT NULL,
    FOREIGN KEY (line_id) REFERENCES lines(line_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id),
    PRIMARY KEY (line_id,stop_id),
    sequence_number INT NOT NULL,
    time_offset_minutes INT NOT NULL CHECK (time_offset_minutes>=0),
    UNIQUE(line_id, sequence_number)

);



CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(50) PRIMARY KEY,
    line_id INT NOT NULL,
    FOREIGN KEY (line_id) REFERENCES lines(line_id),
    scheduled_departure TIMESTAMP NOT NULL,
    vehicle_id VARCHAR(5) NOT NULL 

);

CREATE TABLE IF NOT EXISTS stop_events (
-- Has: trip, stop, scheduled time, actual time, passengers on/off
    trip_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    stop_id INT NOT NULL,
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id),
    scheduled_time TIMESTAMP NOT NULL,
    actual_time TIMESTAMP NOT NULL,
    passengers_on INT NOT NULL CHECK (passengers_on>=0),
    passengers_off INT NOT NULL CHECK (passengers_off>=0),
    PRIMARY KEY(trip_id,stop_id,scheduled_time)

);

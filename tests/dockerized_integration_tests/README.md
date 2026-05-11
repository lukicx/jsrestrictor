# Dockerized integration tests

This directory contains Docker-based integration tests for JShelter.

## Building the Firefox extension package

Some Firefox tests require the JShelter Firefox package to be available in the
repository root as `jshelter_firefox.zip`.

Build it from the repository root:

`make firefox`

This command must be executed from the repository root, not from this directory.

## Requirements

- Docker is installed and running
- Docker Compose is available

## Preparing browser profiles

Some tests require manually prepared browser profiles. The profiles are stored
in Docker volumes, so they do not need to be prepared before every test run.

Before running the full test suite, prepare both the Chrome JShelter profile and
the Firefox FPD profile.


### Preparing the Chrome profile with JShelter

Run from this directory:

`./start_integration chrome-jshelter`

Open in the browser:

`http://localhost:7901/`

1. **Accept** cookies.
2. Click **Add extension**.
3. Open the three-dot menu.
4. Go to **Extensions -> Manage extensions**.
   Alternatively, open `chrome://extensions/`.
5. Open **JShelter -> Details**.
6. Enable **Allow User Scripts**.
7. Press Enter in the terminal to close the browser.

### Preparing the Firefox profile with JShelter for FPD

Run from this directory:

`./start_integration firefox-jshelter`

Open in the browser:

`http://localhost:7900/`

Steps:

1. Click **Add to Firefox** and then **Add**.
2. Open **Extensions** in the top-right corner.
3. Open **JShelter**.
4. Go to **Global Settings**.
5. Set **Fingerprint Detector -> Behavior** to **Limited Blocking**.
6. Press Enter in the terminal to close the browser.

## Running all tests

Run from this directory:

`./start_integration`


## Running individual test groups

```bash
./start_integration fingerprinting
./start_integration fpd
./start_integration geo
./start_integration lna
./start_integration nbs
./start_integration sensor
```

## Stopping the test environment

When you are done running tests, stop the containers manually:

`docker compose down`

This stops and removes the containers but preserves the prepared browser
profiles in Docker volumes.

To remove profiles, use `docker compose down -v`.

## Test groups

- `fingerprinting` – tests JavaScript APIs commonly used for browser fingerprinting
- `fpd` – tests Fingerprinting Detector behavior
- `geo` – tests geolocation API protection
- `lna` – tests Local Network Access behavior
- `nbs` – tests Network Boundary Shield behavior
- `sensor` – tests Generic Sensor API protection

1. Preparing the Chrome profile with JShelter

./start_integration chrome-jshelter

Open in the browser:

http://localhost:7901/

Steps:
- Click Add extension.
- Open the three-dot menu.
- Go to Extensions -> Manage extensions.
- Alternatively, open chrome://extensions/.
- Open JShelter -> Details.
- Enable Allow User Scripts.
- Press Enter in the terminal to close the browser.

2. Preparing the Firefox profile with JShelter for FPD

./start_integration firefox-jshelter

Open in the browser:

http://localhost:7900/

Steps:
- Click Add to Firefox -> Add.
- Open Extensions in the top-right corner -> JShelter.
- Go to Global Settings.
- Set Fingerprint Detector -> Behavior to Limited Blocking.
- Press Enter in the terminal to close the browser.

3. Running all tests

./start_integration

4. Running individual tests

./start_integration fingerprinting
./start_integration fpd
./start_integration geo
./start_integration lna
./start_integration nbs
./start_integration sensor

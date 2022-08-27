# devstatmon
Device ONLINE/OFFLINE status monitor

## Pre-requisites
* [edgebridge](https://github.com/toddaustin07/edgebridge)
* LAN Presence Edge driver from my [shared projects channel](https://bestow-regional.api.smartthings.com/invite/d429RZv8m9lo)
* Python 3.x

## Instructions

1. Download devstatmon.py and devstatmon.cfg to a directory on your computer
2) Edit devstatmon.cfg:
    * The first 3 entries represent each of the devices you want to monitor and is a list of one or more values separated by commas.  Each of the three entries should contain the same number of comma-separated items
      * device_names - list of short alphanumeric names representing the devices (no blanks or special characters)
      * device_ids - list of corresponding SmartThings device IDs in UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx) hexidecimal characters
      * polling_interval - list of desired corresponding polling intervals in seconds
    * SmartThings_Bearer_Token - your [personal token](https://account.smartthings.com/tokens); be sure that it includes authorization for reading location and devices
    * port - port number to be used by this application (defaults to 50003)
    * bridge_address - IP:port number of the edgebridge server application
    * console_output - yes/no
    * logfile_output - yes/no
    * logfile - name of log file (defaults to devstatmon.log); will be in the current working directory
    
    Example:
 ```
 [config]
device_names = dev1, dev2, dev3
device_ids = 72fa839a-2a8d-40ad-b21d-e25722f4d3e5, 82d03cd4-7bc6-49fd-bf40-0a4319fb1799, ff235174-56df-4a0f-a8a1-5821cbdb3e05
polling_interval = 600, 600, 600
#
SmartThings_Bearer_Token = 1234abcd-56ef-78ab-9cde-abcd1234ef56
#
port = 50003
bridge_address = 192.168.1.140:8088
#
console_output = yes
logfile_output = yes
logfile = devstatmon.log
```
3. Be sure edgebridge is installed and running
4. Install the LAN Presence Edge driver to your hub from [this channel](https://bestow-regional.api.smartthings.com/invite/d429RZv8m9lo) (if not already)
    * Create a separate LAN Presence device for each SmartThings device you configured above
    * For each LAN Presence device, configure device Settings:
      * LAN Device Name - the short name you used in the devstatmon.cfg file
      * LAN Device Address - the IP:port address where your devstatmon app will be running (e.g. 192.168.1.30:50003)
      * Bridge Address - the IP:port address where your edgebridge app is running (e.g. 192.168.1.140:8088)
    * Monitor the edgebridge console output, you should see a registration message received from the driver for each device configured
5. Start the devstatmon app:
```
python3 devstatmon.py
```

Watch the console output of the devstatmon app.  You should begin to see messages like this:
```
Sat Aug 27 14:56:17 2022  Device <72fa839a-2a8d-40ad-b21d-e25722f4d3e5> (dev1) returned ONLINE
Sat Aug 27 14:56:17 2022  	Updating SmartThings device "dev1" to present
Sat Aug 27 14:56:34 2022  Device <82d03cd4-7bc6-49fd-bf40-0a4319fb1799> (dev2) returned OFFLINE
Sat Aug 27 14:56:34 2022  	Updating SmartThings device "dev2" to notpresent
Sat Aug 27 14:56:56 2022  Device <ff235174-56df-4a0f-a8a1-5821cbdb3e05> (dev3) returned ONLINE
Sat Aug 27 14:56:56 2022  	Updating SmartThings device "dev3" to present
Sat Aug 27 15:06:17 2022  Device <72fa839a-2a8d-40ad-b21d-e25722f4d3e5> (dev1) returned ONLINE
Sat Aug 27 15:06:34 2022  Device <82d03cd4-7bc6-49fd-bf40-0a4319fb1799> (dev2) returned OFFLINE
Sat Aug 27 15:06:56 2022  Device <ff235174-56df-4a0f-a8a1-5821cbdb3e05> (dev3) returned ONLINE
Sat Aug 27 15:16:17 2022  Device <72fa839a-2a8d-40ad-b21d-e25722f4d3e5> (dev1) returned ONLINE
Sat Aug 27 15:16:34 2022  Device <82d03cd4-7bc6-49fd-bf40-0a4319fb1799> (dev2) returned OFFLINE
Sat Aug 27 15:16:56 2022  Device <ff235174-56df-4a0f-a8a1-5821cbdb3e05> (dev3) returned ONLINE
Sat Aug 27 15:26:17 2022  Device <72fa839a-2a8d-40ad-b21d-e25722f4d3e5> (dev1) returned ONLINE
Sat Aug 27 15:26:17 2022  	Updating SmartThings device "dev1" to present
Sat Aug 27 15:26:34 2022  Device <82d03cd4-7bc6-49fd-bf40-0a4319fb1799> (dev2) returned OFFLINE
Sat Aug 27 15:26:56 2022  Device <ff235174-56df-4a0f-a8a1-5821cbdb3e05> (dev3) returned ONLINE
```

The SmartThings API is polled based on the interval you configured.  The *start* of polling for each device is staggered randomly, so it may take some number of seconds before each device polling initially begins.

Updates are sent to your SmartThings Edge presence device (via edgebridge) when there is a change, OR every 30 minutes whether or not there is a change.

**ONLINE = present, OFFLINE = not present**

You should see messages on your edgebridge console whenever update messages are sent from the devstatmon app, and your SmartThings device presence state will change accordingly as the edgebridge server forwards the message to the Edge driver.

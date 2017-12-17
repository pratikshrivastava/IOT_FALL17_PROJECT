#!/bin/sh 


## Read the data from the GPS 
echo "started on: " `date`




## Stop and disable the getty service.
 

sudo systemctl stop  getty@ttyAMA0.service
sudo systemctl disable getty@ttyAMA0.service

### sleep for 2 min, so that hte other services like wifi etc are up. 

sleep 120 

## Execute the gps tracker script.


cd /home/pi/Desktop/iot_project/

sudo python gps_tracker_app.py >  logs\`date.log
#!/use/bin/py



### import libraries required for working of the code.
import serial
import pynmea2
import time 
from haversine import *
from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
# import boto3




#### Creds detail  for connecting with AWS 

host = 'a21ztuc2nsqgls.iot.us-east-2.amazonaws.com'

rootCAPath = 'root-CA.crt'
certificatePath = 'iot_pi.cert.pem'
privateKeyPath = 'iot_pi.private.key'

#useWebsocket = 'args.useWebsocket'

clientId = 'iot_pi_1'

### Topic for MQTT client connection 
topic = 'gps_location'

### time dealy for collecting data with the GPS. 
delay = 30

#print(datetime.now())
#time.sleep(delay)
#print(datetime.now())


### distance moved to trigger the alarm
distance_threshold = 10 

### filename for logging the data send to AWS 
filename='test_data_aws.csv'

### AWS credential setup with the MQTT Client 

myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, 8883)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec


# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()


#### Function for calculating the distance between two points
#### Used haversine function for calculating the azimuthal distance and not euclidean. 

def distance(position1,position2):
	change = haversine((position1[0], position1[1]),(position2[0],position2[1]),miles =False)
	#change = great_circle((position1[0], position1[1]),(position2[0],position2[1])).miles
	change = change * 1000 
	return change


### Boolean function to check if the GPS has moved more than 10 meters. ### 

def chk_move(change_pos):
	if(change_pos > distance_threshold ): 
		moving=True
	else:
		moving=False
	return moving

###  Write data to a file ### 

def log_data_file(filename,data): 
	f = open(filename,"a+")
	f.write(data)
	f.close()


###  Create data in csv format ### 
	
def create_data_csv(time_stamp, location_data):
	
	timestamp = str(time_stamp) 
	lat = str(location_data[0])
	lon = str(location_data[1])
	data = timestamp + "," + lat + "," + lon + "\n"  
	return data 

###  Created data in json  format ### 	


def create_data_json(time_stamp, location_data):
	data = {'devicename': clientId , 'timestamp' : time_stamp, 'lat':location_data[0], 'lon': location_data[1]}		
	return data

def main_func(start_position,new_position):
		#print('In Main') 		
		### Get change in position
		change_pos = distance(start_position,new_position)
		
		### Check whether there is a change in position above the 
		### threshold if yes, then push the data to AWS and into a file. 
		if(chk_move(change_pos)):
			
			#print('In check_movement') 	
			### Publish data to AWS 
			myAWSIoTMQTTClient.publish(topic,str(create_data_json(datetime.now(), new_position)), 0)
			print('Published topic %s: %s\n' % (topic,str(create_data_json(datetime.now(),new_position))))					
			
			### Also log the dat into a file
			log_data_file(filename, str(create_data_csv(datetime.now(), new_position)))

			
#### Function for reading the serial data from the GPS 
#### using the serial ports 

def read_serial_data():

	serialStream = serial.Serial("/dev/ttyAMA0", 9600, timeout=5)
	cnt = 0
	while True:
		### Read the data from serial port line by line. 
		sentence = serialStream.readline()
		
		### Check for the NMEA GPS fix. 
		### if found , then parse the latitude and longitude values. 
		if(sentence.find('GGA') > 0):
			data = pynmea2.parse(sentence)
			
			lat,lon = data.latitude, data.longitude
			data = str(datetime.now())+ ',' + str(lat) + ',' + str(lon) + '\n'
			# print(data)
			
			### Open a file and save this data into it. 
			f = open('logs/test_new_app.txt',"a+")
			f.write(data)
			
			### Check for the starting position of the GPS. 
			### If cnt == 0 then only starting position or else it would be the next position. 
			### 
			
			if(cnt > 0):
				new_position = [lat,lon]
				
				### Pass the starting and new position to the main function for further processing. 
				main_func(start_position,new_position)
			else: 
				start_position = [lat,lon]
				cnt = 100
			### wait for sometime before reading the next values. 
			time.sleep(delay)
			f.close()
	return   


read_serial_data()			

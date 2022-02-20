#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime, time, collections
import RPi.GPIO as GPIO
import Adafruit_ADS1x15

debug = 0

path_to_files = '/tmp/'

adc = Adafruit_ADS1x15.ADS1115()
GAIN = 1

anemo_pin = 23 # Anemometer_pin

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(anemo_pin, GPIO.IN, GPIO.PUD_UP)

revs = 0
last_time = datetime.datetime.now()

wind_values = [None] * 5

wind_angle_raw = [92, 151, 137, 120, 64, 13, 21, 39]
wind_angle = [45, 90, 135, 180, 225, 270, 315, 360]

# S = 0.39
# SV = 0.92
# V = 1.51
# JV = 1.37
# J = 1.2
# JZ = 0.64
# Z = 0.13
# SZ = 0.21

def count_revs(channel):
	global last_time, revs
	revs += 1

def get_angle():
	raw_value = round(float(adc.read_adc(0, gain=GAIN)) * 4.096 / 65535, 2) * 100
	angle = -1
	for i in xrange(0, len(wind_angle_raw)):
		if raw_value in xrange(wind_angle_raw[i] - 3, wind_angle_raw[i] + 4):
			angle = wind_angle[i]
	return angle

GPIO.add_event_detect(anemo_pin, GPIO.FALLING, callback=count_revs, bouncetime=10)

samples = 100
average = [0] * samples
direction = [-1] * samples
i = 0
ready = 0

while True:
	present_time = datetime.datetime.now()
	if float(str((present_time - last_time).seconds) + "." + str((present_time - last_time).microseconds)) >= 2.98:
		average[i] = revs
		revs = 0
		gust_speed = (float(max(average)) - 1.62391033623907) / 1.3765877957658
		if gust_speed < 0:
			gust_speed = 0
		wind_speed = ((float(sum(average)) / samples) - 1.62391033623907) / 1.3765877957658
		if wind_speed < 0:
			wind_speed = 0
		if average[i] >= 0:
			direction[i] = get_angle()
		else:
			direction[i] = 0
		stripped_direction = direction[:]
		while stripped_direction.count(-1) > 0:
			stripped_direction.remove(-1)
		angle_counter = collections.Counter(stripped_direction)
		angle_most = angle_counter.most_common(1)
		if debug == 1:
			print average
			print direction
			print stripped_direction
			print "Check time: " + str((present_time - last_time).seconds) + "." + str((present_time - last_time).microseconds) + " s"
			print "Direction: " + str(round((float(adc.read_adc(0, gain=GAIN)) * 4.096 / 65535), 3)) + " V" # Should be * 2 ?
			print "Gust revs: " + str(max(average)) # Maximum value in list = gust speed
			print "Total revs/5min: " + str(sum(average)) # Correlate this number with something
			print "Avg. revs/5min: " + str(round(float(sum(average)) / samples, 2))
			print "---------------------"
			print "Gust speed: " + str(round(gust_speed, 2)) + " km/h" # Maximum value in list = gust speed
			print "Wind speed: " + str(round(wind_speed, 2)) + " km/h"
			print "---------------------"
			print "Size of angle array: " + str(len(stripped_direction))
			print "Average angle: " + str(int(float(sum(stripped_direction)) / len(stripped_direction)))
			print "Most angle: " + str(angle_most[0][0])
			print angle_counter
		wind_values[0] = round(wind_speed, 1)
		wind_values[1] = round(gust_speed, 1)
		wind_values[2] = round(wind_speed / 3.6, 1)
		wind_values[3] = round(gust_speed / 3.6, 1)
#		wind_values[4] = round((float(adc.read_adc(0, gain=GAIN)) * 4.096 / 65535), 3)
		if len(stripped_direction) > 0:
			wind_values[4] = str(angle_most[0][0])
		else:
			wind_values[4] = str(0)
		try:
			wind_file = open(path_to_files + 'wind', 'w')
			for index in range(0, len(wind_values)):
		                wind_file.write("%s\n" % wind_values[index])
		        wind_file.close()
		except:
			pass
		i += 1
		if i == samples:
			i = 0
		last_time = datetime.datetime.now()
	time.sleep(0.01)

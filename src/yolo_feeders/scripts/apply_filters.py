#!/usr/bin/env python

# Listens for images supplied through 'apply_filters' topic
# Applies filter to image based on argument
# Publishes augmented image to camera/rgb/image_raw
# OPTIONS: C (default), DP, HP, D

# Created 01/10/19 - Andrew Bui
# Last Modified 13/10/19 - Dustin Haines

import argparse
import sys
import cv2
import numpy as np
import random
import time
import rospkg
import rospy
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import Header
from sensor_msgs.msg import Image

# Constant directory locations
rospack = rospkg.RosPack()
fp = rospack.get_path('yolo_feeders')
NODE_NAME = 'filters'
IMAGE_FOLDER = fp + '/../../transform_images/'
# TODO: Export config out to a yaml file and load on launch
# Default configurations
INPUT_TOPIC = '/image_raw'
OUTPUT_TOPIC = '/transform/image'
IMAGE_CRACK = 'cracks.png'
IMAGE_NOISE = 'noise.png'
IMAGE_SCRATCHES = 'scratches.png'

# Variables dependent on CLI parameters
TRANSFORM_IMAGE_NAME = ''
TRANSFORM_IMAGE = None
TRANSFORM_ON = False
DEADPIXEL_ON = False
HOTPIXEL_ON = False

# Constant variables that are reused
bridge = CvBridge()
last_frame = -1

def images_in(data):
	global last_frame
	frame_num = data.header.seq
	# Verify we haven't already recorded the interpretation of the frame
	if frame_num > last_frame:
		# Update the last frame we saw
		last_frame = frame_num
		# Take the sensor_msgs Image and convert to cv2
		supplied_image = bridge.imgmsg_to_cv2(data)#, desired_encoding='bgra8')
		# Obtain dimensions of supplied feed
		width, height, _ = supplied_image.shape
		# Create random pixel defects based on the size of the image
		#pixel_defect_x = random.randint(0, width)
		#pixel_defect_y = random.randint(0, height)


		if TRANSFORM_ON:
			# Make overlay same size as camera resolution
			overlay = cv2.resize(TRANSFORM_IMAGE, (int(height), int(width)))

			# Extract the alpha mask of the RGBA image, convert to RGB
			_, _, _, a = cv2.split(overlay)
			overlay = cv2.cvtColor(overlay, cv2.COLOR_BGRA2BGR)	
			
			# Apply some simple filtering to remove edge noise
			mask = cv2.medianBlur(a, 5)
			inv_mask = cv2.bitwise_not(mask)

			# Black out the region of the image where the overlay will go
			supplied_image = cv2.bitwise_and(supplied_image, supplied_image, mask=inv_mask)
			# Obtain the portion of the overlay image that is the effect
			overlay = cv2.bitwise_and(overlay, overlay, mask=mask)

			# Merge the two
			transformed_image = cv2.add(supplied_image, overlay)
			# Reverse the image ordering to display correctly
			transformed_image = cv2.cvtColor(transformed_image, cv2.COLOR_BGR2RGB)

		#if dead_pixel:
		#	# Dead Pixel
		#	cv2.circle(suppliedImage, (pixel_defect_x, pixel_defect_y), 5, (0, 0, 0), thickness=-1, lineType=8, shift=0)
		#if hot_pixel:
			# Hot Pixel
		#	cv2.circle(suppliedImage, (pixel_defect_x, pixel_defect_y), 5, (45, 67, 237), thickness=-1, lineType=8, shift=0)
		#	cv2.circle(suppliedImage, (pixel_defect_x, pixel_defect_y), 3, (63, 82, 63), thickness=-1, lineType=8, shift=0)
		#	cv2.circle(suppliedImage, (pixel_defect_x, pixel_defect_y), 1, (81, 99, 232), thickness=-1, lineType=8, shift=0)

		# Convert cv2 image to imgmsg for YOLO
		transformed_image_msg = bridge.cv2_to_imgmsg(transformed_image)
		transformed_image_msg.encoding = 'bgr8'
		# Publish to topic
		pub.publish(transformed_image_msg)

def argument_parser():
	parser = argparse.ArgumentParser()
	# Specify all possible command line arguments
	parser.add_argument('-f', '--filename')
	parser.add_argument('-hp', '--hotpixel', action='store_true')
	parser.add_argument('-dp', '--deadpixel', action='store_true')
	parser.add_argument('-c', '--cracks', action='store_true')
	parser.add_argument('-n', '--noise', action='store_true')
	parser.add_argument('-s', '--scratches', action='store_true')
	parser.add_argument('-it', '--input_topic')
	parser.add_argument('-ot', '--output_topic')
	return parser

if __name__ == '__main__':
	# Retrieve argument parser and parse anything supplied
	parser = argument_parser()
	args = parser.parse_args()
	# Update parameters as appropriate
	if args.cracks:
		TRANSFORM_IMAGE_NAME = IMAGE_CRACK
	elif args.noise:
		TRANSFORM_IMAGE_NAME = IMAGE_NOISE
	elif args.scratches:
		TRANSFORM_IMAGE_NAME = IMAGE_SCRATCHES
	elif args.filename:
		TRANSFORM_IMAGE_NAME = args.filename
	elif args.hotpixel is not None or args.deadpixel is not None:
		TRANSFORM_IMAGE_NAME = 'NA'
	else:
		print('ERROR: Valid scenario needs to be specified')
		print('Supply an image to overlay with -f, or use one of the options -c, -n, -s for default images')
		print('Alternatively, use -h or -d for hot/dead pixel transformations')
		exit(1)

	HOTPIXEL_ON = True if args.hotpixel else False
	DEADPIXEL_ON = True if args.deadpixel else False
	INPUT_TOPIC = args.input_topic if args.input_topic else INPUT_TOPIC
	OUTPUT_TOPIC = args.output_topic if args.output_topic else OUTPUT_TOPIC
	
	# Ensure the supplied file is valid
	try:
		if TRANSFORM_IMAGE_NAME != 'NA':
			TRANSFORM_ON = True
			file = open(IMAGE_FOLDER + TRANSFORM_IMAGE_NAME, 'r')
			file.close()
			# Load the file and keep a reference to minimise disk I/O
			TRANSFORM_IMAGE = cv2.imread(IMAGE_FOLDER + TRANSFORM_IMAGE_NAME, -1)
			print('File to use ' + TRANSFORM_IMAGE_NAME + ' exists and will be used for transformations')
		else:
			print('No overlay image will be applied. Scenario is only hot/dead pixel')
	except:
		print('ERROR: Transform file ' + TRANSFORM_IMAGE_NAME + ' could not be loaded from ' + IMAGE_FOLDER)
		print('Please check the filename and ensure the file exists')
		exit(1)

	# Launch the node
	pub = rospy.Publisher(OUTPUT_TOPIC, Image, queue_size=2)
	# Initialise the node
	rospy.init_node(NODE_NAME, anonymous=True)
	# Subscribe to topics, specifying the data type and callback function	
	rospy.Subscriber(INPUT_TOPIC, Image, images_in)
	print '\nROS Node launched. Listening to topic ' +  INPUT_TOPIC + ', Outputing to topic ' + OUTPUT_TOPIC
	print '\nRunning with the following parameters'
	print 'TRANSFORM_IMAGE_NAME: ' + TRANSFORM_IMAGE_NAME
	print 'HOTPIXEL_ON:' + str(HOTPIXEL_ON)
	print 'DEADPIXEL_ON:' + str(DEADPIXEL_ON)
    # Keeps the listener alive
	rospy.spin()




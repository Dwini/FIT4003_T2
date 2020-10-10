#!/usr/bin/env python
# Takes in filename of a results csv, analyses the data
# and prints out results based on arguments

# Created: 15/10/19 - Andrew Bui
# Last Modified: 18/10/19 - Andrew Bui

import argparse
import csv

# Configuration
OUTPUT_BOUNDS = '../output_bounds/'
OUTPUT_FILENAME_DIR = '../output_bounds_reports/'
OUTPUT_FILENAME_DET = None
OUTPUT_FILE_DET_REPORT = None
OUTPUT_FILENAME_SUM = None
OUTPUT_FILE_SUM_REPORT = None

# Creates parser to read arguments
def create_parser():
	parser = argparse.ArgumentParser()

	# Specify arguments
	parser.add_argument('-f', '--filename')
	parser.add_argument('-s', '--summary',action='store_true')
	parser.add_argument('-d', '--detailed', action='store_true')

	return parser

# Outputs the number of onjects that were found during yolo run
def summary_breakdown(csvFile):

	objectsDetected = 0
	numSequence = 0
	aveProb = 0
	
	with csvFile:
	# Skip first row if there is a header
		has_header = csv.Sniffer().has_header(csvFile.read(1024))
		csvFile.seek(0)
		csvReader = csv.reader(csvFile)
		if has_header:
			next(csvReader)
		try:
			for line in csvReader:
				numSequence += 1
				objectsDetected += int(line[1])
				aveProb += float(line[2])

			aveProb = aveProb/numSequence
		except ValueError:
			print('Incorrect report type for this file. Choose -d for detailed report\n')
			exit(1)
		
		summaryFile = open(OUTPUT_FILENAME_DIR + OUTPUT_FILENAME_SUM, 'w')
		summaryFile.write('Number of objects detected: {}\n'.format(objectsDetected))
		summaryFile.write('Total average probability: {}\n'.format(aveProb))
		summaryFile.close()

		print("Writing summary to {}".format(OUTPUT_FILENAME_SUM))


# Outputs average probably and count of each object type
def detailed_breakdown(csvFile):
	allObjects = {}
	averageProbability = {}

	# read in csv file
	with csvFile:
		# Skip first row if there is a header
		has_header = csv.Sniffer().has_header(csvFile.read(1024))
		csvFile.seek(0)
		csvReader = csv.reader(csvFile)
		if has_header:
			next(csvReader)
		
		for line in csvReader:
			# Appends probability instance if object already exists
			if line[1] in allObjects:
				allObjects[line[1]].append(float(line[2]))
			# Otherwise add new object type
			else:
				allObjects[line[1]] = [float(line[2])]
	
	# Open file and write results
	OUTPUT_FILE_DET_REPORT = csv.writer(open(OUTPUT_FILENAME_DIR+OUTPUT_FILENAME_DET, 'w'), delimiter=',')
	OUTPUT_FILE_DET_REPORT.writerow(['OBJECT_TYPE', 'OBJECT_COUNT', 'AVERAGE_PROB'])
	print('Writing results in {}'.format(OUTPUT_FILENAME_DIR+OUTPUT_FILENAME_DET))

	# Determine average and count for each object type
	for key, value in allObjects.items():
		average = round(sum(value)/len(value),4)
		averageProbability[key] = {
			"average": average,
			"count": len(value)
		}
	
	# Write each object type to an output csv file 
	for key, value in sorted(averageProbability.items()):
		OUTPUT_FILE_DET_REPORT.writerow([key, value['count'], value['average']])

if __name__ == "__main__":	
	# Create parser
	parser = create_parser()
	args = parser.parse_args()

	# Check that filename has been specified
	if args.filename:
		filename = OUTPUT_BOUNDS + args.filename

		# Check if file can be read, exit if it cannot
		try:
			csvFile = open(filename, mode='r')
		except IOError:
			print('Could not read file:{}\nEnter a valid filename with the extension included.\n'.format(filename))
			exit(1)

		# Report based on type of csv is read
		if args.detailed:
			OUTPUT_FILENAME_DET = args.filename.split('_')[0] + '_Detailed_Report.csv'
			detailed_breakdown(csvFile)
		elif args.summary:
			OUTPUT_FILENAME_SUM = args.filename.split('_')[0] + '_Summary_Report.txt'
			summary_breakdown(csvFile)
		else:
			print('Report type needs to be specified.\nSupply as an argument either -s for summary or -d for detailed.\n')
		exit(1)
	else:
		print('Filename not specified\n')
		exit(1)

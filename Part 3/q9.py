import sqlite3
import sys

# Receive database path and query path from the user
dbName = str(input("Enter path to database: "))
fileName = str(input("Enter path to file containing query: "))

# Append ".db" to database path and ".txt" to query path if user did not include it
if ("db" not in dbName):
	dbName = dbName + ".db"
if (".txt" not in fileName):
	fileName = fileName + ".txt"

# Connect to the database
database = sqlite3.connect (dbName)
cursor = database.cursor ()

try:
	query = "DROP INDEX subjPred;"
	cursor.execute(query)
	database.commit()
except:
	pass
# Create the index
query = "CREATE INDEX subjPred on rdf (subject, predicate);"
cursor.execute(query)
database.commit()

# Takes in a string and a dictionary holding all results per argument
# 	Whenever there is a match between the string and the argument (key) then the argument and all its
# 		values gets printed
def printingFunction (match, args):
	print (match + ":")
	
	# Match is one of the arguments from the (SELECT... WHERE) that has to be printed
	# Iterate through the dictionary containing arguments and its query results and print values only if there is a match
	for i in args:
		if (i == match):
			for j in args[i]:
				value = j[0]
				
				# Once we encounter a ":", then assume that whatever comes before it is a prefix
				if (":" in value):
					while ("-" in value):
						value = value[:value.index("-")] + "_" + value[value.index("-") + 1 :]
					
					# Concatenating the uri with the object, so the result is a big uri
					query = "SELECT uri FROM uri WHERE prefix = (?);"
					cursor.execute (query, [( value[:value.index(":")] )])
					database.commit()
					uri = cursor.fetchall()

					# If the result of the query returns a prefix, concatenate strings to output a full URL
					if (uri != []):
						print ("\t", uri[0][0] + value[value.index(":") + 1:])

					# If the value itself is a URL, then the prefix query (above) returns nothing. Print the value anyways
					else:
						print ("\t", value)

				# If the value has no url (ex. if it is an xsd value) then print it out
				else:
					print ("\t", value)
		
# Open the query file for reading
file = open (fileName)

# Initialize data structures needed
# 	uriDict - a dictionary containing prefix and URI
# 	printList - list of arguments to be printed
#	args - a dictionary to store specified subjects/objects and its values
# 	previousArgs - stores arguments from the previous line (if the previous line ends with a ";" or ",")
uriDict = {}
printList = []
args = {}
previousArgs = []

# Iterate through all lines in query file
for line in file:

	try:
		# If the line in the query file is a newline then skip that line
		if (len(line.split()) == 0):
			continue


		# Check if the line contains a prefix
		if ("PREFIX" in line):
			uriLine = line.split()
			uriDict [uriLine[1]] = uriLine[2]
			continue


		# Check if the line is a "SELECT ..... WHERE {" statement
		# 	If it is, then return the paramenters
		# 	For now, we assume that the "SELECT ... WHERE " is all in one line
		if ("SELECT" in line):
			printList = line.split()
			extractedPrintList = False
			i = 0
			while (extractedPrintList != True):
				if (i == len(printList)):
					break
				elif (printList[i] == "SELECT" or printList[i] == "WHERE" or printList[i] == "{"):
					printList.pop(i)
				else:
					i = i + 1
			continue


		# Printing functions. If the user wantes "*" to be printed then all arguments
		# 	gets printed. Otherwise, only the keys that match with printList is printed
		if ("}" in line):
			if (line.split() == ["}"]):	
				if (printList[0] == "*"):
					for i in args:
						# pass
						printingFunction(i, args)
				else:
					for i in printList:
						# pass
						printingFunction(i, args)

		
		# If the line is a legitimate SPARQL triple then query from the table and format appropriately
		elif ("SELECT" not in line):

			lineSplit = line.split()
			lineSplit = previousArgs + lineSplit

			# If "FILTER" is in the line, assume that it is a filtering function
			if ("FILTER" in line):

				# If "REGEX" is in line then assume it is a string constraint
				if ("REGEX" in line):

					# keepArgs is a list to contain all the matches that must be displayed
					keepArgs = []

					# Isolate the arguments for REGEX
					regexFilter = line[line.index("(") + 1 : line.index(")")]
					regexFilter = regexFilter.split(",")

					# The arguments are wrapped by quotation marks. Parse string to not include quotation marks
					for i in regexFilter:
						if ('"' in i):
							iIndex = regexFilter.index(i)
							temp = regexFilter.pop(iIndex)
							temp = temp[temp.index('"') + 1:]
							temp = temp[:temp.index('"')]
							regexFilter.insert(iIndex, temp)
						# Remove any spaces around line arguments
						elif ("?" in i):
							regexFilter.insert(regexFilter.index(i), i.strip())
							regexFilter.pop(regexFilter.index(i))

					# caseInsensitive is a parameter that indicates if character cases matter
					if ("i" in regexFilter):
						caseInsensitive = True
						regexFilter.remove("i")
					else:
						caseInsensitive = False
					for i in args[regexFilter[0]]:
						if (regexFilter[1] in i[0]):
							keepArgs.append(i)
						elif (caseInsensitive == True):
							if (regexFilter[1].lower() in i[0].lower()):
								keepArgs.append(i)
					args[regexFilter[0]] = keepArgs
					continue

				# If "REGEX" is not in line, then assume that it is a numeric constraint
				# Example query line: FILTER (?argument == "10"^^xsd:integer)
				elif ("REGEX" not in line):

					# Isolate the part where the actual numerical comparison is done 
					# Example numFilter: (?argument == "10"^^xsd:integer)
					numFilter = line[line.index("(") + 1 : line.index(")")]

					# Convert the numerical argument into an integer or a float, depending on the specification
					# Example num: num = 10 (from "10"^^xsd:integer)
					if ("^^xsd:integer" in line):
						num = int(line[line.index('"') + 1 : line.index("^^xsd:integer") - 1])
					elif ("^^xsd:float" in line):
						num = float(line[line.index('"') + 1 : line.index("^^xsd:float") - 1])

					if ("==" in line):
						# Example line in query: FILTER(?argument == "10"^^xsd:integer)
						# Example toCompare: toCompare = "?argument"
						toCompare = numFilter[numFilter.index("?") : numFilter.index("=")]
						toCompare = toCompare.strip()

						# Obtain the list of values that match with the variable to be compared with the number (toCompare)
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num != num2):
								args[toCompare].remove(args[toCompare][i])
							elif (num == num2):
								i += 1

					# The following uses the same logic as above 
					elif ("!=" in line):
						toCompare = numFilter[numFilter.index("?") : numFilter.index("!")]
						toCompare = toCompare.strip()
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num == num2):
								args[toCompare].remove(args[toCompare][i])
							elif (num != num2):
								i += 1
					elif ("<=" in line):
						toCompare = numFilter[numFilter.index("?") : numFilter.index("<")]
						toCompare = toCompare.strip()
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num2 > num):
								args[toCompare].remove(args[toCompare][i])
							elif (num2 <= num):
								i += 1
					elif (">=" in line):
						toCompare = numFilter[numFilter.index("?") : numFilter.index(">")]
						toCompare = toCompare.strip()
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num2 < num):
								args[toCompare].remove(args[toCompare][i])
							elif (num2 >= num):
								i += 1
					elif ("<" in line):
						toCompare = numFilter[numFilter.index("?") : numFilter.index("<")]
						toCompare = toCompare.strip()
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num2 >= num):
								args[toCompare].remove(args[toCompare][i])
							elif (num2 < num):
								i += 1
					elif (">" in line):
						toCompare = numFilter[numFilter.index("?") : numFilter.index(">")]
						toCompare = toCompare.strip()
						done = False
						i = 0
						while (done == False):
							if (i >= len(args[toCompare])):
								break
							num2 = args[toCompare][i][0]	# Returns, for example, 'number:"2"^^xsd:float'
							num2 = float(num2[num2.index('"') + 1 : num2.index("^^xsd") - 1])	# num2 is now "2.0" of type flaot if we consider the example above
							if (num2 <= num):
								args[toCompare].remove(args[toCompare][i])
							elif (num2 > num):
								i += 1
					continue
				else:
					continue

			if ("?" in lineSplit[0]):
				subj = lineSplit[0]
				queryArg1 = lineSplit[1]
				queryArg2 = lineSplit[2]
				query = "SELECT subject FROM rdf WHERE predicate = (?) AND object = (?);"


			elif ("?" in lineSplit[2]):
				obj = lineSplit[2]
				queryArg1 = lineSplit[0]
				queryArg2 = lineSplit[1]
				query = "SELECT object FROM rdf WHERE subject = (?) AND predicate = (?);"

			cursor.execute(query, [(queryArg1), (queryArg2)])
			database.commit()
			objects = cursor.fetchall()

			if (lineSplit[-1] == "."):
				previousArgs = []
			elif (lineSplit[-1] == ","):
				previousArgs = []
				previousArgs.append(lineSplit[0])
				previousArgs.append(lineSplit[1])
			elif (lineSplit[-1] == ";"):
				previousArgs = []
				previousArgs.append(lineSplit[0])

			try:
				args[subj] = objects
			except:
				args[obj] = objects
	except:
		print ("")		

# Close file for reading
file.close()

# Drop the index
# query = "DROP INDEX subjPred;"
# cursor.execute(query)
# database.commit()
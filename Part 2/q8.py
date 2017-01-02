import sqlite3
import sys
import os

# Error checking class for turtle file lines
def error_check (line, recentPunc, lineSplit):

	# Accounts for the event where objects can be strings including spaces
	lineSplit = line.split()
	spaceInObject = False
	newObject = ''
	for i in lineSplit:
		if ('"' in i):
			spaceInObject = (not spaceInObject)
			if ('"' in i[i.index('"') + 1:]):
				spaceInObject = (not spaceInObject)
			elif (spaceInObject == False):
				newObject += i
				lineSplit.insert(lineSplit.index(i) + 1, newObject)
				lineSplit.remove(i)
		if (spaceInObject == True):
				newObject += i + " "
				lineSplit.insert(lineSplit.index(i), " ")
				lineSplit.remove(i)
	while (" " in lineSplit):
		lineSplit.remove(" ")

	# Line above ends with ".". Expect subject, predicate, object, 
	# punctuation (4 parameters)

	if (recentPunc == "."):
		try:
			# Confirm correct number of arguments present
			assert (len(lineSplit) == 4)
			return line [-1], lineSplit
		except AssertionError:
			pass
	# Line above ends with ";". Expect predicate, object, punctuation (3 
	# parameters)
	if (recentPunc == ";"):
		try:
			# Confirm correct number of arguments present
			assert (len(lineSplit) == 3)
			return line [-1], lineSplit
		except AssertionError:
			pass
	# Line above ends with ",". Expect object, punctuation (2 arguments)
	if (recentPunc == ","):
		try:
			# Confirm correct number of arguments present
			assert (len(lineSplit) == 2)
			return line [-1], lineSplit
		except AssertionError:
			pass
	# Print error message if AssertionError
	if (AssertionError):
		print ("Assertion Error: missing some arguments")
		print ("Please fix line" + ":", line, "\nQuitting...")
		os.system ("make clean")
		sys.exit()



def parse_execute (line, cursor, database, params, new, previousPunc):

	# Take care of prefix definitions
	if ("@prefix" in line):

		# Store the prefix as the table name for sql
		table_name = line [len ("@prefix ") : line.index (":")]

		# Isolate the uri from punctuation
		uri = line [line.index (table_name) + len (table_name) :]
		
		# SQLite has issues with the character "-". They are replaced with "_"
		if ("-" in table_name):
			table_name = table_name[:table_name.index("-")] + "_" + table_name[table_name.index("-") + 1:]
			table_name.strip("-")
		
		# Assert that uri wrappers "<" and ">" are present
		try:
			assert ("<" in uri and ">" in uri)
		except AssertionError:
			print ("Assertion Error: Missing uri wrappers '<' and '>' in", line, "\nQuitting...")
			os.system("make clean")
			sys.exit()
		
		# No AssertionError, isolate uri
		uri = uri.strip (uri [: (uri.index("<") + 1)])
		uri = uri.strip (uri [uri.index(">") :])

		# If prefix is defined twice (by accident) ensure two different URIs not created for the same prefix
		# created for the same prefix
		try:
			query = "SELECT uri FROM uri WHERE prefix = (?);"
			cursor.execute(query, [(table_name)])
			assert (cursor.fetchall() == [])
		except AssertionError:
			return params

		# Store prefix and uri for bookkeeping purposes
		query = ""
		query += "INSERT INTO uri VALUES (?, ?);"
		bind = [(table_name, uri)]
		cursor.executemany(query, bind)

		# Commit
		database.commit ()
		return params

	elif (len(params) + len(new) == 4):

		# 4 parameters in line (subject, predicate, object, punctuation). 
		if (previousPunc == "."):
			subject = new [0]
			predicate = new [1]
			objects = new [2]
			punc = new [3]

		# 3 parameters in line (predicate, object, punctuation). 
		# Receive subject from params
		elif (previousPunc == ";"):
			subject = params [0]
			predicate = new [0]
			objects = new [1]
			punc = new [2]

		# 2 parameters in line (object punctuation).
		# Receive subject and predicate from params
		elif (previousPunc == ","):
			subject = params [0]
			predicate = params [1]
			objects = new [0]
			punc = new [1]

		# Error check: make sure that the colon is in subject and predicate
		try:
			assert (":" in subject and ":" in predicate)
		except AssertionError:
			print ("Missing a colon somewhere")
			print ("Fix line: ", line)
			os.system ("make clean")
			sys.exit()

		# Store resources, predicates and values
		# subjectValue = subject[subject.index(":") + 1 :]
		# predicateValue = predicate[predicate.index(":") + 1 :]

		# Insert the subject, predicate, and the object into the table for the resource
		query = "INSERT INTO rdf VALUES (?, ?, ?);"

		# Confirm if the prefix is already defined. Not required for the program to run, but for good practice
		if (":" in objects and ("xsd" not in objects or "<" not in objects)):
			objectID = objects[:objects.index(":")]
			objectValue = objects[objects.index(":")+1:]
			try:
				confirm = "SELECT uri FROM uri WHERE prefix = (?);"
				cursor.execute(confirm, [(objectID)])
				confirm = cursor.fetchall()
				database.commit()
				assert (confirm != [])
			except AssertionError:
				objectID = ""
				objectValue = objects
		else:
			objectID = ""
			objectValue = objects
			pass

		if ("<" in objects and ">" in objects):
			objects = objects[objects.index("<") + 1 :objects.index(">")]

		# Isolate the url
		# cursor.executemany (query, [(subjectValue, predicateValue, objects)])
		cursor.executemany (query, [(subject, predicate, objects)])
		database.commit()

		# Returns appropriate parameters when "," or ";" are encountered.
		if (line [-1] == ".") :
			return []
		elif (line [-1] == ";") :
			return [subject]
		elif (line [-1] == ",") :
			return [subject, predicate]
	else:
		return params





os.system ("make clean")

# I used an external resource to learn how to use sqlite3 with Python
# Source: http://www.blog.pythonlibrary.org/2012/07/18/python-a-simple-step-by-step-sqlite-tutorial/

# Obtain the database name and turtle file name
dbName = input (str ("Enter name of database: "))
fileName = input (str ("Enter name of turtle file: "))

# Concatenate ".db" and ".txt" with database and file name, if not included already
if (".db" not in dbName):
	dbName = dbName + ".db"
if (".txt" not in fileName):
	fileName = fileName + ".txt"

# Create and connect to the database, initiate cursor
database = sqlite3.connect (dbName)
cursor = database.cursor ()

# Open the turtle file and read line-by-line. Implement functions
try:
	f = open (fileName)
except:
	print ("File does not exist. Please ensure file name is spelled correctly")
	os.system ("make clean")
	sys.exit()

# Create table to store uri and all triples
uri_table = "CREATE TABLE uri (prefix text UNIQUE, uri text UNIQUE); "
triple_table = "CREATE TABLE rdf (subject text, predicate text, object text);"
cursor.execute (uri_table)
cursor.execute(triple_table)
database.commit ()

# Initialize data structures that are needed and a variable to count lines
errorCheckOutput = [".", []]
params = []
previousPunc = "."

for line in f:

	# Skip all empty lines
	if (len(line.split()) == 0):
		continue

	# Fixing spaces: make every space between words a tab
	# The overhead of this is that objects that are strings with spaces have tabs rather than spaces between
	# 	words. This is fixed later
	words = line.split()
	line = ""
	for i in words:
		line = line + i + "\t"
	# Remove the last tab after the punctuation (".", ",", ";")
	line = line[:len(line)-1]
	
	# Check of each line ends with either a (. or , or ;). Return error if it doesn't
	try:
		assert (line[-1] == "." or line[-1] == "," or line[-1] == ";")
	except AssertionError:
		print ("Line " + line + "must end with '.' or ';' or ',' \nQuitting...")
		os.system ("make clean")
		sys.exit()

	# Check for proper spelling of "@prefix" and that prefix line has correct number of words (4)
	if (line[0] == "@"):
		try:
			assert (line [0:7] == "@prefix")
		except AssertionError:
			print ("Spelling error: '@prefix' not spelled correctly in line \n" + line + "\nQuitting...")
			os.system ("make clean")
			sys.exit()
		try:
			assert (len(line.split()) == 4)
		except AssertionError:
			print ("Missing some arguments in line \n" + line + "\nQuitting...")
			os.system ("make clean")
			sys.exit()

	# errorCheckOutput is a list containing only 2 things:
	# 	the first element is a string of the most recent punctuation (".", ".", ";"). recentPunc (recent punctuation) is set to this element
	# 	the second element is a list of the all the parameters listed in line (ex. if the most recent punctuation (of the previous line) 
	# 		was a semicolon, then the second element would only have two elements, the predicate and the object)
	previousPunc = errorCheckOutput[0]
	errorCheckOutput = error_check (line, previousPunc, line.split())

	# params contains all elements required but not present. If the previous line ended witth a comma, then params would hold its subject and predicate,
	# 	as the current line would only have the object specified. If the previous line ended with a semicolon, then params would hold only the subject.
	# 	Likewise, if the previous line ended with a period, then params would hold nothing
	new = errorCheckOutput[1]
	params = parse_execute (line, cursor, database, params, new, previousPunc)
	
database.commit ()
database.close()

os.system ("cp " + dbName + " ../Part\ 3/")
f.close()
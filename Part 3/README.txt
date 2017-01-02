Error checking in q9.py is not as extensive as in q8.py, so we have included a
sample query to specify the syntax (which is identical to SPARQL)

PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX schema: <http://schema.org/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT * WHERE {
	
  	dbr:Edmonton dbo:testing ?number .
  	dbr:Vancouver dbo:testing ?number2 .
	FILTER (?number<"8"^^xsd:integer) .
	FILTER (?number2 > "4"^^xsd:integer) .
} 
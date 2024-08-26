#makefile for cleaning and running a python script

#cleaning the directory
clean:
	rm -rf log.txt tor flask.log

#running the python script
run:
	python3 main.py
ERL_FILES=$(wildcard *.erl)
BEAM_FILES=$(ERL_FILES:.erl=.beam)

all: $(BEAM_FILES)

%.beam: %.erl
	erlc $<

clean:
	rm -f *.beam *.erl

compile:
	python3 exemplo.py

potion_tests:
	python3 -m unittest discover -s tests

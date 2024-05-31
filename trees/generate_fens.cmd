universe	= vanilla
executable	= venv/bin/python

output		= condor/out/$(Process)
stream_output	= True
error		= condor/err/$(Process)
log 		= condor/log

arguments	= main.py ./stockfish condor/fens/puzzles_$(Process).csv

# queue 1917
queue 1

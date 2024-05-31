universe	= vanilla
executable	= install_and_run.sh

should_transfer_files	= IF_NEEDED
transfer_input_files	= requirements.txt, condor/fens/puzzles_$(Process).csv, main.py, stockfish

output		= condor/out/$(Process)
stream_output	= True
error		= condor/err/$(Process)
log 		= condor/log

arguments	= condor/fens/puzzles_$(Process).csv

queue 1917

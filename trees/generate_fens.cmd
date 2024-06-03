universe	= vanilla
executable	= install_and_run.sh

# Run only on lab machines
requirements	= regexp("^(ash|beech|cedar|curve|edge|maple|oak|pixel|ray|texel|vertex|willow)[0-9]{2}", TARGET.Machine)

should_transfer_files	= IF_NEEDED
transfer_input_files	= requirements.txt, condor/fens/puzzles_$(Process).csv, main.py, stockfish

output		= condor/out/$(Process)
stream_output	= True
error		= condor/err/$(Process)
log 		= condor/log/$(Process)

arguments	= condor/fens/puzzles_$(Process).csv

queue 1917


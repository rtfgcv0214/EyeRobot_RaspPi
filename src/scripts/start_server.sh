#!/bin/bash

SESSION=wifi_clients

tmux new-session -d -s $SESSION

# left pane: video
tmux send-keys -t $SESSION:0 "python3 -m wifi.wifi_video_server" C-m

tmux split-window -h -t $SESSION

# second pane: uart
tmux send-keys -t $SESSION:0.1 "python3 -m wifi.wifi_server" C-m

tmux select-layout -t $SESSION tiled

tmux attach -t $SESSION
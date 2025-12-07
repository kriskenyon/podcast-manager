#!/bin/bash
# Simple script to run the podcast manager without installing

export PYTHONPATH=src
python3 -m podcastmanager.main "$@"

#!/bin/bash

python record.py -u -d 1 > $HOME/`date +\%Y\%m\%d\%H\%M\%S*`-cron.log 2>&1
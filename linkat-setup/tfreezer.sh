#!/bin/bash
LOG="/var/log/tfreezer.log"

date >> $LOG
/usr/bin/tfreezer -r $USER >> $LOG

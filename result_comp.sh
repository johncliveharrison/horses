#!/bin/bash
echo $1
#rm result-summary.txt;
for ii in $(seq 0 100);
do grep -r -A 2 "^$ii " results/$1* >> result-summary.txt;
done

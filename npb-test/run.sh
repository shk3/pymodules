#!/bin/bash

NCPUS=$1
shift

export OMP_NUM_THREADS=$NCPUS
export GOMP_CPU_AFFINITY=0-$((NCPUS-1))

env | grep OMP

for n in {1..10}
do
	for dir in $@
	do
		echo "simd:$dir"
		$dir/bin/bt.A.x
		$dir/bin/lu.A.x
		$dir/bin/sp.A.x
	done
done


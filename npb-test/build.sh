#!/bin/bash

set -e

module load gcc/4.7.2

build() {
	tar xf NPB3.3.1.tar.gz NPB3.3.1/NPB3.3-OMP
	mv NPB3.3.1/NPB3.3-OMP $1
	cp make.def $1/config/
	cd $1
	make bt CLASS=A SSE_FLAG=$2 CC=$3 F77=$4
	make sp CLASS=A SSE_FLAG=$2 CC=$3 F77=$4
	make lu CLASS=A SSE_FLAG=$2 CC=$3 F77=$4
	cd ..
}

build sse3 -msse3 gcc gfortran
build sse4a -msse4a gcc gfortran
build avx -mavx gcc gfortran

build sse3-intel -xSSE3 icc ifort
build sse4.2-intel -xSSE4.2 icc ifort
build avx-intel -xAVX icc ifort


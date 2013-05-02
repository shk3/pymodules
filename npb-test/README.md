Performance of NAS Parallel Benchmarks with SSE3 vs. Higher SSE Instructions
============================================================================

The build.sh script will build SSE3, SSE4.2, SSE4a, and AVX versions of the
three pseudo-applications (bt, sp, lu) from the OpenMP NAS Parallel Benchmarks.
Some versions use gcc 4.7.2 and others ifort 2011.11.339.

The run.sh script will run 10 trials of the A problem size for two
different versions, e.g.

    ./run.sh 16 sse3 avx

where the first argument is the number of cores, and the next two arguments
are the directories containing the build variants.

On the Oscar cluster at CCV, we ran this script on the appropriate nodes to
generate four log files:

    ./run.sh 16 sse3-intel avx-intel >"Xeon E5-2670.txt"
    ./run.sh 8 sse3-intel sse4.2-intel >"Xeon E5540.txt"
    ./run.sh 16 sse3 sse4a >"Opteron 8382.txt"
    ./run.sh 64 sse3 avx >"Opteron 6282SE.txt"

Figure 2 in our LISA'13 submission was generated from these log files with
the plot.py script:

    ./plot.py *.txt

This script picks the trial with the maximum performace.  It requires
matplotlib 1.2.0 and numpy 1.6.1.



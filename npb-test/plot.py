#!/usr/bin/env python

import os
import sys

from itertools import chain
from numpy import arange
from matplotlib.pyplot import *
from matplotlib.ticker import FixedLocator, FormatStrFormatter

data = {}
colors = {}
labels = {}

for filename in sys.argv[1:]:
	group = os.path.splitext(filename)[0]
	data[group] = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
	n = 0
	for line in open(filename):
		if line.startswith("simd:sse3"):
			simd = 0
		elif line.startswith("simd:sse4a"):
			simd = 1
			colors[group] = 'r'
			labels[group] = 'SSE4a'
		elif line.startswith("simd:sse4.2"):
			simd = 1
			colors[group] = 'b'
			labels[group] = 'SSE4.2'
		elif line.startswith("simd:avx"):
			simd = 1
			colors[group] = 'g'
			labels[group] = 'AVX'
		elif line.startswith(" Mop/s total"):
			mops = float(line.rstrip().split()[3]) / 1000.0
			data[group][n%3][simd] = max(mops, data[group][n%3][simd])
			n += 1

print data

# Plot

figure(figsize=(12,4))
title("Performance of NAS Parallel Benchmarks with SSE3 vs. Higher SSE Instructions", fontsize=15)

nbars = 2
bar_width = 0.7
bar_margin = 1.0

groups = sorted(data.keys(), reverse=True)
ngroups = len(groups)
group_margin = 3.0

plots = [
	"Block Tri-diagonal (BT)",
	"Lower-Upper Gauss-Seidel (LU)",
	"Scalar Penta-diagonal (SP)"]
nplots = len(plots)

group_size = ngroups * (nbars + bar_margin) - bar_margin
plot_size = nplots * (group_size + group_margin) + group_margin

xlim([0, plot_size])

xmajor = (group_size + group_margin) * arange(nplots) + group_margin + 0.5 * group_size

axis = []
for j in range(nplots):
	plot_offset = group_margin + j * (group_size + group_margin)
	for i in range(ngroups):
		axis.append(plot_offset + i * (nbars + bar_margin))

xminor = [x + 0.5 * nbars for x in axis]

ax = gca()
ax.xaxis.set_major_locator(FixedLocator(xmajor))
ax.set_xticklabels(map('\n\n\n{}'.format, plots), fontsize=13)
ax.xaxis.set_minor_locator(FixedLocator(xminor))
ax.set_xticklabels(
	[group.replace(' ', '\n') for group in groups] * nplots,
	minor=True, fontsize=10)
ax.tick_params(which='minor', direction='out', top='off')
for t in ax.xaxis.get_ticklines(): t.set_visible(False) 
for t in ax.yaxis.get_ticklines(): t.set_visible(False) 
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ylim([0,70])
ylabel('Billion Ops. / Sec. (Gop/s)')
grid(axis='y')

bar([x + 0.5 for x in axis],
	[data[g][p][0] for p in range(nplots) for g in groups],
	bar_width, align='center', alpha=0.8, linewidth=0, color='grey',
	label='SSE3')

#bar([x + 1.5 for x in axis],
#	[data[g][p][1] for p in range(nplots) for g in groups],
#	bar_width, align='center', alpha=0.8, linewidth=0,
#	color=[colors.get(g) for p in range(nplots) for g in groups],
#	label=[labels.get(g) for p in range(nplots) for g in groups])
for j in range(nplots):
	plot_offset = group_margin + j * (group_size + group_margin)
	for i, group in enumerate(groups):
		bar(plot_offset + i * (nbars + bar_margin) + 1.5,
			data[group][j][1], bar_width, align='center', alpha=0.8, linewidth=0,
			color=colors[group], label=labels[group])

legend(('SSE3', 'SSE4.2', 'AVX', 'SSE4a'), loc="upper right", fontsize=11)

tight_layout()
savefig('figure-nas.pdf')


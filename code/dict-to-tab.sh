#!/bin/bash
# Works for dict or inv.dict.
cat ../data/inv.dict | sed -r 's/(.*)	([0-9\.e-]+) (.*)(	.*)*/\1	\2	\3	\4/' | cut -d"	" -f1-4 > ../data/inv.dict.tab

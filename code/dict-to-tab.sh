#!/bin/bash
#cat ../data/google-crosswikis/inv.dict | sed -r 's/(.*)	([0-9\.e-]+) (.*)(	.*)*/\1	\2	\3	\4/' | cut -d"	" -f1-4 > ../data/google-crosswikis/inv.dict.tab

cat ../data/google-crosswikis/dictionary | sed -r 's/(.*)	([0-9\.e-]+) (\S*)( .*)*/\1	\2	\3	\4/' | cut -d"	" -f1-4 > ../data/google-crosswikis/dictionary.tab

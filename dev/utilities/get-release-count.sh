#!/usr/bin/env bash

curl https://api.github.com/repos/sbmlteam/moccasin/releases 2>&1 | \
gawk -- '
$0 ~ "       \"name\":" {printf $2}
$0 ~ "       \"download_count\":" {print " " $2}
'
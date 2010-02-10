#!/bin/sh
err=3
while test "$err" -eq 3 ; do
    python manage.py --reload $*
    err="$?"
done

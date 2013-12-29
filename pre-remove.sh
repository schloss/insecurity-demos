#!/bin/sh
if [ "$1" = "remove" ]; then
rm /usr/share/insecuritydemos/*.pyc
rm /usr/share/insecuritydemos/demos/*.pyc
fi

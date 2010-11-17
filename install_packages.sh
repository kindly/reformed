#!/bin/sh

######################################################
#                                                    #
#   Install the required python packages for rebase  #
#                                                    #
######################################################


vflag=no
hflag=no
set -- $(getopt -o vh -l help -l verbose -- "$@")
while [ $# -gt 0 ]
do
    case "$1" in
    (-v) vflag=yes;;
    (--verbose) vflag=yes;;
    (-h) hflag=yes;;
    (--help) hflag=yes;;
    (--) shift; break;;
    (-*) echo "$0: error - unrecognized option $1" 1>&2; exit 1;;
    (*)  break;;
    esac
    shift
done

if [ "$hflag" = "yes" ]; then
  echo "Usage: install_packages [options]"
  echo "Install the python dependencies for rebase."
  echo "  -h, --help       This small usage guide"
  echo "  -v, --verbose    Verbose show pip output"
  exit 1
fi

# Make sure only root can run our script
echo "$UID"

exit 1

if [ $EUID -ne 0 ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# check pip installed
type -P pip &>/dev/null || { echo "pip python package not found please install and run again" >&2; exit 1; }

# do pip install of packages
echo "installing python dependencies this may take some time"
while read line
do
  echo -n $line
  if [ "$vflag" = "yes" ]; then
    pip install $line 
  else
    pip install -q $line 
    echo " installed"
  fi
done < rebase-requirements.txt


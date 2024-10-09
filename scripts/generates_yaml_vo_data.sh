#!/bin/bash
# generates yaml config files for VO configuration

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTDIR
source vault/token.sh
./update-vo-config -b ../generated_vars  -t $EGI_TOKEN --use-pickle

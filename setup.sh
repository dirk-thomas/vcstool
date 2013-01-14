if [ "$BASH_SOURCE" ]; then
  BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  SCRIPT=$(readlink -f $0)
  BASEDIR=$(dirname $SCRIPT)
  if [ ! -f "$BASEDIR/setup.sh" ]; then
    echo "In non-bash shells the setup.sh file must be sourced from the same directory"
    return 1
  fi
fi

export PATH=$BASEDIR/scripts:$PATH
export PYTHONPATH=$BASEDIR:$PYTHONPATH

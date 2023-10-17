#!/bin/bash

THISDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASEDIR=$THISDIR/..
rm $BASEDIR/dist/*.whl $BASEDIR/dist/*.tar.gz

virtualenv $BASEDIR/pyvirtualenv
source $BASEDIR/pyvirtualenv/bin/activate

pip install -r $BASEDIR/requirements.txt
pip install tox

python -m tox --root $BASEDIR/
if [ $? -ne 0 ]; then
    echo "FAILED: Cannot release a broken version!"
    exit 127
fi

pip install twine build
python -m build --outdir $BASEDIR/dist/ $BASEDIR/

pip install --force-reinstall $BASEDIR/dist/pyangbind-*.whl
export PYBINDPLUGIN=`/usr/bin/env python -c \
'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))'`
if ! pyang -V --plugindir $PYBINDPLUGIN -f pybind -o $BASEDIR/tests/base-binding-out.py $BASEDIR/tests/base-test.yang; then
    echo "FAILED: cannot bind with pyang"
    exit 126
fi

python -m twine upload -s $BASEDIR/dist/pyangbind*

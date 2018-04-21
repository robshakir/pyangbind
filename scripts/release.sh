#!/bin/bash

THISDIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rm $THISDIR/../dist/*.whl $THISDIR/../dist/*.tar.gz

python $THISDIR/../setup.py bdist_wheel sdist

coverage run setup.py test -q

if [ $? -ne 0 ]; then
    echo "FAILED: Cannot release a broken version!"
    exit 127
fi

twine upload -s $THISDIR/../dist/pyangbind*

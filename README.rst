virtual-extruders
=================

.. image:: https://img.shields.io/pypi/v/virtual-extruders.svg
   :target: https://pypi.python.org/pypi/virtual-extruders
.. image:: https://img.shields.io/pypi/status/virtual-extruders.svg
   :target: https://pypi.python.org/pypi/virtual-extruders
.. image:: https://img.shields.io/pypi/format/virtual-extruders.svg
   :target: https://pypi.python.org/pypi/virtual-extruders
.. image:: https://img.shields.io/pypi/pyversions/virtual-extruders.svg
   :target: https://python.org
.. image:: https://img.shields.io/pypi/l/virtual-extruders.svg
   :target: https://github.com/stygian-violet/virtual-extruders/blob/master/LICENSE

Overview
--------

Convert G-code for a multi-extruder 3D printer to single extruder,
substituting tool selection with manual filament change.

Requirements
------------

- `Python <https://www.python.org/>`__ >= 3.10

Installation
------------

Pip
^^^

.. code-block:: bash

    pip install virtual-extruders

Portable
^^^^^^^^

Copy `virtual_extruders.py
<https://github.com/stygian-violet/virtual-extruders/blob/master/virtual_extruders.py>`__
to any directory and make it executable.

.. code-block:: bash

    install -m755 -D -t ~/.config/PrusaSlicer/scripts virtual_extruders.py

Usage
-----

CLI
^^^

The command-line interface can be used
with ``virtual-extruders`` if it was installed with a package manager
or with ``/path/to/virtual_extruders.py`` otherwise.

.. code-block:: console

    > ./virtual_extruders.py -h
    usage: virtual_extruders.py [-h] [-V] [-i] [-f] [-g GCODE [GCODE ...]] file

    positional arguments:
      file                  g-code file

    options:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      -i, --in-place        edit the file in place
      -f, --skip-first      skip first tool change
      -g, --tool-change-gcode GCODE [GCODE ...]
                            set tool change g-code (default: [';TOOL_CHANGE',
                            'M117 Insert filament [next_extruder] and resume
                            printing', 'M600', ';TOOL_CHANGE_END'])

PrusaSlicer
^^^^^^^^^^^

To use this program as a post-processing script in PrusaSlicer,
add the following line to the **Post-processing scripts** parameter
in **Print Settings** → **Output options**:

.. code-block:: bash

    virtual-extruders -i -f

For more detailed configuration instructions and a test model, see
`How to change filament mid-layer
<https://www.printables.com/model/1908968-how-to-change-filament-mid-layer>`__.

Development
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

    python -m venv env
    source env/bin/activate
    pip install --group dev -e .

Building
^^^^^^^^

.. code-block:: bash

    python -m build

Testing
^^^^^^^

.. code-block:: bash

    coverage run && coverage report

Linting
^^^^^^^

.. code-block:: bash

    ruff check && mypy

Uploading
^^^^^^^^^

.. code-block:: bash

    twine upload dist/*

Licenses
--------

-  `virtual-extruders <https://github.com/stygian-violet/virtual-extruders/blob/master/LICENSE>`__

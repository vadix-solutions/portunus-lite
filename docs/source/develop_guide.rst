Development Guide
===============================

This is for internal use only! (We like to keep our docs in one place)

Running Tests
-------------

Run the following ``bash ./scripts/run_tests_unit.sh``

* To run tests without coverage (or to override how coverrage is run), override the environment variable ``COV_TEST``
* To run a particular test, specify the full path and module.
* To disable stdout/err capture, use ``-s`` flag

All of the above together:

``COV_TEST='' bash ./scripts/run_tests_unit.sh -s id_rbac/tests/test_access_graph.py::TestAccessDAGPerformance::test_dense_dag``

Getting log output
*****************

To get log output at the CLI level, add ``--log-cli-level=INFO``

Otherwise, log output is written to ``pytest.log`` as defined in ``pytest.ini`` - you may need to be in the container to view that file

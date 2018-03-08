## Contributing to PyangBind

Contributions to PyangBind are very welcome, either directly via pull requests, or as feature suggestions or bug reports.

A couple of requests:

 * Code style is currently intended to be PEP-8 compliant, however, the following rules are ignored:
   * E111 - indentation is not a multiple of four
   * E114 - indentation is not a multiple of four (comment)
   * E121 - continuation line under-indented for hanging indent
   * E126 - continuation line over-indented for hanging indent
   * E127 - continuation line over-indented for visual indent
   * E128 - continuation line under-indented for visual indent
   * E131 - continuation line unaligned for hanging indent
 * The standard indentation in PyangBind code is 2 spaces (**not** 4)
 * Continued lines are made to be subjectively aesthetically pleasing/readable.
 * Please run tests/run.sh and check that all the tests pass if you're changing code. New tests are much appreciated. If you'd like to use a different test framework, that's fine -- just please ensure that `TESTNAME/run.py` runs the tests.
 * If you have an issue with generated code/odd errors during build -- please do just e-mail this over or open an issue. If you can't share the YANG itself, then anonymised YANG is very welcome.
 * If you'd like to discuss the best design for a feature, or don't get how a feature fits in, please open an issue, or send e-mail.

And most of all, thanks for contributions :-)

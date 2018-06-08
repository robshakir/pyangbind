## Contributing to PyangBind

Contributions to PyangBind are very welcome, either directly via pull requests, or as feature suggestions or bug reports.

### Code Style

To avoid unnecessary discussions about coding style we are currently enforcing it with [black](https://github.com/ambv/black). Before pushing code:

* make sure you are running the correct version of `black` as per `requirements.DEVELOPER.txt`.
* reformat your code with `black` passing the option `--line-length 119`.

### Testing

 * New code should be covered by tests, and run under both Python 2 and 3.
 * To ease the testing of generated bindings, there is the `tests.base.PyangBindTestCase` class which
 you may subclass in order to automate the process. A simple example of its usage can be seen in
 `tests/strings/run.py`.
 * Tests can be run via the `tox` command, or `setup.py test`.

### Other Issues

 * If you have an issue with generated code/odd errors during build -- please do just e-mail this over or open an issue.
   If you can't share the YANG itself, then anonymised YANG is very welcome.
 * If you'd like to discuss the best design for a feature, or don't get how a feature fits in, please open an issue,
   send an e-mail, or join us in the #pyangbind channel on the
   [NetworkToCode Slack](https://networktocode.slack.com/).

And most of all, thanks for contributions :-)

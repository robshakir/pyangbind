## Changelog

25-05-2015 - tag: rel.00:

	* Initial release of PyangBind outside of BT.

09-06-2015 - tag: rel.01-alpha.01:

	* Merge of xpath-helper-04 into master.
	* Support for leafref with XPath lookups.

04-09-2015 - tag: rel.02:

	* Merge of serialiser-11 into master.
	* Support for serialising to JSON, extensions, refactored xpathhelper, and a number of new types.

31-12-2015 - 0.1.0

	* Adopt semantic versioning.
	* First release packaged for PyPi

11-01-2016 - 0.1.3

	* Final test release to PyPI's test repo.
	* To be released as 0.2.0.

11-01-2016 - 0.2.0
  * Released to PyPI.

15-03-2016 - 0.3.1
  * Adds support for serialising and deserialising to IETF JSON.
  * Tests against Juniper Networks' code - thanks especially to Pallavi Mahajan, and Nilesh Simaria
    at Juniper for their example output.
  * Adds support for 'and' and 'or' in XPATH expressions.
  * Adds support for multiple predicates in an XPATH expression (i.e., element[one='1'][two='2'])
  * Changes the default for a require-instance leafref to true (COMPATIBILITY WARNING) -  note that
    no special version number is given here since we're still in a 0.x.y version, 1.0.x release
    should follow merging open pullreqs.
  * Makes pybindJSON methods static methods, so class instantiation is not required (COMPATIBILITY
    WARNING).
  * Adds support for carrying the namespace and defined module in a class.
  * Adds a metadata element to carry JSON metadata that was received.

16-03-2016 - 0.3.2
  * Fixes an issue relating to to identity value inheritance.
def xml_tree_equivalence(e1, e2):
    """
    Rough XML comparison function based on https://stackoverflow.com/a/24349916/1294458.
    This is necessary to provide some sort of structural equivalence of a generated XML
    tree; however there is no XML deserialisation implementation yet. A naive text comparison
    fails because it seems it enforces ordering, which seems to vary between python versions
    etc. Strictly speaking, I think, only the *leaf-list* element mandates ordering.. this
    function uses simple sorting on tag name, which I think, should maintain the relative
    order of these elements.
    """
    if e1.tag != e2.tag:
        return False
    if e1.text != e2.text:
        return False
    if e1.tail != e2.tail:
        return False
    if e1.attrib != e2.attrib:
        return False
    if len(e1) != len(e2):
        return False
    e1_children = sorted(e1.getchildren(), key=lambda x: x.tag)
    e2_children = sorted(e2.getchildren(), key=lambda x: x.tag)
    if len(e1_children) != len(e2_children):
        return False
    return all(xml_tree_equivalence(c1, c2) for c1, c2 in zip(e1_children, e2_children))

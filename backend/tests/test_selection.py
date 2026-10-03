import pytest
from app.models import Interval,SyllabusNode
from app.syllabus.selection import normalize,subtract,toggle_node,deepest_topic

def I(start,end):return Interval(start=start,end=end)
def test_selecting_children_excludes_parent_gaps():
    assert normalize([I(120,240),I(360,480)]) == [I(120,240),I(360,480)]
def test_parent_minus_child_retains_intervening_material():
    assert subtract([I(0,600)],[I(120,240)]) == [I(0,120),I(240,600)]
def test_overlapping_and_adjacent_ranges_are_not_duplicated():
    assert normalize([I(5,10),I(0,7),I(10,12)]) == [I(0,12)]
def test_node_toggle_respects_full_parent_and_partial_children():
    parent=SyllabusNode(id='p',title='Parent',start=0,end=600)
    child=SyllabusNode(id='c',parent_id='p',title='Child',start=120,end=240)
    assert toggle_node(toggle_node([],parent,True),child,False) == [I(0,120),I(240,600)]
def test_exact_child_end_belongs_to_parent():
    nodes=[SyllabusNode(id='p',title='Parent',start=0,end=600),SyllabusNode(id='c',parent_id='p',title='Child',start=120,end=240)]
    assert deepest_topic(nodes,239)=='c'
    assert deepest_topic(nodes,240)=='p'
    with pytest.raises(ValueError):deepest_topic(nodes,600)

# tests/unit/test_models/test_dependency_graph.py
import pytest
import networkx as nx
from excel_processor.models.dependency_graph import DependencyGraph

def test_dependency_graph_creation():
    graph = DependencyGraph()
    
    # Add nodes
    graph.add_node("Sheet1.A", is_formula=False)
    graph.add_node("Sheet1.B", is_formula=True, formula="=A*2")
    
    # Add dependency
    graph.add_dependency("Sheet1.B", "Sheet1.A")
    
    assert "Sheet1.A" in graph.graph.nodes
    assert "Sheet1.B" in graph.graph.nodes
    assert ("Sheet1.B", "Sheet1.A") in graph.graph.edges

def test_dependency_graph_processing_order():
    graph = DependencyGraph()
    
    # Create a simple dependency chain
    graph.add_node("Sheet1.A", is_formula=False)
    graph.add_node("Sheet1.B", is_formula=True, formula="=A*2")
    graph.add_node("Sheet1.C", is_formula=True, formula="=B+1")
    
    graph.add_dependency("Sheet1.B", "Sheet1.A")
    graph.add_dependency("Sheet1.C", "Sheet1.B")
    
    order = graph.get_processing_order()
    
    # Verify correct processing order
    assert order.index("Sheet1.A") < order.index("Sheet1.B")
    assert order.index("Sheet1.B") < order.index("Sheet1.C")

def test_circular_dependency_detection():
    graph = DependencyGraph()
    
    # Create circular dependency
    graph.add_node("Sheet1.A", is_formula=True, formula="=B+1")
    graph.add_node("Sheet1.B", is_formula=True, formula="=A*2")
    
    graph.add_dependency("Sheet1.A", "Sheet1.B")
    graph.add_dependency("Sheet1.B", "Sheet1.A")
    
    with pytest.raises(ValueError, match="Circular dependency: Sheet1.A -> Sheet1.B -> Sheet1.A"):
        graph.get_processing_order()

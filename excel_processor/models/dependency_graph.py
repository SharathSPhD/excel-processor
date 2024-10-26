# excel_processor/models/dependency_graph.py
from typing import Dict, Set, List, Optional, Any
import networkx as nx
from ..models.worksheet import WorksheetInfo

class DependencyNode:
    """Represents a node in the dependency graph."""
    def __init__(self, 
                 sheet_name: str, 
                 column_name: str, 
                 is_formula: bool = False,
                 formula: Optional[str] = None):
        self.sheet_name = sheet_name
        self.column_name = column_name
        self.is_formula = is_formula
        self.formula = formula
        self.dependencies: Set[str] = set()
    
    def __str__(self) -> str:
        return f"{self.sheet_name}.{self.column_name}"

class DependencyGraph:
    """Manages dependencies between Excel formulas and columns."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._sheet_data: Dict[str, WorksheetInfo] = {}
        self._node_cache: Dict[str, DependencyNode] = {}
    
    def add_node(self, 
                 node_id: str, 
                 is_formula: bool = False,
                 formula: Optional[str] = None):
        """Add a node to the dependency graph."""
        try:
            sheet_name, column_name = node_id.split('.')
            node = DependencyNode(sheet_name, column_name, is_formula, formula)
            self._node_cache[node_id] = node
            
            self.graph.add_node(
                node_id,
                is_formula=is_formula,
                formula=formula
            )
            
        except ValueError:
            raise ValueError(f"Invalid node ID format: {node_id}")
    
    def add_dependency(self, from_node: str, to_node: str):
        """Add a dependency edge between nodes."""
        if from_node not in self.graph:
            raise ValueError(f"Source node not found: {from_node}")
        if to_node not in self.graph:
            raise ValueError(f"Target node not found: {to_node}")
            
        self.graph.add_edge(from_node, to_node)
        self._node_cache[from_node].dependencies.add(to_node)
    
    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get all dependencies for a node."""
        if node_id not in self.graph:
            raise ValueError(f"Node not found: {node_id}")
            
        return set(nx.descendants(self.graph, node_id))
    
    def get_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node."""
        if node_id not in self.graph:
            raise ValueError(f"Node not found: {node_id}")
            
        return set(nx.ancestors(self.graph, node_id))
    
    def get_processing_order(self) -> List[str]:
        """Get nodes in topological order for processing."""
        try:
            self.validate()  # Ensure graph is valid
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("Cannot determine processing order: circular dependencies")
    
    def validate(self) -> List[str]:
        """Validate the dependency graph."""
        errors = []
        
        try:
            # Check for cycles
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                for cycle in cycles:
                    cycle_str = " -> ".join(cycle + [cycle[0]])
                    errors.append(f"Circular dependency: {cycle_str}")
            
            # Check for missing references
            for node_id in self.graph.nodes():
                node = self._node_cache[node_id]
                sheet = node.sheet_name
                
                if sheet not in self._sheet_data:
                    errors.append(f"Missing sheet: {sheet}")
                    continue
                
                if node.column_name not in self._sheet_data[sheet].data.columns:
                    errors.append(f"Missing column: {node.column_name} in sheet {sheet}")
            
            # Validate formula dependencies
            for node_id, node in self._node_cache.items():
                if node.is_formula:
                    deps = node.dependencies
                    for dep in deps:
                        if dep not in self.graph:
                            errors.append(
                                f"Formula in {node_id} references non-existent "
                                f"dependency: {dep}"
                            )
            
        except Exception as e:
            errors.append(f"Error validating dependency graph: {str(e)}")
        
        return errors
    
    def add_worksheet(self, worksheet: WorksheetInfo):
        """Add worksheet information to the graph."""
        self._sheet_data[worksheet.name] = worksheet
        
        # Add nodes for input columns
        for col in worksheet.input_columns:
            node_id = f"{worksheet.name}.{col}"
            self.add_node(node_id, is_formula=False)
        
        # Add nodes for formula columns
        for col, formula in worksheet.formulas.items():
            node_id = f"{worksheet.name}.{col}"
            self.add_node(node_id, is_formula=True, formula=formula)
    
    def get_node_info(self, node_id: str) -> Dict[str, Any]:
        """Get detailed information about a node."""
        if node_id not in self._node_cache:
            raise ValueError(f"Node not found: {node_id}")
            
        node = self._node_cache[node_id]
        return {
            'sheet_name': node.sheet_name,
            'column_name': node.column_name,
            'is_formula': node.is_formula,
            'formula': node.formula,
            'dependencies': list(node.dependencies),
            'dependents': list(self.get_dependents(node_id))
        }
    
    def visualize(self) -> str:
        """Generate a DOT representation of the graph."""
        try:
            import graphviz
            dot = graphviz.Digraph(comment='Excel Dependencies')
            
            # Add nodes
            for node_id in self.graph.nodes():
                node = self._node_cache[node_id]
                label = f"{node_id}\n{node.formula if node.formula else 'Input'}"
                shape = 'box' if node.is_formula else 'ellipse'
                dot.node(node_id, label, shape=shape)
            
            # Add edges
            for edge in self.graph.edges():
                dot.edge(edge[0], edge[1])
            
            return dot.source
            
        except ImportError:
            return "graphviz package not available for visualization"

    def __str__(self) -> str:
        """String representation of the graph."""
        return (f"DependencyGraph with {len(self.graph.nodes())} nodes and "
                f"{len(self.graph.edges())} dependencies")
    
    def clear(self):
        """Clear all graph data."""
        self.graph.clear()
        self._sheet_data.clear()
        self._node_cache.clear()
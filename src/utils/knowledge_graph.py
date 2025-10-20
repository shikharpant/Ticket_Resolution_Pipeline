"""
Knowledge graph utilities for GST concept relationships
"""

import json
import logging
import sqlite3
import networkx as nx
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LightweightKnowledgeGraph:
    """Embedded knowledge graph retriever"""

    def __init__(self, db_path: str = "./knowledge_graph.db"):
        self.db_path = Path(db_path)
        self.graph = nx.DiGraph()
        self.conn = None

        # Initialize connection if database exists
        if self.db_path.exists():
            self.conn = sqlite3.connect(str(self.db_path))
        else:
            logger.warning(f"⚠️ Graph database not found: {db_path}")

    def load(self):
        """Load graph from SQLite database"""
        if not self.conn:
            logger.error("❌ No database connection for knowledge graph")
            return

        try:
            # Load nodes - FIXED: Avoid 'type' keyword conflict
            cursor = self.conn.execute("SELECT id, type, label, metadata FROM nodes")
            for node_id, node_type, label, metadata in cursor:
                meta = json.loads(metadata) if metadata else {}
                meta['entity_type'] = node_type  # Store as 'entity_type' instead of 'type'
                meta['label'] = label
                self.graph.add_node(node_id, **meta)

            # Load edges
            cursor = self.conn.execute("SELECT source, target, relation, weight FROM edges")
            for source, target, relation, weight in cursor:
                self.graph.add_edge(source, target, relation=relation, weight=weight)

            logger.info(f"✅ Graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        except Exception as e:
            logger.error(f"❌ Failed to load graph: {e}")

    def find_related(self, entity: str, max_depth: int = 2, max_results: int = 20) -> list:
        """Find entities related to entity via BFS traversal"""
        if entity not in self.graph:
            return []

        related = []
        visited = set([entity])
        current_level = [(entity, 0)]

        while current_level and len(related) < max_results:
            next_level = []

            for node, depth in current_level:
                if depth >= max_depth:
                    continue

                # Get neighbors
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)

                        # Get edge info
                        edge_data = self.graph.get_edge_data(node, neighbor)
                        relation = edge_data.get('relation', 'related_to')
                        weight = edge_data.get('weight', 1.0)

                        # Get node info
                        node_data = self.graph.nodes.get(neighbor, {})

                        related.append({
                            'entity': neighbor,
                            'relation': relation,
                            'weight': weight,
                            'depth': depth + 1,
                            'type': node_data.get('entity_type', 'unknown'),
                            'label': node_data.get('label', neighbor)
                        })

                        if len(related) >= max_results:
                            break
                        next_level.append((neighbor, depth + 1))

            current_level = next_level

        # Sort by weight and depth
        related.sort(key=lambda x: (-x['weight'], x['depth']))
        return related[:max_results]

    def get_entity_info(self, entity: str) -> dict:
        """Return node metadata for an entity"""
        if entity not in self.graph:
            return {}
        return dict(self.graph.nodes[entity])

    def close(self):
        if self.conn:
            self.conn.close()

    def get_stats(self) -> dict:
        """Get graph statistics"""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'is_loaded': self.graph.number_of_nodes() > 0
        }
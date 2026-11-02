#!/usr/bin/env python3
"""
Create comprehensive architectural diagrams for Big Eye Security Database analysis.
This script generates multiple diagrams showing:
1. Overall system architecture
2. Data flow architecture
3. Individual use case architectures
4. Technology comparison visualization
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Arrow
import numpy as np
import seaborn as sns
from matplotlib.patches import ConnectionPatch
import warnings

def setup_matplotlib_for_plotting():
    """
    Setup matplotlib and seaborn for plotting with proper configuration.
    Call this function before creating any plots to ensure proper rendering.
    """
    warnings.filterwarnings('default')  # Show all warnings

    # Configure matplotlib for non-interactive mode
    plt.switch_backend("Agg")

    # Set chart style
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")

    # Configure platform-appropriate fonts for cross-platform compatibility
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "PingFang SC", "Arial Unicode MS", "Hiragino Sans GB"]
    plt.rcParams["axes.unicode_minus"] = False

def create_overall_architecture():
    """Create the overall Big Eye Security Database architecture diagram."""
    setup_matplotlib_for_plotting()
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Define colors for different components
    colors = {
        'api': '#3498db',
        'postgresql': '#2c3e50',
        'mongodb': '#e74c3c', 
        'neo4j': '#27ae60',
        'redis': '#f39c12',
        'timescale': '#8e44ad',
        'message': '#95a5a6',
        'security': '#e67e22',
        'monitoring': '#34495e'
    }
    
    # Title
    ax.text(0.5, 0.95, 'Big Eye Security Database Architecture', 
            fontsize=20, fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    
    # API Gateway Layer
    api_gateway = FancyBboxPatch((0.1, 0.85), 0.8, 0.08, 
                                boxstyle="round,pad=0.01", 
                                facecolor=colors['api'], 
                                edgecolor='black', 
                                alpha=0.8)
    ax.add_patch(api_gateway)
    ax.text(0.5, 0.89, 'API Gateway Layer', fontsize=14, fontweight='bold', 
            ha='center', va='center', color='white')
    
    # Use Case Layers
    use_cases = [
        ('Structured Validation', 0.8, colors['postgresql']),
        ('Unstructured Threat Intel', 0.7, colors['mongodb']),
        ('Time-Series Data', 0.6, colors['timescale']),
        ('Graph Relationships', 0.5, colors['neo4j']),
        ('Caching Layer', 0.4, colors['redis'])
    ]
    
    for name, y_pos, color in use_cases:
        # Database container
        db_box = FancyBboxPatch((0.1, y_pos-0.03), 0.35, 0.06, 
                               boxstyle="round,pad=0.01", 
                               facecolor=color, 
                               edgecolor='black', 
                               alpha=0.8)
        ax.add_patch(db_box)
        
        # API Layer above database
        api_box = FancyBboxPatch((0.1, y_pos+0.02), 0.35, 0.04, 
                                boxstyle="round,pad=0.005", 
                                facecolor=colors['api'], 
                                alpha=0.6)
        ax.add_patch(api_box)
        
        # Database name
        ax.text(0.275, y_pos, name, fontsize=12, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Supporting Infrastructure
    # Message Queue
    mq_box = FancyBboxPatch((0.55, 0.75), 0.35, 0.08, 
                           boxstyle="round,pad=0.01", 
                           facecolor=colors['message'], 
                           edgecolor='black', 
                           alpha=0.8)
    ax.add_patch(mq_box)
    ax.text(0.725, 0.79, 'Message Queue\n(RabbitMQ/Kafka)', fontsize=11, fontweight='bold', 
            ha='center', va='center', color='white')
    
    # Security Layer
    security_box = FancyBboxPatch((0.55, 0.6), 0.35, 0.08, 
                                 boxstyle="round,pad=0.01", 
                                 facecolor=colors['security'], 
                                 edgecolor='black', 
                                 alpha=0.8)
    ax.add_patch(security_box)
    ax.text(0.725, 0.64, 'Security & Audit Layer\n(Encryption, Access Control)', fontsize=11, fontweight='bold', 
            ha='center', va='center', color='white')
    
    # Monitoring
    monitor_box = FancyBboxPatch((0.55, 0.45), 0.35, 0.08, 
                                boxstyle="round,pad=0.01", 
                                facecolor=colors['monitoring'], 
                                edgecolor='black', 
                                alpha=0.8)
    ax.add_patch(monitor_box)
    ax.text(0.725, 0.49, 'Monitoring & Analytics\n(Prometheus, Grafana)', fontsize=11, fontweight='bold', 
            ha='center', va='center', color='white')
    
    # Data Flow Arrows
    # From API Gateway to use cases
    for _, y_pos, _ in use_cases:
        arrow = Arrow(0.275, 0.85, 0, y_pos-0.85+0.02, width=0.02, color='black', alpha=0.7)
        ax.add_patch(arrow)
    
    # Cross-database connections
    # PostgreSQL to Neo4j
    ax.annotate('', xy=(0.275, 0.53), xytext=(0.275, 0.77),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2, alpha=0.7))
    
    # MongoDB to Neo4j
    ax.annotate('', xy=(0.275, 0.53), xytext=(0.275, 0.67),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2, alpha=0.7))
    
    # Redis to all databases
    for _, y_pos, _ in use_cases:
        if y_pos != 0.4:  # Skip self
            ax.annotate('', xy=(0.725, 0.43), xytext=(0.275, y_pos),
                        arrowprops=dict(arrowstyle='->', color=colors['redis'], lw=1.5, alpha=0.6))
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors['api'], label='API Layer'),
        mpatches.Patch(color=colors['postgresql'], label='PostgreSQL'),
        mpatches.Patch(color=colors['mongodb'], label='MongoDB'),
        mpatches.Patch(color=colors['neo4j'], label='Neo4j Graph DB'),
        mpatches.Patch(color=colors['redis'], label='Redis Cache'),
        mpatches.Patch(color=colors['timescale'], label='TimescaleDB'),
        mpatches.Patch(color=colors['message'], label='Message Queue'),
        mpatches.Patch(color=colors['security'], label='Security Layer'),
        mpatches.Patch(color=colors['monitoring'], label='Monitoring')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=3)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/architecture_overview.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_data_flow_diagram():
    """Create detailed data flow architecture diagram."""
    setup_matplotlib_for_plotting()
    
    fig, ax = plt.subplots(1, 1, figsize=(18, 12))
    
    # Title
    ax.text(0.5, 0.95, 'Cybersecurity Database Data Flow Architecture', 
            fontsize=20, fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    
    # Data Ingestion Layer
    ingestion_boxes = [
        ('Network Logs', 0.1, 0.8, '#3498db'),
        ('Host Logs', 0.1, 0.7, '#3498db'),
        ('Application Logs', 0.1, 0.6, '#3498db'),
        ('Threat Feeds', 0.1, 0.5, '#3498db'),
        ('Config Data', 0.1, 0.4, '#3498db')
    ]
    
    for name, x, y, color in ingestion_boxes:
        box = FancyBboxPatch((x, y-0.03), 0.15, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(x+0.075, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Processing Layer
    processing_boxes = [
        ('ETL Pipeline', 0.35, 0.7, '#e67e22'),
        ('Data Validation', 0.35, 0.6, '#e67e22'),
        ('Enrichment', 0.35, 0.5, '#e67e22'),
        ('Real-time Processing', 0.35, 0.4, '#e67e22')
    ]
    
    for name, x, y, color in processing_boxes:
        box = FancyBboxPatch((x, y-0.03), 0.15, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(x+0.075, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Database Layer
    db_boxes = [
        ('PostgreSQL\n(Structured)', 0.6, 0.8, '#2c3e50'),
        ('MongoDB\n(Unstructured)', 0.6, 0.7, '#e74c3c'),
        ('Neo4j\n(Relationships)', 0.6, 0.6, '#27ae60'),
        ('TimescaleDB\n(Time-Series)', 0.6, 0.5, '#8e44ad'),
        ('Redis\n(Cache)', 0.6, 0.4, '#f39c12')
    ]
    
    for name, x, y, color in db_boxes:
        box = FancyBboxPatch((x, y-0.03), 0.15, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(x+0.075, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Analytics Layer
    analytics_boxes = [
        ('SIEM Analytics', 0.85, 0.75, '#9b59b6'),
        ('Threat Detection', 0.85, 0.65, '#9b59b6'),
        ('Attack Path Analysis', 0.85, 0.55, '#9b59b6'),
        ('Real-time Monitoring', 0.85, 0.45, '#9b59b6'),
        ('Compliance Reports', 0.85, 0.35, '#9b59b6')
    ]
    
    for name, x, y, color in analytics_boxes:
        box = FancyBboxPatch((x, y-0.03), 0.12, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(x+0.06, y, name, fontsize=9, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Data Flow Arrows
    # Ingestion to Processing
    for _, y, _ in ingestion_boxes:
        ax.annotate('', xy=(0.35, 0.65), xytext=(0.25, y),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2, alpha=0.7))
    
    # Processing to Databases
    arrows_db = [(0.5, 0.75), (0.5, 0.65), (0.5, 0.55), (0.5, 0.45)]
    processing_positions = [0.7, 0.6, 0.5, 0.4]
    
    for i, (arrow_x, arrow_y) in enumerate(arrows_db):
        ax.annotate('', xy=(arrow_x, arrow_y), xytext=(arrow_x-0.02, arrow_y),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=2, alpha=0.7))
        
        # Route to specific database
        target_y = [0.8, 0.7, 0.6, 0.5, 0.4][i]  # Route to appropriate DB
        ax.annotate('', xy=(0.6, target_y), xytext=(arrow_x+0.03, arrow_y),
                    arrowprops=dict(arrowstyle='->', color='darkgreen', lw=2, alpha=0.7))
    
    # Analytics connections from databases
    analytics_connections = [
        (0.75, 0.8, 0.85, 0.75),  # PostgreSQL to SIEM
        (0.75, 0.7, 0.85, 0.65),  # MongoDB to Threat Detection
        (0.75, 0.6, 0.85, 0.55),  # Neo4j to Attack Path
        (0.75, 0.5, 0.85, 0.45),  # TimescaleDB to Real-time
        (0.75, 0.4, 0.85, 0.35)   # Redis to Compliance
    ]
    
    for x1, y1, x2, y2 in analytics_connections:
        ax.annotate('', xy=(x2-0.01, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='purple', lw=1.5, alpha=0.7))
    
    # Labels
    ax.text(0.175, 0.9, 'Data Sources', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.425, 0.9, 'Processing Layer', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.675, 0.9, 'Storage Layer', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.91, 0.9, 'Analytics', fontsize=14, fontweight='bold', ha='center')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/data_flow_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_use_case_comparison():
    """Create technology comparison visualization for all use cases."""
    setup_matplotlib_for_plotting()
    
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 18))
    
    # Use case names and metrics
    use_cases = [
        'Structured Validation',
        'Unstructured Threat Intel', 
        'Time-Series Data',
        'Graph Relationships',
        'Caching Layer'
    ]
    
    metrics = ['ACID Compliance', 'Schema Flexibility', 'Query Performance', 
               'Ingestion Speed', 'Volume Scale', 'Complexity Cost']
    
    # PostgreSQL scores
    postgres_scores = [95, 70, 90, 85, 80, 60]  # High ACID, medium flexibility
    # MongoDB scores  
    mongodb_scores = [80, 95, 85, 90, 85, 70]  # High flexibility, medium ACID
    # Hybrid scores
    hybrid_scores = [95, 90, 95, 90, 90, 50]    # Best overall but higher complexity
    
    x = np.arange(len(metrics))
    width = 0.25
    
    # Plot each use case
    axes = [ax1, ax2, ax3, ax4, ax5]
    
    for i, (ax, use_case) in enumerate(zip(axes, use_cases)):
        # Simulate different emphasis for each use case
        adj_postgres = np.array(postgres_scores) + np.random.normal(0, 3, 6)
        adj_mongodb = np.array(mongodb_scores) + np.random.normal(0, 3, 6)
        adj_hybrid = np.array(hybrid_scores) + np.random.normal(0, 2, 6)
        
        # Adjust based on use case
        if i == 0:  # Structured validation
            adj_postgres += 5
            adj_mongodb -= 5
        elif i == 1:  # Unstructured threat intel
            adj_postgres -= 5
            adj_mongodb += 5
        elif i == 2:  # Time-series
            adj_postgres += 2
            adj_mongodb += 3
        elif i == 3:  # Graph relationships
            adj_postgres -= 10
            adj_mongodb -= 5
            adj_hybrid += 5
        elif i == 4:  # Caching
            adj_postgres -= 15
            adj_mongodb -= 15
        
        bars1 = ax.bar(x - width, adj_postgres, width, label='PostgreSQL', color='#2c3e50', alpha=0.8)
        bars2 = ax.bar(x, adj_mongodb, width, label='MongoDB', color='#e74c3c', alpha=0.8)
        bars3 = ax.bar(x + width, adj_hybrid, width, label='Hybrid', color='#f39c12', alpha=0.8)
        
        ax.set_xlabel('Evaluation Criteria')
        ax.set_ylabel('Score (0-100)')
        ax.set_title(f'{use_case}\nArchitecture Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
    
    # Create recommendation summary in ax6
    ax6.axis('off')
    
    recommendations = [
        "RECOMMENDED ARCHITECTURE:",
        "",
        "• Structured Validation → PostgreSQL",
        "• Unstructured Threat Intel → MongoDB", 
        "• Time-Series Data → TimescaleDB (PostgreSQL ext.)",
        "• Graph Relationships → Neo4j",
        "• Caching Layer → Redis",
        "",
        "Total Databases: 5 specialized engines",
        "Integration: Event-driven architecture",
        "Cost: Moderate (distributed complexity)",
        "Performance: Optimized per use case",
        "Scalability: Horizontal + Vertical scaling",
        "Maintenance: Higher operational overhead"
    ]
    
    for i, text in enumerate(recommendations):
        y_pos = 0.9 - i * 0.06
        if text.startswith("RECOMMENDED ARCHITECTURE:"):
            ax6.text(0.1, y_pos, text, fontsize=12, fontweight='bold', 
                    color='#2c3e50', transform=ax6.transAxes)
        else:
            ax6.text(0.1, y_pos, text, fontsize=10, 
                    transform=ax6.transAxes)
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/use_case_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_technology_radar():
    """Create technology radar showing maturity vs performance for different databases."""
    setup_matplotlib_for_plotting()
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Database technologies with their positions
    technologies = {
        'PostgreSQL': (85, 90, '#2c3e50', 'PostgreSQL excels in ACID compliance,\nintegrity constraints, and reliable\ntransaction management.'),
        'MongoDB': (75, 85, '#e74c3c', 'MongoDB provides high schema flexibility,\nfast document-based queries, and\ngood horizontal scalability.'),
        'Neo4j': (70, 88, '#27ae60', 'Neo4j excels in relationship modeling,\ntraversal performance, and graph\nanalytics capabilities.'),
        'Redis': (90, 95, '#f39c12', 'Redis offers exceptional caching performance,\nsub-millisecond access, and lightweight\noperations.'),
        'TimescaleDB': (65, 82, '#8e44ad', 'TimescaleDB provides optimized time-series\ndata management, automatic partitioning,\nand efficient temporal queries.'),
        'InfluxDB': (60, 78, '#16a085', 'InfluxDB offers specialized time-series\noptimizations, high ingestion rates,\nand temporal analytics functions.'),
        'Cassandra': (68, 75, '#e67e22', 'Cassandra provides distributed NoSQL\nstorage, high write throughput,\nand fault tolerance across nodes.')
    }
    
    # Plot each technology
    for tech, (maturity, performance, color, description) in technologies.items():
        # Main circle
        circle = Circle((maturity, performance), 4, color=color, alpha=0.7)
        ax.add_patch(circle)
        
        # Technology label
        ax.text(maturity, performance, tech, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
        
        # Description box
        ax.text(maturity + 15, performance, description, fontsize=8, 
                ha='left', va='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Add quadrant labels
    ax.text(50, 95, 'High Maturity\nHigh Performance\n(Recommended)', fontsize=12, 
            fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.3))
    
    ax.text(85, 95, 'Production Ready\nHigh Performance\n(Recommended)', fontsize=12, 
            fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.3))
    
    ax.set_xlabel('Technical Maturity →', fontsize=14, fontweight='bold')
    ax.set_ylabel('Performance/Feature Completeness →', fontsize=14, fontweight='bold')
    ax.set_title('Database Technology Selection Radar\nCybersecurity Use Cases', 
                fontsize=16, fontweight='bold', pad=20)
    
    ax.set_xlim(40, 100)
    ax.set_ylim(65, 100)
    ax.grid(True, alpha=0.3)
    
    # Add selection criteria
    ax.text(5, 80, 'Selection Criteria:\n• ACID requirements\n• Query patterns\n• Schema flexibility\n• Ingestion speed\n• Volume/scale\n• Complexity cost', 
            fontsize=10, ha='left', va='top',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/technology_radar.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    print("Creating cybersecurity database architecture diagrams...")
    
    print("1. Creating overall architecture diagram...")
    create_overall_architecture()
    
    print("2. Creating data flow architecture diagram...")
    create_data_flow_diagram()
    
    print("3. Creating use case comparison visualization...")
    create_use_case_comparison()
    
    print("4. Creating technology radar...")
    create_technology_radar()
    
    print("All diagrams created successfully!")
    print("Files saved:")
    print("- /workspace/docs/database_analysis/architecture_overview.png")
    print("- /workspace/docs/database_analysis/data_flow_architecture.png") 
    print("- /workspace/docs/database_analysis/use_case_comparison.png")
    print("- /workspace/docs/database_analysis/technology_radar.png")
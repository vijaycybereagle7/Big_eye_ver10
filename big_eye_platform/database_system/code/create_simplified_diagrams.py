#!/usr/bin/env python3
"""
Create simplified Big Eye Security Database architecture diagrams.
This script generates essential diagrams for the database architecture analysis.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import numpy as np
import seaborn as sns
import warnings

def setup_matplotlib_for_plotting():
    """Setup matplotlib and seaborn for plotting with proper configuration."""
    warnings.filterwarnings('default')
    plt.switch_backend("Agg")
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")
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
        ('Structured Validation Data', 0.8, colors['postgresql']),
        ('Unstructured Threat Intelligence', 0.7, colors['mongodb']),
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
        ax.text(0.275, y_pos, name, fontsize=11, fontweight='bold', 
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
        arrow = FancyBboxPatch((0.26, y_pos-0.01), 0.03, 0.02, 
                              boxstyle="rarrow,pad=0", 
                              facecolor='black', 
                              alpha=0.7)
        ax.add_patch(arrow)
    
    # Cross-database connections
    # PostgreSQL to Neo4j
    ax.plot([0.275, 0.275], [0.77, 0.53], 'r-', linewidth=2, alpha=0.7)
    ax.annotate('', xy=(0.275, 0.53), xytext=(0.275, 0.77),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2, alpha=0.7))
    
    # MongoDB to Neo4j
    ax.plot([0.275, 0.275], [0.67, 0.53], 'r-', linewidth=2, alpha=0.7)
    ax.annotate('', xy=(0.275, 0.53), xytext=(0.275, 0.67),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2, alpha=0.7))
    
    # Redis to all databases
    for _, y_pos, _ in use_cases:
        if y_pos != 0.4:  # Skip self
            ax.plot([0.725, 0.275], [0.43, y_pos], color=colors['redis'], linewidth=1.5, alpha=0.6)
    
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
    print("✓ Overall architecture diagram created")

def create_data_flow_diagram():
    """Create simplified data flow architecture diagram."""
    setup_matplotlib_for_plotting()
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Title
    ax.text(0.5, 0.95, 'Cybersecurity Database Data Flow Architecture', 
            fontsize=20, fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    
    # Data Ingestion Layer
    ingestion_items = [
        ('Network Logs', 0.8, '#3498db'),
        ('Host Logs', 0.7, '#3498db'),
        ('Application Logs', 0.6, '#3498db'),
        ('Threat Feeds', 0.5, '#3498db'),
        ('Config Data', 0.4, '#3498db')
    ]
    
    for name, y, color in ingestion_items:
        box = FancyBboxPatch((0.05, y-0.03), 0.2, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(0.15, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Processing Layer
    processing_items = [
        ('ETL Pipeline', 0.75, '#e67e22'),
        ('Data Validation', 0.65, '#e67e22'),
        ('Enrichment', 0.55, '#e67e22'),
        ('Real-time Processing', 0.45, '#e67e22')
    ]
    
    for name, y, color in processing_items:
        box = FancyBboxPatch((0.3, y-0.03), 0.2, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(0.4, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Database Layer
    db_items = [
        ('PostgreSQL\n(Structured)', 0.8, '#2c3e50'),
        ('MongoDB\n(Unstructured)', 0.7, '#e74c3c'),
        ('Neo4j\n(Relationships)', 0.6, '#27ae60'),
        ('TimescaleDB\n(Time-Series)', 0.5, '#8e44ad'),
        ('Redis\n(Cache)', 0.4, '#f39c12')
    ]
    
    for name, y, color in db_items:
        box = FancyBboxPatch((0.55, y-0.03), 0.2, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(0.65, y, name, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Analytics Layer
    analytics_items = [
        ('SIEM Analytics', 0.75, '#9b59b6'),
        ('Threat Detection', 0.65, '#9b59b6'),
        ('Attack Path Analysis', 0.55, '#9b59b6'),
        ('Real-time Monitoring', 0.45, '#9b59b6'),
        ('Compliance Reports', 0.35, '#9b59b6')
    ]
    
    for name, y, color in analytics_items:
        box = FancyBboxPatch((0.8, y-0.03), 0.18, 0.06, 
                            boxstyle="round,pad=0.01", 
                            facecolor=color, 
                            edgecolor='black', 
                            alpha=0.8)
        ax.add_patch(box)
        ax.text(0.89, y, name, fontsize=9, fontweight='bold', 
                ha='center', va='center', color='white')
    
    # Data Flow Arrows
    # Ingestion to Processing
    ingestion_positions = [0.8, 0.7, 0.6, 0.5, 0.4]
    for y in ingestion_positions:
        ax.annotate('', xy=(0.3, 0.65), xytext=(0.25, y),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2, alpha=0.7))
    
    # Processing to Databases
    for y in [0.75, 0.65, 0.55, 0.45]:
        ax.annotate('', xy=(0.55, y+0.1), xytext=(0.5, y),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=2, alpha=0.7))
    
    # Analytics connections
    analytics_connections = [
        (0.75, 0.8), (0.65, 0.7), (0.55, 0.6), (0.45, 0.5), (0.35, 0.4)
    ]
    
    for analytics_y, db_y in analytics_connections:
        ax.annotate('', xy=(0.89, analytics_y), xytext=(0.75, db_y),
                    arrowprops=dict(arrowstyle='->', color='purple', lw=1.5, alpha=0.7))
    
    # Labels
    ax.text(0.15, 0.9, 'Data Sources', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.4, 0.9, 'Processing', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.65, 0.9, 'Storage', fontsize=14, fontweight='bold', ha='center')
    ax.text(0.89, 0.9, 'Analytics', fontsize=14, fontweight='bold', ha='center')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/data_flow_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Data flow architecture diagram created")

def create_use_case_comparison():
    """Create technology comparison visualization for all use cases."""
    setup_matplotlib_for_plotting()
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Use case names and their recommended solutions
    use_cases = [
        ('Structured Validation Data', 'PostgreSQL'),
        ('Unstructured Threat Intel', 'MongoDB'),
        ('Time-Series Data', 'TimescaleDB'),
        ('Graph Relationships', 'Neo4j'),
        ('Caching Layer', 'Redis'),
        ('Summary', 'All Technologies')
    ]
    
    # Evaluation criteria
    criteria = ['ACID\nCompliance', 'Schema\nFlexibility', 'Query\nPerformance', 
               'Ingestion\nSpeed', 'Volume\nScale', 'Complexity\nCost']
    
    for i, (use_case, recommendation) in enumerate(use_cases):
        ax = axes[i]
        
        if use_case == 'Summary':
            # Create a summary comparison
            technologies = ['PostgreSQL', 'MongoDB', 'Neo4j', 'Redis', 'TimescaleDB']
            scores = [90, 85, 88, 95, 82]
            colors = ['#2c3e50', '#e74c3c', '#27ae60', '#f39c12', '#8e44ad']
            
            bars = ax.bar(technologies, scores, color=colors, alpha=0.8)
            ax.set_title('Technology Performance Summary\n(Overall Recommendation Score)', 
                        fontsize=12, fontweight='bold')
            ax.set_ylabel('Score (0-100)')
            ax.set_ylim(0, 100)
            
            # Add value labels on bars
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{score}', ha='center', va='bottom', fontweight='bold')
        
        else:
            # Create radar chart for individual use case
            categories = ['PostgreSQL', 'MongoDB', 'Neo4j']
            
            # Scores for this specific use case
            if use_case == 'Structured Validation Data':
                scores = [95, 60, 70]
            elif use_case == 'Unstructured Threat Intel':
                scores = [60, 95, 75]
            elif use_case == 'Time-Series Data':
                scores = [80, 70, 65]
            elif use_case == 'Graph Relationships':
                scores = [40, 50, 95]
            elif use_case == 'Caching Layer':
                scores = [50, 55, 60]
            
            # Create radar chart
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
            scores_closed = scores + [scores[0]]  # Close the plot
            angles_closed = np.concatenate((angles, [angles[0]]))
            
            ax.plot(angles_closed, scores_closed, 'o-', linewidth=2, color='#2c3e50')
            ax.fill(angles_closed, scores_closed, alpha=0.25, color='#2c3e50')
            ax.set_xticks(angles)
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)
            ax.set_title(f'{use_case}\nRecommended: {recommendation}', 
                        fontsize=12, fontweight='bold')
            ax.grid(True)
            
            # Add score labels
            for angle, score, category in zip(angles, scores, categories):
                ax.text(angle, score + 5, f'{score}', ha='center', va='center', 
                       fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/use_case_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Use case comparison diagram created")

def create_technology_radar():
    """Create simplified technology radar."""
    setup_matplotlib_for_plotting()
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Database technologies with their positions
    technologies = {
        'PostgreSQL': (85, 90, '#2c3e50'),
        'MongoDB': (75, 85, '#e74c3c'),
        'Neo4j': (70, 88, '#27ae60'),
        'Redis': (90, 95, '#f39c12'),
        'TimescaleDB': (65, 82, '#8e44ad'),
        'InfluxDB': (60, 78, '#16a085'),
        'Cassandra': (68, 75, '#e67e22')
    }
    
    # Plot each technology
    for tech, (maturity, performance, color) in technologies.items():
        # Main circle
        circle = Circle((maturity, performance), 4, color=color, alpha=0.7)
        ax.add_patch(circle)
        
        # Technology label
        ax.text(maturity, performance, tech, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
    
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
    
    plt.tight_layout()
    plt.savefig('/workspace/docs/database_analysis/technology_radar.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Technology radar diagram created")

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
    
    print("\nAll diagrams created successfully!")
    print("Files saved in /workspace/docs/database_analysis/:")
    print("- architecture_overview.png")
    print("- data_flow_architecture.png") 
    print("- use_case_comparison.png")
    print("- technology_radar.png")
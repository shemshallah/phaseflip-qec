# 📄 FILE 21: phaseflip_qec/utils/visualization.py

**Filename:** `phaseflip_qec/utils/visualization.py`  
**Purpose:** Visualization utilities for results and benchmarks  
**Location:** `phaseflip_qec/utils/` directory

"""
Visualization Utilities for PhaseFlip QEC

Provides plotting and visualization functions for error correction results.

Created by OaGI Research
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Tuple
from matplotlib.figure import Figure
from matplotlib.axes import Axes


def plot_error_suppression(
    physical_error_rates: List[float],
    code_distances: List[int] = [3, 5, 7],
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot error suppression vs physical error rate for different code distances.
    
    Args:
        physical_error_rates: List of physical error rates to plot
        code_distances: List of code distances to compare
        figsize: Figure size (width, height)
        save_path: Path to save figure (optional)
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Import encoders
    from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
    
    encoders = {
        3: Distance3Encoder(),
        5: Distance5Encoder(),
        7: Distance7Encoder(),
    }
    
    colors = {3: 'blue', 5: 'green', 7: 'red'}
    markers = {3: 'o', 5: 's', 7: '^'}
    
    # Plot for each code distance
    for distance in code_distances:
        encoder = encoders[distance]
        logical_errors = [
            encoder.estimate_logical_error_rate(p) 
            for p in physical_error_rates
        ]
        
        ax.loglog(
            physical_error_rates,
            logical_errors,
            marker=markers[distance],
            color=colors[distance],
            linewidth=2,
            markersize=8,
            label=f'Distance-{distance} PhaseFlip'
        )
    
    # Plot baseline (no error correction)
    ax.loglog(
        physical_error_rates,
        physical_error_rates,
        '--',
        color='gray',
        linewidth=2,
        label='No error correction'
    )
    
    # Plot surface code comparison (quadratic scaling)
    surface_code_errors = [p**2 * 10 for p in physical_error_rates]
    ax.loglog(
        physical_error_rates,
        surface_code_errors,
        ':',
        color='orange',
        linewidth=2,
        label='Surface code (d=7, approx)'
    )
    
    ax.set_xlabel('Physical Error Rate', fontsize=12, fontweight='bold')
    ax.set_ylabel('Logical Error Rate', fontsize=12, fontweight='bold')
    ax.set_title('PhaseFlip QEC Error Suppression', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_syndrome_distribution(
    syndrome_counts: Dict[str, int],
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot distribution of measured syndromes.
    
    Args:
        syndrome_counts: Dictionary mapping syndrome strings to counts
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    syndromes = list(syndrome_counts.keys())
    counts = list(syndrome_counts.values())
    
    # Sort by count
    sorted_indices = np.argsort(counts)[::-1]
    syndromes = [syndromes[i] for i in sorted_indices]
    counts = [counts[i] for i in sorted_indices]
    
    # Color code based on syndrome weight
    colors = []
    for syndrome in syndromes:
        weight = syndrome.count('1')
        if weight == 0:
            colors.append('green')
        elif weight == 1:
            colors.append('yellow')
        elif weight == 2:
            colors.append('orange')
        else:
            colors.append('red')
    
    bars = ax.bar(range(len(syndromes)), counts, color=colors, alpha=0.7, edgecolor='black')
    ax.set_xticks(range(len(syndromes)))
    ax.set_xticklabels(syndromes, rotation=45, ha='right')
    ax.set_xlabel('Syndrome', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Syndrome Measurement Distribution', fontsize=14, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', alpha=0.7, label='No error (weight 0)'),
        Patch(facecolor='yellow', alpha=0.7, label='Single error (weight 1)'),
        Patch(facecolor='orange', alpha=0.7, label='Double error (weight 2)'),
        Patch(facecolor='red', alpha=0.7, label='Triple+ error (weight 3+)'),
    ]
    ax.legend(handles=legend_elements, fontsize=9)
    
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_fidelity_comparison(
    circuit_depths: List[int],
    fidelities_no_code: List[float],
    fidelities_with_code: List[float],
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot fidelity comparison with and without error correction.
    
    Args:
        circuit_depths: List of circuit depths
        fidelities_no_code: Fidelities without error correction
        fidelities_with_code: Fidelities with PhaseFlip QEC
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(
        circuit_depths,
        fidelities_no_code,
        'o-',
        color='red',
        linewidth=2,
        markersize=8,
        label='No error correction'
    )
    
    ax.plot(
        circuit_depths,
        fidelities_with_code,
        's-',
        color='green',
        linewidth=2,
        markersize=8,
        label='PhaseFlip QEC'
    )
    
    ax.set_xlabel('Circuit Depth (Number of Gates)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fidelity', fontsize=12, fontweight='bold')
    ax.set_title('Circuit Fidelity Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1.05])
    
    # Add shaded regions
    ax.axhspan(0.9, 1.0, alpha=0.1, color='green', label='High fidelity (>90%)')
    ax.axhspan(0.5, 0.9, alpha=0.1, color='yellow')
    ax.axhspan(0, 0.5, alpha=0.1, color='red')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def create_bloch_sphere_comparison(
    state_no_code,
    state_with_code,
    figsize: Tuple[int, int] = (12, 5),
    save_path: Optional[str] = None
) -> Figure:
    """
    Create side-by-side Bloch sphere comparison.
    
    Args:
        state_no_code: Statevector without error correction
        state_with_code: Statevector with PhaseFlip QEC
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        Matplotlib Figure object
    """
    try:
        from qiskit.visualization import plot_bloch_multivector
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Plot without error correction
        plot_bloch_multivector(state_no_code, ax=ax1)
        ax1.set_title('Without Error Correction', fontsize=12, fontweight='bold')
        
        # Plot with error correction
        plot_bloch_multivector(state_with_code, ax=ax2)
        ax2.set_title('With PhaseFlip QEC', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
        
    except ImportError:
        print("Qiskit visualization not available. Install with: pip install qiskit[visualization]")
        return None


def plot_algorithm_success_rates(
    algorithms: List[str],
    success_rates_no_code: List[float],
    success_rates_with_code: List[float],
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot algorithm success rate comparison.
    
    Args:
        algorithms: List of algorithm names
        success_rates_no_code: Success rates without error correction
        success_rates_with_code: Success rates with PhaseFlip QEC
        figsize: Figure size
        save_path: Path to save figure
        
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x = np.arange(len(algorithms))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, success_rates_no_code, width, 
                   label='No error correction', color='red', alpha=0.7)
    bars2 = ax.bar(x + width/2, success_rates_with_code, width,
                   label='PhaseFlip QEC', color='green', alpha=0.7)
    
    ax.set_xlabel('Algorithm', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Algorithm Success Rate Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 105])
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def create_comparison_dashboard(
    physical_error_rate: float = 0.001,
    save_path: Optional[str] = None
) -> Figure:
    """
    Create comprehensive comparison dashboard.
    
    Args:
        physical_error_rate: Physical error rate for calculations
        save_path: Path to save figure
        
    Returns:
        Matplotlib Figure object
    """
    from ..encoders import Distance3Encoder, Distance5Encoder, Distance7Encoder
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Plot 1: Error suppression scaling
    ax1 = fig.add_subplot(gs[0, :])
    physical_rates = np.logspace(-4, -2, 20)
    
    encoders = {
        3: Distance3Encoder(),
        5: Distance5Encoder(),
        7: Distance7Encoder(),
    }
    
    for distance, encoder in encoders.items():
        logical_errors = [encoder.estimate_logical_error_rate(p) for p in physical_rates]
        ax1.loglog(physical_rates, logical_errors, marker='o', linewidth=2, 
                   label=f'Distance-{distance}')
    
    ax1.loglog(physical_rates, physical_rates, '--', color='gray', label='No code')
    ax1.set_xlabel('Physical Error Rate', fontweight='bold')
    ax1.set_ylabel('Logical Error Rate', fontweight='bold')
    ax1.set_title('Error Suppression Scaling', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Suppression factors
    ax2 = fig.add_subplot(gs[1, 0])
    distances = [3, 5, 7]
    suppressions = [
        physical_error_rate / encoders[d].estimate_logical_error_rate(physical_error_rate)
        for d in distances
    ]
    ax2.bar(distances, suppressions, color=['blue', 'green', 'red'], alpha=0.7)
    ax2.set_xlabel('Code Distance', fontweight='bold')
    ax2.set_ylabel('Suppression Factor', fontweight='bold')
    ax2.set_title('Error Suppression by Distance', fontweight='bold')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Algorithm success rates
    ax3 = fig.add_subplot(gs[1, 1])
    algorithms = ['VQE', 'QAOA', 'Grover', "Shor's"]
    gate_counts = [50, 100, 200, 500]
    
    success_no_code = [(1 - physical_error_rate)**n * 100 for n in gate_counts]
    logical_error = encoders[7].estimate_logical_error_rate(physical_error_rate)
    success_with_code = [(1 - logical_error)**n * 100 for n in gate_counts]
    
    x = np.arange(len(algorithms))
    width = 0.35
    ax3.bar(x - width/2, success_no_code, width, label='No code', color='red', alpha=0.7)
    ax3.bar(x + width/2, success_with_code, width, label='PhaseFlip d=7', color='green', alpha=0.7)
    ax3.set_xlabel('Algorithm', fontweight='bold')
    ax3.set_ylabel('Success Rate (%)', fontweight='bold')
    ax3.set_title('Algorithm Success Rates', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(algorithms)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Resource requirements
    ax4 = fig.add_subplot(gs[1, 2])
    qubits = [encoders[d].num_physical_qubits for d in distances]
    ax4.bar(distances, qubits, color=['blue', 'green', 'red'], alpha=0.7)
    ax4.set_xlabel('Code Distance', fontweight='bold')
    ax4.set_ylabel('Physical Qubits Required', fontweight='bold')
    ax4.set_title('Resource Requirements', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Comparison table
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('tight')
    ax5.axis('off')
    
    table_data = []
    table_data.append(['Code Distance', 'Physical Qubits', 'Logical Error Rate', 
                      'Suppression Factor', 'Max Correctable'])
    
    for distance, encoder in encoders.items():
        logical_err = encoder.estimate_logical_error_rate(physical_error_rate)
        suppression = physical_error_rate / logical_err
        max_correct = (distance - 1) // 2
        
        table_data.append([
            f'{distance}',
            f'{encoder.num_physical_qubits}',
            f'{logical_err:.2e}',
            f'{suppression:,.0f}×',
            f'{max_correct}'
        ])
    
    table = ax5.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.15, 0.15, 0.2, 0.2, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header row
    for i in range(5):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    fig.suptitle(f'PhaseFlip QEC Comprehensive Dashboard (p = {physical_error_rate})',
                fontsize=16, fontweight='bold')
    
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig
#!/usr/bin/env python3
"""
Visualize Signed Boolean Networks from CSV files as interactive HTML.
Creates a scrollable visualization showing multiple network solutions.
"""

import csv
import glob
import json
from pathlib import Path
import colorsys


def weight_to_color(weight):
    """Convert weight to RGB color using gradient: red(-) → black(0) → green(+)"""
    if weight == 0:
        return (0, 0, 0)  # Black
    
    # Normalize weight to [-1, 1] range for color mapping
    # Weights typically range from -3 to +3, so clamp to that
    normalized = max(-1, min(1, weight / 3.0))
    
    if normalized < 0:
        # Red gradient: (1, 0, 0) to (0, 0, 0)
        r = int(255 * (1 + normalized))
        g = 0
        b = 0
    else:
        # Green gradient: (0, 0, 0) to (0, 1, 0)
        r = 0
        g = int(255 * normalized)
        b = 0
    
    return (r, g, b)


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color string"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def parse_csv_files(base_directory="."):
    """Parse all CSV files from multiple directories and return network data"""
    search_dirs = [
        base_directory,
        str(Path(base_directory) / "Programmes_Laurent")
    ]
    
    networks = []
    all_csv_files = []
    
    for search_dir in search_dirs:
        all_csv_files.extend(glob.glob(f"{search_dir}/*_output.csv"))
    
    # Sort by dimension then by name
    all_csv_files.sort()
    
    for csv_file in all_csv_files:
        filename = Path(csv_file).stem
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                networks.append({
                    'name': filename,
                    'filepath': csv_file,
                    'rows': rows
                })
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
    
    return networks


def extract_network_data(row, num_vars):
    """Extract node and edge data from a CSV row"""
    # Extract f_i values
    f_values = {}
    for i in range(1, num_vars + 1):
        f_values[i] = int(row[f'f_{i}'])
    
    # Extract weight matrix
    weights = {}
    for i in range(1, num_vars + 1):
        for j in range(1, num_vars + 1):
            weight = int(row[f'w_{i},{j}'])
            if weight != 0:
                weights[(i, j)] = weight
    
    return f_values, weights


def create_html_visualization(networks):
    """Create interactive HTML visualization with all networks"""
    
    if not networks:
        print("No networks found!")
        return
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Signed Boolean Network Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .controls label {
            font-weight: bold;
        }
        .controls select {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
        }
        #canvas {
            border: 1px solid #ddd;
            background-color: #fafafa;
            display: block;
            margin: 20px 0;
        }
        .info-panel {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
        }
        .info-panel h3 {
            margin-top: 0;
            color: #333;
        }
        .functions {
            font-family: monospace;
            background-color: white;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        .function-item {
            margin: 5px 0;
            font-size: 13px;
        }
        .legend {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            font-size: 13px;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 1px solid #999;
            margin-right: 5px;
            vertical-align: middle;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Signed Boolean Network Visualization</h1>
        
        <div class="controls">
            <label for="networkSelect">Network:</label>
            <select id="networkSelect" onchange="updateVisualization()">
            </select>
            
            <label for="rowSelect" style="margin-left: 20px;">Solution:</label>
            <select id="rowSelect" onchange="updateVisualization()">
            </select>
            
            <span id="rowCount" style="margin-left: auto; color: #666;"></span>
        </div>
        
        <svg id="canvas" width="900" height="700"></svg>
        
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color" style="background-color: #00ff00;"></span>
                Positive weights
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #000000;"></span>
                Zero weight
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #ff0000;"></span>
                Negative weights
            </div>
        </div>
        
        <div class="info-panel">
            <h3>Transition Functions (f_i)</h3>
            <div class="functions" id="functionsDisplay"></div>
        </div>
    </div>
    
    <script>
        // Network data embedded in HTML
        const networkData = """ + json.dumps(networks) + """;
        let currentRowIdx = 0;
        
        function getNumVars(row) {
            // Count f_i fields to determine dimension
            return Object.keys(row).filter(k => k.startsWith('f_')).length;
        }
        
        function updateVisualization() {
            const networkSelect = document.getElementById('networkSelect');
            const rowSelect = document.getElementById('rowSelect');
            const networkIdx = networkSelect.selectedIndex;
            const rowIdx = rowSelect.selectedIndex;
            
            currentRowIdx = rowIdx;
            
            const network = networkData[networkIdx];
            const row = network.rows[rowIdx];
            const numVars = getNumVars(row);
            
            // Calculate weight range across all networks
            let minWeight = 0, maxWeight = 0;
            for (const net of networkData) {
                for (const dataRow of net.rows) {
                    const numV = getNumVars(dataRow);
                    for (let i = 1; i <= numV; i++) {
                        for (let j = 1; j <= numV; j++) {
                            const weight = parseInt(dataRow[`w_${i},${j}`]) || 0;
                            minWeight = Math.min(minWeight, weight);
                            maxWeight = Math.max(maxWeight, weight);
                        }
                    }
                }
            }
            window.maxAbsWeight = Math.max(Math.abs(minWeight), Math.abs(maxWeight)) || 3;
            
            // Update functions display
            const functionsDisplay = document.getElementById('functionsDisplay');
            let functionsHtml = '';
            for (let i = 1; i <= numVars; i++) {
                const fValue = row['f_' + i];
                functionsHtml += `<div class="function-item">f<sub>${i}</sub> = ${fValue}</div>`;
            }
            functionsDisplay.innerHTML = functionsHtml;
            
            // Update canvas
            drawNetwork(row, numVars);
            
            document.getElementById('rowCount').textContent = 
                `Solution ${rowIdx + 1} of ${network.rows.length}`;
        }
        
        function drawNetwork(row, numVars) {
            const svg = document.getElementById('canvas');
            svg.innerHTML = '';
            
            const width = 900;
            const height = 700;
            const radius = 40;
            const centerX = width / 2;
            const centerY = height / 2;
            
            // Calculate node positions in a circle
            const nodes = [];
            for (let i = 1; i <= numVars; i++) {
                const angle = (i - 1) * (2 * Math.PI / numVars) - Math.PI / 2;
                const x = centerX + (height / 2 - 100) * Math.cos(angle);
                const y = centerY + (height / 2 - 100) * Math.sin(angle);
                nodes.push({ id: i, x, y });
            }
            
            // Draw edges with proper curve offsets to avoid overlaps
            const edges = [];
            for (let i = 1; i <= numVars; i++) {
                for (let j = 1; j <= numVars; j++) {
                    const weight = parseInt(row[`w_${i},${j}`]);
                    if (weight !== 0) {
                        edges.push({
                            source: nodes[i - 1],
                            target: nodes[j - 1],
                            weight: weight,
                            isLoop: i === j
                        });
                    }
                }
            }
            
            // Group edges by (i,j) and (j,i) pairs to detect bidirectional edges
            const edgeMap = new Map();
            for (const edge of edges) {
                const key1 = `${edge.source.id}-${edge.target.id}`;
                const key2 = `${edge.target.id}-${edge.source.id}`;
                
                if (!edgeMap.has(key1)) edgeMap.set(key1, []);
                edgeMap.get(key1).push(edge);
            }
            
            // Define arrowhead markers for each color
            const defs = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'defs'));
            const colors = new Map(); // color -> sanitized ID
            let colorIdx = 0;
            
            // Collect all colors used and create sanitized IDs
            for (const edge of edges) {
                const color = weightToColor(edge.weight);
                if (!colors.has(color)) {
                    colors.set(color, `color${colorIdx++}`);
                }
            }
            
            // Create marker for each color
            for (const [color, colorId] of colors) {
                const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
                marker.setAttribute('id', `arrowhead-${colorId}`);
                marker.setAttribute('markerWidth', '10');
                marker.setAttribute('markerHeight', '10');
                marker.setAttribute('refX', '9');
                marker.setAttribute('refY', '3');
                marker.setAttribute('orient', 'auto');
                
                const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                polygon.setAttribute('points', '0 0, 10 3, 0 6');
                polygon.setAttribute('fill', color);
                
                marker.appendChild(polygon);
                defs.appendChild(marker);
            }
            
            // Draw self-loops FIRST (so they appear behind nodes)
            for (const edge of edges) {
                if (edge.source.id === edge.target.id) {
                    const { source, weight } = edge;
                    const color = weightToColor(weight);
                    const colorId = colors.get(color);
                    const markerId = `arrowhead-${colorId}`;
                    
                    // Create a proper loop that starts and ends at slightly different points
                    const angle = (source.id - 1) * (2 * Math.PI / numVars) - Math.PI / 2;
                    const nodeRadius = 40;
                    const loopDistance = 100;
                    
                    // Start point on node perimeter
                    const startX = source.x + nodeRadius * Math.cos(angle);
                    const startY = source.y + nodeRadius * Math.sin(angle);
                    
                    // End point slightly offset (for arrowhead visibility)
                    const endAngle = angle + 0.15; // About 8.6 degrees
                    const endX = source.x + nodeRadius * Math.cos(endAngle);
                    const endY = source.y + nodeRadius * Math.sin(endAngle);
                    
                    // Control point far from node
                    const controlX = source.x + loopDistance * Math.cos(angle);
                    const controlY = source.y + loopDistance * Math.sin(angle);
                    
                    // Draw rounded loop using cubic bezier for smoother curve
                    const path = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path'));
                    path.setAttribute('d', `M ${startX} ${startY} C ${controlX} ${controlY} ${controlX} ${controlY} ${endX} ${endY}`);
                    path.setAttribute('fill', 'none');
                    path.setAttribute('stroke', color);
                    path.setAttribute('stroke-width', '3');
                    path.setAttribute('stroke-linecap', 'round');
                    path.setAttribute('marker-end', `url(#${markerId})`);
                    
                    // Add weight label for self-loop, positioned clearly
                    const labelDistance = 85;
                    const labelX = source.x + labelDistance * Math.cos(angle);
                    const labelY = source.y + labelDistance * Math.sin(angle);
                    
                    // Background for label
                    const bg = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'rect'));
                    bg.setAttribute('x', labelX - 16);
                    bg.setAttribute('y', labelY - 12);
                    bg.setAttribute('width', '32');
                    bg.setAttribute('height', '20');
                    bg.setAttribute('fill', 'white');
                    bg.setAttribute('stroke', 'none');
                    bg.setAttribute('rx', '4');
                    bg.setAttribute('opacity', '0.9');
                    
                    const text = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'text'));
                    text.setAttribute('x', labelX);
                    text.setAttribute('y', labelY);
                    text.setAttribute('text-anchor', 'middle');
                    text.setAttribute('dy', '0.3em');
                    text.setAttribute('font-size', '12');
                    text.setAttribute('font-weight', 'bold');
                    text.setAttribute('fill', color);
                    text.textContent = weight;
                }
            }
            
            // Draw regular edges
            for (const edge of edges) {
                if (edge.source.id === edge.target.id) continue; // Skip self-loops
                
                const { source, target, weight } = edge;
                const color = weightToColor(weight);
                const colorId = colors.get(color);
                const markerId = `arrowhead-${colorId}`;
                
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const ratio = 40 / distance;
                
                let x1 = source.x + dx * ratio;
                let y1 = source.y + dy * ratio;
                let x2 = target.x - dx * ratio;
                let y2 = target.y - dy * ratio;
                
                // Check if there's a reverse edge
                const key1 = `${source.id}-${target.id}`;
                const key2 = `${target.id}-${source.id}`;
                const hasReverseEdge = edgeMap.has(key2);
                
                // Calculate curve offset
                let curveOffset = 0;
                if (hasReverseEdge) {
                    // Offset edges in opposite directions for bidirectional
                    const reverseEdges = edgeMap.get(key2) || [];
                    const edgeIndex = edgeMap.get(key1).indexOf(edge);
                    curveOffset = (edgeIndex === 0) ? 25 : -25;
                }
                
                // Calculate midpoint and perpendicular
                const midX = (x1 + x2) / 2;
                const midY = (y1 + y2) / 2;
                const perpAngle = Math.atan2(dy, dx) + Math.PI / 2;
                
                // Control point for curve
                const controlX = midX + curveOffset * Math.cos(perpAngle);
                const controlY = midY + curveOffset * Math.sin(perpAngle);
                
                // Draw curved edge
                const path = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path'));
                path.setAttribute('d', `M ${x1} ${y1} Q ${controlX} ${controlY} ${x2} ${y2}`);
                path.setAttribute('fill', 'none');
                path.setAttribute('stroke', color);
                path.setAttribute('stroke-width', '2');
                path.setAttribute('marker-end', `url(#${markerId})`);
                
                // Add weight label with better offset to avoid overlap
                const offsetDistance = 25;
                const labelX = controlX + offsetDistance * Math.cos(perpAngle);
                const labelY = controlY + offsetDistance * Math.sin(perpAngle);
                
                // Background for label readability
                const bg = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'rect'));
                bg.setAttribute('x', labelX - 14);
                bg.setAttribute('y', labelY - 11);
                bg.setAttribute('width', '28');
                bg.setAttribute('height', '18');
                bg.setAttribute('fill', 'white');
                bg.setAttribute('stroke', 'none');
                bg.setAttribute('rx', '3');
                bg.setAttribute('opacity', '0.85');
                
                const text = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'text'));
                text.setAttribute('x', labelX);
                text.setAttribute('y', labelY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('dy', '0.3em');
                text.setAttribute('font-size', '11');
                text.setAttribute('font-weight', 'bold');
                text.setAttribute('fill', color);
                text.textContent = weight;
            }
            
            // Draw nodes with f_i labels
            for (const node of nodes) {
                const circle = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'circle'));
                circle.setAttribute('cx', node.x);
                circle.setAttribute('cy', node.y);
                circle.setAttribute('r', radius);
                circle.setAttribute('fill', 'white');
                circle.setAttribute('stroke', '#333');
                circle.setAttribute('stroke-width', '2');
                
                // Node ID
                const idText = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'text'));
                idText.setAttribute('x', node.x);
                idText.setAttribute('y', node.y - 8);
                idText.setAttribute('text-anchor', 'middle');
                idText.setAttribute('font-size', '18');
                idText.setAttribute('font-weight', 'bold');
                idText.textContent = node.id;
                
                // Subtle f_i value
                const fValue = row['f_' + node.id];
                const fText = svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'text'));
                fText.setAttribute('x', node.x);
                fText.setAttribute('y', node.y + 12);
                fText.setAttribute('text-anchor', 'middle');
                fText.setAttribute('font-size', '10');
                fText.setAttribute('fill', '#999');
                fText.textContent = 'f=' + fValue;
            }
        }
        
        function weightToColor(weight) {
            if (weight === 0) return '#000000';
            
            // Use adaptive max weight from the entire dataset
            const maxAbsWeight = window.maxAbsWeight || 3;
            const absWeight = Math.abs(weight);
            const normalized = Math.min(1, absWeight / maxAbsWeight);
            
            if (weight < 0) {
                // Red gradient: bright red (low |weight|) -> dark red (high |weight|)
                const brightness = Math.round(255 * (1 - normalized * 0.7)); // 255 -> 76
                return `rgb(${brightness}, 0, 0)`;
            } else {
                // Green gradient: bright green (low weight) -> dark green (high weight)
                const brightness = Math.round(255 * (1 - normalized * 0.7)); // 255 -> 76
                return `rgb(0, ${brightness}, 0)`;
            }
        }
        
        window.addEventListener('load', function() {
            const networkSelect = document.getElementById('networkSelect');
            const rowSelect = document.getElementById('rowSelect');
            
            // Populate network dropdown
            for (let i = 0; i < networkData.length; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = networkData[i].name;
                networkSelect.appendChild(option);
            }
            
            // Populate row dropdown for first network
            updateRowDropdown();
            
            // Initial visualization
            updateVisualization();
            
            // Update row dropdown when network changes
            networkSelect.addEventListener('change', updateRowDropdown);
            
            // Add mouse wheel scrolling for solutions
            document.getElementById('canvas').addEventListener('wheel', (e) => {
                e.preventDefault();
                const rowSelect = document.getElementById('rowSelect');
                let newIdx = currentRowIdx + (e.deltaY > 0 ? 1 : -1);
                newIdx = Math.max(0, Math.min(newIdx, rowSelect.options.length - 1));
                rowSelect.selectedIndex = newIdx;
                updateVisualization();
            }, { passive: false });
        });
        
        function updateRowDropdown() {
            const networkSelect = document.getElementById('networkSelect');
            const rowSelect = document.getElementById('rowSelect');
            const networkIdx = networkSelect.selectedIndex;
            
            rowSelect.innerHTML = '';
            const network = networkData[networkIdx];
            
            for (let i = 0; i < network.rows.length; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `Solution ${i + 1}`;
                rowSelect.appendChild(option);
            }
            
            currentRowIdx = 0;
            updateVisualization();
        }
    </script>
</body>
</html>
"""
    
    return html


def main():
    import os
    
    # Parse CSV files from specified directory
    csv_dir = Path(__file__).parent
    networks = parse_csv_files(csv_dir)
    
    if not networks:
        print("No CSV files found!")
        return
    
    print(f"Found {len(networks)} network files")
    
    # Create HTML
    html = create_html_visualization(networks)
    
    # Write to file
    output_file = csv_dir / "sbn_visualization.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Visualization saved to: {output_file}")
    print(f"Open it in a web browser to view the networks")


if __name__ == '__main__':
    main()

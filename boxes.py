# Import matplotlib for creating 3D visualizations
import matplotlib.pyplot as plt
# Import 3D polygon collection for rendering 3D boxes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
# Import numpy for numerical array operations
import numpy as np
# Import random for generating random RGB colors for box visualization
import random
# Import os for file system operations (creating directories, file paths)
import os
# Import Counter for counting occurrences of box types in the summary
from collections import Counter

# ============================================================================
# BOX CLASS: Represents a single box with dimensions, position, and properties
# ============================================================================
class Box:
    def __init__(self, w, d, h, base_name="Box", instance_id=1):
        # Store width, depth, and height dimensions of the box
        self.w, self.d, self.h = w, d, h
        # Store the base name/type of the box (e.g., "Engine", "Kit")
        self.base_name = base_name
        # Create a unique name combining type and instance ID (e.g., "Engine_1")
        self.name = f"{base_name}_{instance_id}"
        # Initialize position at origin; will be updated when box is packed
        self.position = (0, 0, 0)
        # Generate random RGB color (0-1 values) for visual distinction in 3D plot
        self.color = [random.random() for _ in range(3)]
        # Track whether box has been rotated 90 degrees to fit in space
        self.rotated = False 

# ============================================================================
# PALLET CLASS: Represents a pallet that holds multiple boxes
# ============================================================================
class Pallet:
    def __init__(self, w, d, h, id, stability_threshold=0.8):
        # Store pallet dimensions (width, depth, height)
        self.w, self.d, self.h = w, d, h
        # Store unique pallet identifier
        self.id = id
        # Initialize empty list to track all boxes placed on this pallet
        self.boxes = []
        # Initialize with one large space covering entire pallet: (x, y, z, width, depth, height)
        # This represents available space for packing boxes
        self.spaces = [(0, 0, 0, w, d, h)]
        # Set stability threshold: minimum ratio of box base that must be supported (default 80%)
        self.stability_threshold = stability_threshold

    def is_stable(self, x, y, z, bw, bd):
        # Check if a box at position (x, y, z) with base dimensions (bw x bd) is stable
        # Boxes placed directly on pallet floor (z=0) are always stable
        if z == 0: return True
        # Initialize counter for the area of new box that is supported by boxes below
        supported_area = 0
        # Calculate total base area of the box being checked
        box_area = bw * bd
        # Check overlap with each existing box on the pallet
        for b in self.boxes:
            # Check if existing box's top surface aligns with the placement height (z)
            # Use small tolerance (0.01) for floating point comparison
            if abs((b.position[2] + b.h) - z) < 0.01:
                # Calculate x-axis overlap between new box and existing box
                ix = max(0, min(x + bw, b.position[0] + b.w) - max(x, b.position[0]))
                # Calculate y-axis overlap between new box and existing box
                iy = max(0, min(y + bd, b.position[1] + b.d) - max(y, b.position[1]))
                # Add the overlapping area to the total supported area
                supported_area += (ix * iy)
        # Return True if supported area meets or exceeds the stability threshold
        return (supported_area / box_area) >= self.stability_threshold

    def attempt_pack(self, box):
        # Try to pack a single box into available spaces on the pallet
        # Sort spaces by height first (z), then y, then x for optimal packing order
        self.spaces.sort(key=lambda s: (s[2], s[1], s[0]))
        # Iterate through each available space on the pallet
        for i, (sx, sy, sz, sw, sd, sh) in enumerate(self.spaces):
            # Try two orientations: original (w x d) and rotated 90° (d x w)
            orientations = [(box.w, box.d, False), (box.d, box.w, True)]
            # Test each orientation to see if box fits
            for bw, bd, is_rotated in orientations:
                # Check if box dimensions fit within space dimensions and height constraint
                if bw <= sw and bd <= sd and box.h <= sh:
                    # Check if box would be stable at this position with supporting boxes below
                    if not self.is_stable(sx, sy, sz, bw, bd):
                        # Skip this orientation and try next one if not stable
                        continue
                    # Update box width and depth to the current orientation
                    box.w, box.d = bw, bd
                    # Mark whether box was rotated to fit
                    box.rotated = is_rotated
                    # Set the 3D position where box will be placed
                    box.position = (sx, sy, sz)
                    # Add the packed box to this pallet's box list
                    self.boxes.append(box)
                    # Remove the space we just filled from available spaces
                    self.spaces.pop(i)
                    
                    # After placing box, create new spaces from remaining portions of the original space
                    # Add space to the right of the box (if remaining width exists)
                    if sw - bw > 0: self.spaces.append((sx + bw, sy, sz, sw - bw, bd, box.h))
                    # Add space behind the box (if remaining depth exists)
                    if sd - bd > 0: self.spaces.append((sx, sy + bd, sz, sw, sd - bd, box.h))
                    # Add space above the box (if remaining height exists)
                    if sh - box.h > 0: self.spaces.append((sx, sy, sz + box.h, sw, sd, sh - box.h))
                    # Return True to indicate successful packing
                    return True
        # Return False if box could not fit in any available space on this pallet
        return False

    def get_rotated_boxes(self):
        # Return a filtered list of boxes that were rotated 90 degrees to fit
        return [box for box in self.boxes if box.rotated]

    def get_summary(self):
        # Count how many boxes of each type are on this pallet
        counts = Counter(box.base_name for box in self.boxes)
        # Create formatted string like "4x Engine, 12x Kit"
        items_str = ", ".join([f"{qty}x {name}" for name, qty in counts.items()])
        # Return summary with box type counts and total unit count
        return f"{items_str} | Total: {len(self.boxes)} units"

# ============================================================================
# PACK_SYSTEM FUNCTION: Main bin packing algorithm
# ============================================================================
def pack_system(box_list, pallet_dims):
    # Initialize pallet list with first empty pallet
    pallets = [Pallet(*pallet_dims, id=1)]
    # Sort boxes by height descending, then by base area (width × depth) descending
    # This "First Fit Decreasing" approach improves packing efficiency
    box_list.sort(key=lambda b: (b.h, b.w * b.d), reverse=True)
    # Process each box in sorted order
    for box in box_list:
        # Flag to track whether current box was successfully packed
        packed = False
        # Try to pack box into each existing pallet
        for p in pallets:
            # Attempt to pack box into current pallet
            if p.attempt_pack(box):
                # Mark as packed and stop searching other pallets
                packed = True
                break
        # If box didn't fit in any existing pallet, create a new one
        if not packed:
            # Create new pallet with next sequential ID
            new_pallet = Pallet(*pallet_dims, id=len(pallets) + 1)
            # Try to pack box in the new pallet
            if new_pallet.attempt_pack(box): 
                # If successful, add new pallet to list
                pallets.append(new_pallet)
    # Return list of all pallets containing packed boxes
    return pallets

# ============================================================================
# VISUALIZE_AND_REPORT FUNCTION: Create 3D visualizations and text reports
# ============================================================================
def visualize_and_report(pallets):
    # Define directory name where pallet visualization images will be saved
    output_dir = "pallet_plans"
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # Print formatted header for the pallet rotation report
    print("\n" + "="*40 + "\nPALLET ROTATION REPORT\n" + "="*40)
    # Process and visualize each pallet
    for p in pallets:
        # Get list of boxes that were rotated on this pallet
        rotated = p.get_rotated_boxes()
        # Print pallet ID and summary of box counts
        print(f"PALLET {p.id}: {p.get_summary()}")
        # Print list of rotated box names (or "None" if no rotations)
        print(f"  > Rotated items ({len(rotated)}): {[b.name for b in rotated] if rotated else 'None'}")
        
        # Create new matplotlib figure for 3D visualization (10x8 inches)
        fig = plt.figure(figsize=(10, 8))
        # Add 3D subplot to the figure
        ax = fig.add_subplot(111, projection='3d')
        # Set viewing angle: 20° elevation, 45° azimuth for good perspective
        ax.view_init(elev=20, azim=45)
        # Set axis limits to match pallet dimensions
        ax.set_xlim(0, p.w); ax.set_ylim(0, p.d); ax.set_zlim(0, p.h)
        # Set aspect ratio to display pallet with correct proportions
        ax.set_box_aspect([p.w, p.d, p.h])

        # Draw each box on the pallet as a 3D rectangular prism
        for box in p.boxes:
            # Extract box position coordinates
            x, y, z = box.position
            # Define the 8 vertices (corners) of the box in 3D space
            v = np.array([[x,y,z], [x+box.w,y,z], [x+box.w,y+box.d,z], [x,y+box.d,z],
                          [x,y,z+box.h], [x+box.w,y,z+box.h], [x+box.w,y+box.d,z+box.h], [x,y+box.d,z+box.h]])
            # Define the 6 faces of the box using combinations of vertices
            faces = [[v[0],v[1],v[2],v[3]], [v[4],v[5],v[6],v[7]], [v[0],v[1],v[5],v[4]],
                     [v[2],v[3],v[7],v[6]], [v[0],v[3],v[7],v[4]], [v[1],v[2],v[6],v[5]]]
            
            # Set edge color to red for rotated boxes, black for non-rotated (visual distinction)
            edge_color = 'red' if box.rotated else 'black'
            # Set thicker line width for rotated boxes to make them stand out
            line_width = 1.5 if box.rotated else 0.5
            
            # Add the 3D box to the plot with its color, edges, and transparency
            ax.add_collection3d(Poly3DCollection(faces, facecolors=box.color, edgecolors=edge_color, alpha=0.6, linewidths=line_width))
            
            # Create label text: add "(R)" suffix if box was rotated
            lbl = f"{box.name}\n(R)" if box.rotated else box.name
            # Add text label at the center of the box
            ax.text(x+box.w/2, y+box.d/2, z+box.h/2, lbl, fontsize=6, ha='center', weight='bold')

        # Save the 3D visualization as a PNG image at 200 DPI
        plt.savefig(os.path.join(output_dir, f"pallet_{p.id}_plan.png"), dpi=200)
    # Display all generated plots
    plt.show()

# ============================================================================
# MAIN EXECUTION: Entry point when script is run directly
# ============================================================================
if __name__ == "__main__":
    # Define pallet dimensions: width=48, depth=40, height=60 units
    PALLET_CONFIG = (48, 40, 60)
    # Define list of items to pack with their dimensions and quantities
    orders = [
        {"w": 24, "d": 20, "h": 20, "name": "Engine", "qty": 4},
        {"w": 12, "d": 12, "h": 12, "name": "Kit", "qty": 12},
        {"w": 30, "d": 10, "h": 40, "name": "Panel", "qty": 2},
        {"w": 15, "d": 15, "h": 15, "name": "Pump", "qty": 6}
    ]

    # Create empty list to hold all individual box instances
    master_list = []
    # Iterate through each order type
    for item in orders:
        # Create the specified quantity of boxes for this item type
        for i in range(item["qty"]):
            # Instantiate a Box with dimensions, type name, and instance number
            master_list.append(Box(item["w"], item["d"], item["h"], item["name"], i+1))

    # Pack all boxes into pallets using the bin packing algorithm
    packed_pallets = pack_system(master_list, PALLET_CONFIG)
    # Generate 3D visualizations and text reports for all pallets
    visualize_and_report(packed_pallets)

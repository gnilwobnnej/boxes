# 📦 Boxes

A sophisticated 3D bin packing algorithm that intelligently packs items into pallets while maintaining structural stability.

## 🎯 What It Does

**Boxes** solves the classic bin packing problem in three dimensions. It takes a list of items with various dimensions and automatically arranges them onto the minimum number of pallets required, while respecting:

- **Physical constraints** - Items must fit within pallet boundaries
- **Stability requirements** - Items stacked above others must have at least 80% of their base supported
- **Orientation flexibility** - Items can be rotated 90° to optimize space usage

## ✨ Key Features

- **First Fit Decreasing Algorithm** - Intelligently sorts items by height and base area for optimal packing
- **3D Visualization** - Beautiful matplotlib-based 3D renderings of packed pallets
- **Stability Verification** - Ensures that stacked boxes won't topple over
- **Smart Rotation** - Automatically tries 90° rotations to fit items more efficiently
- **Detailed Reports** - Console output showing which items were rotated and pallet summaries
- **Configurable Parameters** - Easy to adjust pallet dimensions and stability thresholds

## 🚀 Getting Started

### Prerequisites

```bash
pip install matplotlib numpy
```

### Quick Start

Simply run the script:

```bash
python boxes.py
```

This will pack the default order (4 Engines, 12 Kits, 2 Panels, 6 Pumps) and generate:
- A pallet rotation report in your console
- 3D visualization images saved to the `pallet_plans/` directory

### Customization

Edit the `orders` list in the `main` execution block to define your own items:

```python
orders = [
    {"w": 24, "d": 20, "h": 20, "name": "Engine", "qty": 4},
    {"w": 12, "d": 12, "h": 12, "name": "Kit", "qty": 12},
    {"w": 30, "d": 10, "h": 40, "name": "Panel", "qty": 2},
    {"w": 15, "d": 15, "h": 15, "name": "Pump", "qty": 6}
]
```

Adjust the `PALLET_CONFIG` to change pallet dimensions:

```python
PALLET_CONFIG = (48, 40, 60)  # (width, depth, height)
```

## 📊 How It Works

### The Algorithm

1. **Initialization** - Creates a single empty pallet
2. **Sorting** - Arranges items by height and base area in descending order (First Fit Decreasing)
3. **Packing Loop** - For each item:
   - Tries to fit it in the first available pallet
   - Tests both original and rotated (90°) orientations
   - Validates stability for items placed above others
   - Creates new pallets as needed when items don't fit

### Architecture

**Box Class** - Represents individual items
- Stores dimensions (width, depth, height)
- Tracks position and rotation status
- Generates unique identifiers and colors for visualization

**Pallet Class** - Manages space and placement
- Maintains a list of available spaces
- Implements stability checking (80% support threshold by default)
- Provides pallet summaries and rotation reports

**pack_system()** - The main packing algorithm
- Orchestrates the bin packing process
- Returns a list of pallets with packed items

**visualize_and_report()** - Output generation
- Generates 3D visualizations of each pallet
- Prints detailed rotation reports
- Saves PNG images at 200 DPI to `pallet_plans/`

## 🎨 Visualization

The 3D plots show:
- **Colored boxes** - Each item type gets a random color for easy distinction
- **Red edges** - Highlight items that were rotated 90° to fit
- **Black edges** - Items in their original orientation
- **Labels** - Box names with "(R)" suffix for rotated items
- **Proper scaling** - Aspect ratios match actual pallet proportions

Example output file: `pallet_1_plan.png`

## 📋 Example Output

```
========================================
PALLET ROTATION REPORT
========================================
PALLET 1: 4x Engine, 12x Kit, 2x Panel, 6x Pump | Total: 24 units
  > Rotated items (3): ['Kit_5', 'Panel_1', 'Pump_2']
```

## 🔧 Configuration

Adjust packing behavior by modifying the `stability_threshold` in the Pallet class:

```python
pallet = Pallet(w, d, h, id, stability_threshold=0.8)  # Default: 80%
```

- **Higher values** (0.9+) - More conservative, fewer stacked items
- **Lower values** (0.6-0.7) - More aggressive packing, tighter stacks

## 📦 Project Structure

```
boxes/
├── README.md           # This file
├── boxes.py            # Main implementation
└── pallet_plans/       # Generated 3D visualizations
```

## 🤝 Contributing

Found a bug or have ideas for improvement? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Submit a pull request

## 📝 License

This project is open source and available for use.

## 💡 Use Cases

- **Logistics & Shipping** - Optimize pallet loads for warehouses
- **Supply Chain** - Minimize pallets needed for shipments
- **Warehouse Management** - Plan efficient storage layouts
- **3D Visualization** - Educational tool for understanding bin packing algorithms

---

**Made with ❤️ by gnilwobnnej**
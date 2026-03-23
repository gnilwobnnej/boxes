import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import random
import os
from collections import Counter

class Box:
    def __init__(self, w, d, h, base_name="Box", instance_id=1):
        self.w, self.d, self.h = w, d, h
        self.base_name = base_name
        self.name = f"{base_name}_{instance_id}"
        self.position = (0, 0, 0)
        self.color = [random.random() for _ in range(3)]
        self.rotated = False 

class Pallet:
    def __init__(self, w, d, h, id, stability_threshold=0.8):
        self.w, self.d, self.h = w, d, h
        self.id = id
        self.boxes = []
        self.spaces = [(0, 0, 0, w, d, h)]
        self.stability_threshold = stability_threshold

    def is_stable(self, x, y, z, bw, bd):
        if z == 0: return True
        supported_area = 0
        box_area = bw * bd
        for b in self.boxes:
            if abs((b.position[2] + b.h) - z) < 0.01:
                ix = max(0, min(x + bw, b.position[0] + b.w) - max(x, b.position[0]))
                iy = max(0, min(y + bd, b.position[1] + b.d) - max(y, b.position[1]))
                supported_area += (ix * iy)
        return (supported_area / box_area) >= self.stability_threshold

    def attempt_pack(self, box):
        self.spaces.sort(key=lambda s: (s[2], s[1], s[0]))
        for i, (sx, sy, sz, sw, sd, sh) in enumerate(self.spaces):
            # 1. Original orientation, 2. Flipped orientation
            orientations = [(box.w, box.d, False), (box.d, box.w, True)]
            for bw, bd, is_rotated in orientations:
                if bw <= sw and bd <= sd and box.h <= sh:
                    if not self.is_stable(sx, sy, sz, bw, bd):
                        continue
                    box.w, box.d = bw, bd
                    box.rotated = is_rotated
                    box.position = (sx, sy, sz)
                    self.boxes.append(box)
                    self.spaces.pop(i)
                    
                    if sw - bw > 0: self.spaces.append((sx + bw, sy, sz, sw - bw, bd, box.h))
                    if sd - bd > 0: self.spaces.append((sx, sy + bd, sz, sw, sd - bd, box.h))
                    if sh - box.h > 0: self.spaces.append((sx, sy, sz + box.h, sw, sd, sh - box.h))
                    return True
        return False

    def get_rotated_boxes(self):
        """Returns a list of boxes that were rotated 90 degrees."""
        return [box for box in self.boxes if box.rotated]

    def get_summary(self):
        counts = Counter(box.base_name for box in self.boxes)
        items_str = ", ".join([f"{qty}x {name}" for name, qty in counts.items()])
        return f"{items_str} | Total: {len(self.boxes)} units"

def pack_system(box_list, pallet_dims):
    pallets = [Pallet(*pallet_dims, id=1)]
    box_list.sort(key=lambda b: (b.h, b.w * b.d), reverse=True)
    for box in box_list:
        packed = False
        for p in pallets:
            if p.attempt_pack(box):
                packed = True
                break
        if not packed:
            new_pallet = Pallet(*pallet_dims, id=len(pallets) + 1)
            if new_pallet.attempt_pack(box): pallets.append(new_pallet)
    return pallets

def visualize_and_report(pallets):
    output_dir = "pallet_plans"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    print("\n" + "="*40 + "\nPALLET ROTATION REPORT\n" + "="*40)
    for p in pallets:
        rotated = p.get_rotated_boxes()
        print(f"PALLET {p.id}: {p.get_summary()}")
        print(f"  > Rotated items ({len(rotated)}): {[b.name for b in rotated] if rotated else 'None'}")
        
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=20, azim=45)
        ax.set_xlim(0, p.w); ax.set_ylim(0, p.d); ax.set_zlim(0, p.h)
        ax.set_box_aspect([p.w, p.d, p.h])

        for box in p.boxes:
            x, y, z = box.position
            v = np.array([[x,y,z], [x+box.w,y,z], [x+box.w,y+box.d,z], [x,y+box.d,z],
                          [x,y,z+box.h], [x+box.w,y,z+box.h], [x+box.w,y+box.d,z+box.h], [x,y+box.d,z+box.h]])
            faces = [[v[0],v[1],v[2],v[3]], [v[4],v[5],v[6],v[7]], [v[0],v[1],v[5],v[4]],
                     [v[2],v[3],v[7],v[6]], [v[0],v[3],v[7],v[4]], [v[1],v[2],v[6],v[5]]]
            
            # Highlight rotated boxes with a red edge and thicker line
            edge_color = 'red' if box.rotated else 'black'
            line_width = 1.5 if box.rotated else 0.5
            
            ax.add_collection3d(Poly3DCollection(faces, facecolors=box.color, edgecolors=edge_color, alpha=0.6, linewidths=line_width))
            
            lbl = f"{box.name}\n(R)" if box.rotated else box.name
            ax.text(x+box.w/2, y+box.d/2, z+box.h/2, lbl, fontsize=6, ha='center', weight='bold')

        plt.savefig(os.path.join(output_dir, f"pallet_{p.id}_plan.png"), dpi=200)
    plt.show()

if __name__ == "__main__":
    PALLET_CONFIG = (48, 40, 60)
    orders = [
        {"w": 24, "d": 20, "h": 20, "name": "Engine", "qty": 4},
        {"w": 12, "d": 12, "h": 12, "name": "Kit", "qty": 12},
        {"w": 30, "d": 10, "h": 40, "name": "Panel", "qty": 2},
        {"w": 15, "d": 15, "h": 15, "name": "Pump", "qty": 6}
    ]

    master_list = []
    for item in orders:
        for i in range(item["qty"]):
            master_list.append(Box(item["w"], item["d"], item["h"], item["name"], i+1))

    packed_pallets = pack_system(master_list, PALLET_CONFIG)
    visualize_and_report(packed_pallets)
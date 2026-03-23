import streamlit as st
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import random
from collections import Counter
import pandas as pd
import io

# PDF Generation Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ============================================================================
# 1. CORE LOGIC
# ============================================================================

class Box:
    def __init__(self, w, d, h, weight, base_name="Box", instance_id=1):
        self.w, self.d, self.h = w, d, h
        self.weight = weight
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
        self.base_weight = 40.0

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
            orientations = [(box.w, box.d, False), (box.d, box.w, True)]
            for bw, bd, is_rotated in orientations:
                if bw <= sw and bd <= sd and box.h <= sh:
                    if not self.is_stable(sx, sy, sz, bw, bd): continue
                    box.w, box.d, box.rotated = bw, bd, is_rotated
                    box.position = (sx, sy, sz)
                    self.boxes.append(box)
                    self.spaces.pop(i)
                    if sw - bw > 0: self.spaces.append((sx + bw, sy, sz, sw - bw, bd, box.h))
                    if sd - bd > 0: self.spaces.append((sx, sy + bd, sz, sw, sd - bd, box.h))
                    if sh - box.h > 0: self.spaces.append((sx, sy, sz + box.h, sw, sd, sh - box.h))
                    return True
        return False

    def get_total_weight(self):
        return sum(box.weight for box in self.boxes) + self.base_weight

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
            if new_pallet.attempt_pack(box): 
                pallets.append(new_pallet)
    return pallets

# ============================================================================
# 2. PDF GENERATION
# ============================================================================

def create_pdf(pallets):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Pallet Packing & Weight Report", styles['Title']))
    elements.append(Spacer(1, 12))

    for p in pallets:
        elements.append(Paragraph(f"Pallet {p.id} Details", styles['Heading2']))
        total_w = p.get_total_weight()
        elements.append(Paragraph(f"Total Pallet Weight: {total_w:.2f} lbs (Includes 40lb base)", styles['Normal']))
        elements.append(Spacer(1, 8))

        counts = Counter(box.base_name for box in p.boxes)
        data = [["Box Type", "Qty", "Unit Wt", "Subtotal"]]
        weight_ref = {box.base_name: box.weight for box in p.boxes}
        
        for name, qty in counts.items():
            u_w = weight_ref[name]
            data.append([name, str(qty), f"{u_w} lbs", f"{qty * u_w:.2f} lbs"])
        
        data.append(["Pallet Base", "1", "40.00 lbs", "40.00 lbs"])
        data.append(["TOTAL", "", "", f"{total_w:.2f} lbs"])

        t = Table(data, colWidths=[150, 50, 100, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Capture 3D Plot
        fig = plt.figure(figsize=(6, 5))
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
            ax.add_collection3d(Poly3DCollection(faces, facecolors=box.color, edgecolors='black', alpha=0.6))
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150)
        plt.close(fig)
        img_buffer.seek(0)
        elements.append(Image(img_buffer, width=400, height=300))
        elements.append(Spacer(1, 30))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ============================================================================
# 3. STREAMLIT UI
# ============================================================================

st.set_page_config(page_title="Pallet Weight Optimizer", layout="wide")
st.title("Pallet Packing & Weight Calculator")

# --- Session State Initialization ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"Name": "Auto9", "Width": 20, "Depth": 15, "Height": 4, "Weight": 15.0, "Quantity": 10}
    ])

# Sidebar Settings
with st.sidebar:
    st.header("Pallet Settings")
    p_w = st.number_input("Width (in)", value=48)
    p_d = st.number_input("Depth (in)", value=40)
    p_h = st.number_input("Max Height (in)", value=60)
    st.info("A static 40 lbs is added to each pallet for the base weight.")

# Header with Clear Button
col_header, col_btn = st.columns([5, 1])
with col_header:
    st.subheader("Box Inventory")
with col_btn:
    if st.button("Clear All", use_container_width=True):
        st.session_state.inventory = pd.DataFrame(columns=["Name", "Width", "Depth", "Height", "Weight", "Quantity"])
        st.rerun()

# Editable Table
df_input = st.data_editor(
    st.session_state.inventory, 
    num_rows="dynamic", 
    use_container_width=True,
    key="inventory_editor"
)

# Main Action
if st.button("Run Packing Plan"):
    master_list = []
    for _, row in df_input.iterrows():
        # Ensure values are numeric and not null
        qty = int(row.get("Quantity", 0)) if pd.notnull(row.get("Quantity")) else 0
        for i in range(qty):
            master_list.append(Box(
                row.get("Width", 0), 
                row.get("Depth", 0), 
                row.get("Height", 0), 
                row.get("Weight", 0), 
                row.get("Name", "Item"), 
                i+1
            ))
    
    if master_list:
        with st.spinner("Optimizing..."):
            packed_pallets = pack_system(master_list, (p_w, p_d, p_h))
            pdf_file = create_pdf(packed_pallets)
            
            st.success(f"Successfully packed items into {len(packed_pallets)} pallet(s)!")
            st.download_button("Download PDF Report", pdf_file, "manifest.pdf", "application/pdf")
            
            # Show stats
            for p in packed_pallets:
                st.write(f"**Pallet {p.id} Total Weight:** {p.get_total_weight():.2f} lbs")
    else:
        st.warning("Inventory is empty or contains zero quantities.")
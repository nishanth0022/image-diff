import streamlit as st
import requests
import json
from PIL import Image, ImageDraw
import fitz

def load_as_image(file_obj) -> Image.Image:
    name = file_obj.name.lower()
    if name.endswith((".png", ".jpg", ".jpeg")):
        return Image.open(file_obj).convert("RGB")
    elif name.endswith(".pdf"):
        doc = fitz.open(stream=file_obj.getvalue(), filetype="pdf")
        page = doc[0]
        # Match the 2.0x Matrix scaling used by the backend parser
        matrix = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=matrix)
        # Handle alpha channel if present
        mode = "RGBA" if pix.alpha else "RGB"
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        return img.convert("RGB")
    return None

def draw_bboxes(img: Image.Image, boxes_with_colors) -> Image.Image:
    draw = ImageDraw.Draw(img)
    for box, color in boxes_with_colors:
        if box:
            draw.rectangle(tuple(box), outline=color, width=3)
    return img

st.set_page_config(layout="wide", page_title="Document Diff Viewer")

st.title("📄 Image Comparison & Diff Viewer")

st.sidebar.header("API Settings")
api_url = st.sidebar.text_input("API URL", "http://127.0.0.1:8001/compare/")

st.sidebar.header("Upload Documents")
base_file = st.sidebar.file_uploader("Upload Base Document", type=["png", "jpg", "jpeg", "pdf"])
revised_files = st.sidebar.file_uploader("Upload Revised Document(s)", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if st.sidebar.button("Run Comparison", type="primary"):
    if not base_file or not revised_files:
        st.warning("Please upload both a base file and at least one revised file.")
    else:
        with st.spinner("Analyzing documents via Image Diff Engine..."):
            files_payload = [
                ("base", (base_file.name, base_file.getvalue(), base_file.type))
            ]
            for r_file in revised_files:
                files_payload.append(
                    ("revised", (r_file.name, r_file.getvalue(), r_file.type))
                )
            
            try:
                response = requests.post(api_url, files=files_payload)
                response.raise_for_status()
                data = response.json()
                
                st.success(f"Processing Complete! Compared 1 base against {data['total_revised']} revised file(s).")
                
                # Load images physically via our Pillow / PyMuPDF handler
                base_img_obj = load_as_image(base_file)
                
                for res in data["results"]:
                    st.markdown("---")
                    st.markdown(f"### Comparison Results for `{res['revised_file']}`")
                    
                    if res["status"] != "ok":
                        st.error(f"Engine failed to process file: {res.get('error')}")
                        continue
                        
                    diffs = res.get("differences", [])
                    st.write(f"**Total differences detected:** `{len(diffs)}`")
                    
                    if diffs:
                        st.dataframe(diffs, use_container_width=True)
                    
                    rev_file_match = next((f for f in revised_files if f.name == res['revised_file']), None)
                    rev_img_obj = load_as_image(rev_file_match) if rev_file_match else None
                        
                    if base_img_obj and rev_img_obj:
                        st.markdown("#### Visual Boundary Map")
                        st.markdown("> 🔴 **Red** = Removed | 🟢 **Green** = Added | 🟡 **Yellow** = Modified/Shifted")
                        
                        base_boxes = []
                        rev_boxes = []
                        
                        for d in diffs:
                            c_type = d["change"]
                            b_box = d.get("bbox")
                            r_box = d.get("revised_bbox") or d.get("bbox")  # fallback if single box provided
                            
                            if c_type == "removed" and b_box:
                                base_boxes.append((b_box, "red"))
                            elif c_type == "added" and r_box:
                                rev_boxes.append((r_box, "green"))
                            elif c_type in ["modified", "shift"]:
                                if b_box: base_boxes.append((b_box, "gold"))
                                if r_box: rev_boxes.append((r_box, "gold"))
                        
                        drawn_base = draw_bboxes(base_img_obj.copy(), base_boxes)
                        drawn_rev = draw_bboxes(rev_img_obj.copy(), rev_boxes)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(drawn_base, caption=f"BASE: {base_file.name}", use_container_width=True)
                        with col2:
                            st.image(drawn_rev, caption=f"REVISED: {rev_file_match.name}", use_container_width=True)
                    else:
                        st.info("Visual boundary box overlays could not be generated for this file format.")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"API Request to Core Engine Failed: {e}")

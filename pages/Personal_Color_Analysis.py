import streamlit as st
from PIL import Image, ImageOps
from translations import translations
import torch
from torchvision import transforms
import facer
import pandas as pd
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

image_directory = "./assets/person-bounding-box.png"
image = Image.open(image_directory)

PAGE_CONFIG = {"page_title":"Personal Color Analysis", 
               "page_icon":image, 
               "layout":"wide", 
               "initial_sidebar_state":"auto"}

st.set_page_config(**PAGE_CONFIG)


st.logo('./assets/logo.png', size="large")

# Default language in session state
if "language" not in st.session_state:
    st.session_state.language = "en"

# Sidebar for language selection
with st.sidebar:
    lang = st.session_state.language
    st.header(translations[lang]["header_language"])
    if st.button("EN"):
        st.session_state.language = "en"
    if st.button("ID"):
        st.session_state.language = "id"

# Model and facer initialization
model = mobilenet_v2(weights=MobileNet_V2_Weights.DEFAULT) 
num_classes = 4  # Ganti dengan jumlah kelas Anda

# Sesuaikan output layer (fc) dengan jumlah kelas yang diinginkan
model.classifier[1]= torch.nn.Linear(model.classifier[1].in_features, num_classes)

MODEL_PATH = "./best_mobilenetv2_model.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
state_dict = torch.load(MODEL_PATH, map_location=device, weights_only=True)
model.load_state_dict(state_dict)  # Muat ke model
model = model.to(device)  # Pindahkan ke device
model.eval()  # Set model ke mode evaluasi

# Define image transformations
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Initialize facer detectors and parsers
face_detector = facer.face_detector('retinaface/mobilenet', device=device)
face_parser = facer.face_parser('farl/lapa/448', device=device)

# Load colors.csv
colors_csv_path = "./assets/colors.csv"
colors_df = pd.read_csv(colors_csv_path)

# Function to analysis the personal color
def upload_img(uploaded_image):
    # Face detection and personal color analysis
        img_tensor = transforms.ToTensor()(uploaded_image).unsqueeze(0).to(device)
        with torch.no_grad():
            detections = face_detector(img_tensor)

        if len(detections) == 0:
            st.error((translations[lang]["error_detect"]))
        else:
            st.success((translations[lang]["success_detect"]))
            
            

# Function to classify and display recommended colors
def classify_spca(uploaded_image):
    processed_image = transform(uploaded_image).unsqueeze(0).to(device)
    with torch.no_grad():
        predictions = model(processed_image)
        confidences = torch.nn.functional.softmax(predictions, dim=1).cpu().numpy()[0]

    # Mapping seasons to predictions
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    predicted_index = confidences.argmax()
    predicted_season = seasons[predicted_index]
    confidence_percentage = confidences[predicted_index] * 100

    st.write((translations[lang]["season_type"]), f"**{predicted_season}**")
    st.write((translations[lang]["confidence"]),  f"**{confidence_percentage:.2f}%**")

    # Filter warna berdasarkan musim yang diprediksi
    season_colors = colors_df[colors_df['season'] == predicted_season]

    st.write((translations[lang]["recommendation"]), f"{predicted_season}:")
    
    # Create table with 8 colors per row
    colors_per_row = 5
    rows = [season_colors[i:i+colors_per_row] for i in range(0, len(season_colors), colors_per_row)]

    for row in rows:
        columns = st.columns(len(row))
        for col, (_, color) in zip(columns, row.iterrows()):
            hex_code = color['hex']
            with col:
                # Display color block
                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <div style="background-color: {hex_code}; width: 50px; height: 50px; border-radius: 50%; margin: 0 auto; box-shadow: 0 0 5px rgba(0,0,0,0.3);"></div>
                        <div style="margin-top: 5px; font-size: 14px; color: #333;">{hex_code}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

# Function for the analysis page
def analysis_page():
    st.title(translations[lang]["analysis_title"])

    # Membuat dua kolom
    col1, col2 = st.columns(2)

    # Kolom Kiri: Upload Gambar
    with col1:
        uploaded_file = st.file_uploader(translations[lang]["upload_image"],type=["jpg", "png"])

        # Simpan file yang diunggah secara lokal
        if uploaded_file is not None:
            uploaded_image_path = "temp_uploaded_image.jpg"
            with open(uploaded_image_path, "wb") as f:
                f.write(uploaded_file.read())

            # Tampilkan gambar yang diunggah
            uploaded_image = Image.open(uploaded_file).convert("RGB")
            uploaded_image = ImageOps.exif_transpose(uploaded_image)
            st.image(uploaded_image, use_container_width=True)
        else:
            st.warning(translations[lang]["warning_2"])

    # Kolom Kanan: Hasil Analisis
    with col2:
        st.write(translations[lang]["analyze_result"])
        
        if uploaded_file is not None:
            # Deteksi wajah dan analisis personal color
            upload_img(uploaded_image)

            if st.button("Start Analysis"):
                classify_spca(uploaded_image)
        else:
            st.info(translations[lang]["upload_info"])

# Run the analysis page
analysis_page()

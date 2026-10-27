# 🏠 Floorplan to Blender 3D (GLB) Generator

An AI-powered pipeline and web application that converts 2D residential floor plan images (PNG, JPG, BMP, TIFF, WebP) into production-ready, topologically clean 3D models (`.glb`) natively importable into Blender and interactive in web 3D viewers.

---

## ✨ Features

- **AI Architectural Segmentation:** Uses a ResNet-34 UNet trained on CubiCasa5K-style floor plan data to identify:
  - `Wall` (ID 1)
  - `Door` (ID 2)
  - `Window` (ID 3)
  - `Floor/Background` (ID 0)
- **Aspect-Preserving Letterboxing:** Centers and letterboxes arbitrary aspect-ratio floor plans on a 512×512 canvas so walls and openings retain their true scale without stretching.
- **Real Boolean Wall Openings:** Performs 2D Shapely difference operations (`wall.difference(openings)`) so that doorways and window cutouts punch real topological holes through the walls.
- **Architectural Lintels & Sills:**
  - **Main Walls:** Full-height structural walls ($2.70\text{ m}$).
  - **Door Lintels:** Wall header sections above doors ($2.00\text{ m} \rightarrow 2.70\text{ m}$).
  - **Doors:** Wooden door panels ($0.00\text{ m} \rightarrow 2.00\text{ m}$).
  - **Window Sills:** Wall under window openings ($0.00\text{ m} \rightarrow 0.85\text{ m}$).
  - **Window Lintels:** Wall header above windows ($1.90\text{ m} \rightarrow 2.70\text{ m}$).
  - **Window Glass:** Semi-transparent architectural glass panes ($0.85\text{ m} \rightarrow 1.90\text{ m}$).
  - **Foundation Slab:** Baseplate floor extended $0.6\text{ m}$ past perimeter ($-0.15\text{ m} \rightarrow 0.00\text{ m}$).
- **Native Blender & glTF 2.0 Alignment:** Exported models adhere to the glTF 2.0 standard ($Y$-Up), which Blender's official glTF importer maps automatically to native $Z$-Up at $(0,0,0)$ origin in real-world meters.
- **Interactive Web App:** Dark-mode interface powered by Google `<model-viewer>`, supporting drag-and-drop uploads, one-click built-in sample tests, orbit controls, camera reset, and instant `.glb` download.

---

## 💻 System Requirements

- **Operating System:** Windows 10/11, Ubuntu 20.04+, Debian, Fedora, or macOS.
- **Python Version:** **Python 3.10, 3.11, or 3.12** (*Python 3.11 or 3.12 is strongly recommended for Windows binary wheels*).
- **Blender (Optional, for 3D editing):** Blender 3.6 LTS, 4.x, or 5.x.

---

## 🚀 Windows Installation & Running Guide

### Option 1: One-Click Launcher (Easiest)
Simply double-click the **`run_windows.bat`** file in the project folder. It will:
1. Verify Python is installed and added to PATH.
2. Create a clean virtual environment (`venv`).
3. Upgrade `pip` and install all required libraries.
4. Launch the local web server at `http://localhost:5000`.

---

### Option 2: Manual Windows Setup (Command Prompt / PowerShell)

Open PowerShell or Command Prompt inside the project directory:

```powershell
# 1. Verify your Python version (must be 3.10, 3.11, or 3.12)
python --version

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# In Command Prompt (cmd.exe):
venv\Scripts\activate.bat
# OR in PowerShell:
venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install PyTorch (CPU version for universal Windows compatibility)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 6. Install all other project dependencies
pip install -r requirements.txt

# 7. Start the Web App
python app.py
```

Now open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 🐧 Linux / macOS Installation & Running Guide

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Start the application
python3 app.py
```
Or run directly:
```bash
chmod +x run.sh
./run.sh
```

---

## 🎨 How to Open the Output in Blender

1. Generate your 3D model in the web UI and click **"📥 Download Blender GLB"**.
2. Launch **Blender**.
3. Go to **`File` → `Import` → `glTF 2.0 (.glb/.gltf)`**.
4. Select your downloaded `.glb` file.
5. In Blender's Outliner (top-right), you will find separated, organized architectural components:
   - `walls`
   - `doors`
   - `door_lintels`
   - `window_sills`
   - `window_lintels`
   - `window_glass`
   - `floor_slab`
6. Switch Viewport Shading to **Material Preview** or **Rendered** to see architectural materials and transparency.

---

## 📂 Project Structure

```
floorplan2blend-app/
├── app.py                  # Flask web server & REST API
├── requirements.txt        # Verified cross-platform dependencies
├── run_windows.bat         # 1-click Windows runner
├── run.sh                  # 1-click Linux/macOS runner
├── README.md               # Documentation & setup guide
├── .gitignore              # Git ignore rules for virtualenvs and sessions
├── weights/
│   ├── best.safetensors    # Pretrained ResNet34-UNet segmentation weights
│   └── config.yaml         # Training configuration
├── samples/                # Built-in real floor plans from GitHub
│   ├── example.png
│   ├── floorplan_apartment.png
│   ├── floorplan_cottage.png
│   ├── floorplan_duplex.png
│   ├── floorplan_villa.png
│   └── real_floorplan.png
├── src/
│   ├── __init__.py
│   ├── labels.py           # Class IDs, architectural heights & color tokens
│   ├── model.py            # SMP UNet architecture builder
│   ├── preprocess.py       # Aspect-ratio preserving letterbox padding
│   ├── extract.py          # Contour extraction, morphology & Shapely vectorization
│   ├── generate_3d.py      # Boolean opening cuts, lintels, sills & glTF assembly
│   └── pipeline.py         # End-to-end pipeline runner
└── templates/
    └── index.html          # Modern dark-mode UI with Google <model-viewer>
```

---

## 📤 Pushing to Your GitHub Repository

To push this codebase to a new or existing GitHub repository:

```bash
# 1. Initialize Git in the project directory
git init

# 2. Add all files
git add .

# 3. Create the initial commit
git commit -m "feat: complete floorplan to Blender 3D pipeline with boolean openings and web viewer"

# 4. Set the default branch to main
git branch -M main

# 5. Add your GitHub remote repository (replace with your repo URL)
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git

# 6. Push to GitHub
git push -u origin main
```
*(Note: `weights/best.safetensors` is ~94MB and fits within GitHub's 100MB file limit. If you use Git LFS, run `git lfs track "*.safetensors"`).*

---

## 📜 License

MIT License. Free for personal, research, and commercial use.

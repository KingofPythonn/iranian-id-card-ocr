# Iranian ID Card OCR Scanner 🪪🔍

An end-to-end computer vision and OCR system for scanning Iranian national ID cards and extracting structured personal information into an Excel file.

This project uses a browser-based camera interface, OpenCV image processing, EasyOCR text recognition, FastAPI backend services, and rule-based validation to detect an ID card, correct its perspective, extract key fields, and export the result in a structured format.

---

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-blueviolet)
![EasyOCR](https://img.shields.io/badge/OCR-EasyOCR-orange)
![Pandas](https://img.shields.io/badge/Pandas-Excel%20Export-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Prototype-lightgrey)

---

## 🚀 Features

- 📷 Mobile-friendly browser camera interface
- 🟩 On-screen alignment frame for positioning the ID card
- ✂️ Image capture and cropping using the HTML Canvas API
- 🌐 FastAPI backend for receiving and processing uploaded images
- 🧠 ID card detection using OpenCV
- 🔄 Perspective correction and card warping
- 🖼 Image preprocessing for better OCR accuracy
- 🔍 Persian and English OCR using EasyOCR
- 📝 Extraction of key identity-card fields:
  - National ID number
  - First name
  - Family name
  - Father’s name
  - Birth date
- 🔢 Persian/Arabic digit normalization
- ✅ Iranian national ID checksum validation
- 🛠 Rule-based correction for common OCR errors
- 📊 Automatic Excel output generation
- 🧪 Debug outputs for received image, warped image, and OCR regions
- 🔐 HTTPS support for mobile camera access during local testing

---

## 📌 Project Purpose

Manual data entry from identity documents is slow, repetitive, and prone to mistakes.

This project was developed as a computer vision and software engineering prototype to automate information extraction from Iranian national ID cards. It combines image processing, OCR, validation logic, and structured data export in one complete workflow.

The goal is not only to read text from an image, but also to build a practical pipeline that can:

1. Capture the document image
2. Isolate the card region
3. Correct perspective distortion
4. Recognize Persian and numerical text
5. Clean and validate extracted values
6. Save the result in an Excel file

---

## 🧠 How It Works

The main processing pipeline is:

```text
Input Image
   ↓
Card Detection
   ↓
Perspective Correction / Warping
   ↓
Image Preprocessing
   ↓
OCR
   ↓
Field Extraction
   ↓
Post-processing and Validation
   ↓
Excel Output
```

### Workflow

1. The user opens the camera page in a browser.
2. The ID card is placed inside the on-screen guide frame.
3. The current camera frame is captured.
4. The selected card region is cropped using the Canvas API.
5. The cropped image is uploaded to the FastAPI backend.
6. OpenCV processes the image and performs perspective correction.
7. EasyOCR reads Persian and numerical text from the card.
8. The backend extracts fields such as name, family name, father’s name, birth date, and national ID number.
9. Rule-based validation and normalization are applied.
10. The final extracted information is saved into an Excel file.

---

## 🛠 Technologies Used

### Frontend

- HTML
- React
- Tailwind CSS
- Browser Camera API
- Canvas API

### Backend

- Python
- FastAPI
- Uvicorn
- OpenCV
- EasyOCR
- NumPy
- Pandas
- RapidFuzz, optional, for fuzzy text/label matching

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/KingofPythonn/iranian-id-card-ocr.git
cd iranian-id-card-ocr
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install opencv-python-headless numpy pandas fastapi easyocr uvicorn
```

Optional dependency for fuzzy matching:

```bash
pip install rapidfuzz
```

Optional dependency for EasyOCR GPU support:

```bash
pip install torch torchvision torchaudio
```

---

## 🧪 Usage

Run the backend server from the project root:

```bash
python server.py
```

If HTTPS is configured, the server can be accessed at:

```text
https://localhost:8443
```

Open the camera interface locally:

```text
https://localhost:8443/camera.html
```

To use the camera interface from a phone:

1. Connect your phone and laptop to the same Wi-Fi network.
2. Find your laptop IPv4 address.
3. Open the following URL on your phone:

```text
https://YOUR_LAPTOP_IP:8443/camera.html
```

Example:

```text
https://192.168.1.20:8443/camera.html
```

If the browser shows a warning because of the self-signed certificate, choose the advanced option and continue for local testing.

---

## 🔐 HTTPS Setup for Mobile Camera Access

Mobile browsers usually require HTTPS to allow camera access.

For local testing, you can generate a self-signed certificate.

### Windows Git Bash

```bash
"C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -newkey rsa:2048 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

### PowerShell

```powershell
& "C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -newkey rsa:2048 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

After generating the certificate files, place them in the same directory as the backend script.

---

## 📁 Output Files

The backend can generate several output files during processing.

| File                | Description                                        |
| ------------------- | -------------------------------------------------- |
| `results.xlsx`      | Excel file containing extracted records            |
| `last_received.png` | Last uploaded raw image                            |
| `last_warped.png`   | Perspective-corrected card image                   |
| `last_debug.png`    | Debug image showing OCR boxes and selected regions |

### Example Excel Fields

| Field            | Description                      |
| ---------------- | -------------------------------- |
| `timestamp`      | Date and time of processing      |
| `national_id`    | Validated national ID number     |
| `raw_nid_digits` | Raw OCR digits before correction |
| `name`           | Extracted first name             |
| `family`         | Extracted family name            |
| `father`         | Extracted father’s name          |
| `birth_date`     | Extracted birth date             |
| `raw_text`       | Raw OCR output                   |

---

## 🔌 API Endpoints

| Endpoint          | Description                                                  |
| ----------------- | ------------------------------------------------------------ |
| `/`               | Serves the main page                                         |
| `/camera.html`    | Serves the camera interface                                  |
| `/process-photo`  | Receives and processes uploaded ID card images               |
| `/image-last`     | Displays the last received image                             |
| `/warped-last`    | Displays the last warped card image                          |
| `/debug-last`     | Displays the debug image with OCR boxes and selected regions |
| `/excel-download` | Downloads the Excel output file                              |

---

## 🧠 OCR and Validation Logic

The backend includes several post-processing methods to improve extraction quality:

- Persian and Arabic digits are normalized to standard Latin digits.
- Birth dates are extracted using regular expressions.
- National ID numbers are validated using checksum logic.
- OCR artifacts and unnecessary characters are cleaned.
- Fuzzy matching can be used to detect Persian field labels even when OCR output is imperfect.
- Fixed regions of interest are used as fallback extraction zones after card warping.
- Debug images are generated to help inspect OCR boxes and selected regions.

---

## 📂 Project Structure

```text
iranian-id-card-ocr/
├── README.md
├── LICENSE
├── .gitignore
├── server.py
├── camera.html
├── cert.pem
├── key.pem
├── Project Report.pdf
├── results.xlsx
├── last_received.png
├── last_warped.png
├── last_debug.png
└── requirements.txt
```

> **Note:** The exact structure may vary depending on the final repository files.

---

## 🖼 Demo

Add screenshots here after uploading demo images to the repository.

```markdown
![Camera Interface](demo/screenshots/camera_interface.png)
![Warped Card](demo/screenshots/warped_card.png)
![Debug Output](demo/screenshots/debug_output.png)
```

Example output file:

```markdown
[Download sample Excel output](demo/sample_output.xlsx)
```

Use only synthetic, anonymized, blurred, or non-sensitive demo data.

---

## ⚠️ Privacy Notice

This project is intended for educational and research demonstration purposes.

Do not upload real national ID card images, real personal information, or private extracted data to a public repository.

Any demo images or Excel files included in this repository should be synthetic, anonymized, blurred, or used only for demonstration.

---

## 🚧 Limitations

- OCR accuracy depends on image quality, lighting, alignment, and resolution.
- Persian text recognition may produce errors depending on font, blur, and contrast.
- Rule-based extraction may need adjustment for different ID card layouts.
- The project is a prototype and has not been tested on a large-scale real-world dataset.
- Self-signed HTTPS certificates are suitable for local testing only, not production deployment.

---

## 🔮 Future Improvements

- Improve Persian OCR post-processing
- Add a larger evaluation dataset
- Add machine-learning-based document layout detection
- Improve recognition under low-light or blurry conditions
- Add a web dashboard for reviewing and correcting OCR results
- Store extracted records in a database
- Add Docker support
- Add automated tests
- Separate frontend and backend for production deployment

---

## 🛡 License

This project is licensed under the MIT License.

Feel free to use, modify, and share it.

---

## 🙌 Credits

- [FastAPI](https://fastapi.tiangolo.com/) – backend API framework
- [OpenCV](https://opencv.org/) – computer vision and image processing
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) – optical character recognition
- [Pandas](https://pandas.pydata.org/) – Excel/data handling
- [Tailwind CSS](https://tailwindcss.com/) – frontend styling
- [React](https://react.dev/) – browser interface

---

## 📬 Contact

Created by **Sina Abbaszadeh Balanga**

- GitHub: [KingofPythonn](https://github.com/KingofPythonn)
- LinkedIn: [Sina Abbaszadeh](https://www.linkedin.com/in/sina-abbaszadeh-08bab2248)

# Iranian ID Card OCR Scanner

A computer vision and OCR prototype for scanning Iranian national ID cards and extracting key information into an Excel file.

The project includes a browser-based camera interface, a FastAPI backend, OpenCV-based image processing, EasyOCR text recognition, and validation logic for Iranian national ID numbers.

---

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-blueviolet)
![EasyOCR](https://img.shields.io/badge/OCR-EasyOCR-orange)
![Pandas](https://img.shields.io/badge/Pandas-Excel%20Export-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Prototype-lightgrey)

---

## Features

- Browser camera interface for capturing ID card images
- Mobile-friendly card alignment frame
- Image cropping with the Canvas API
- FastAPI backend for image upload and processing
- Card detection and perspective correction using OpenCV
- Image preprocessing to improve OCR results
- Persian and English OCR using EasyOCR
- Extraction of:
  - National ID number
  - First name
  - Family name
  - Father’s name
  - Birth date
- Persian and Arabic digit normalization
- Iranian national ID checksum validation
- Basic correction rules for common OCR mistakes
- Excel export using Pandas
- Debug images for checking OCR regions and warped cards
- HTTPS support for local mobile camera testing

---

## Project Overview

This project was built as a prototype for automating data entry from Iranian national ID cards.

Instead of manually typing information from a card, the system captures an image, detects the card area, corrects the perspective, runs OCR, validates the extracted values, and saves the final result in a structured Excel file.

- [Project*report_in* english](<https://github.com/KingofPythonn/iranian-id-card-ocr/blob/main/docs/Project%20Report(in%20English)%20.pdf>)

The full workflow is:

```text
Input Image
   ↓
Card Detection
   ↓
Perspective Correction
   ↓
Image Preprocessing
   ↓
OCR
   ↓
Field Extraction
   ↓
Validation
   ↓
Excel Output
```

---

## How It Works

1. The user opens the camera page in a browser.
2. The ID card is placed inside the guide frame.
3. The browser captures the current camera frame.
4. The selected area is cropped with the Canvas API.
5. The cropped image is sent to the FastAPI backend.
6. OpenCV detects and warps the card.
7. EasyOCR reads the visible text.
8. The backend extracts fields such as name, family name, father’s name, birth date, and national ID.
9. The extracted data is cleaned, normalized, and validated.
10. The final record is saved to an Excel file.

---

## Technologies

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
- RapidFuzz, optional, for fuzzy label matching

---

## Installation

Clone the repository:

```bash
git clone https://github.com/KingofPythonn/iranian-id-card-ocr.git
cd iranian-id-card-ocr
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install opencv-python-headless numpy pandas fastapi easyocr uvicorn
```

Optional fuzzy matching support:

```bash
pip install rapidfuzz
```

Optional GPU support for EasyOCR:

```bash
pip install torch torchvision torchaudio
```

---

## Usage

Run the backend server:

```bash
python server.py
```

Open the local camera page:

```text
https://localhost:8443/camera.html
```

To open it from a phone:

1. Connect the phone and laptop to the same Wi-Fi network.
2. Find the laptop’s IPv4 address.
3. Open this address on the phone:

```text
https://YOUR_LAPTOP_IP:8443/camera.html
```

Example:

```text
https://192.168.1.20:8443/camera.html
```

For local testing with a self-signed certificate, the browser may show a security warning. Use the advanced option to continue.

---

## HTTPS Setup

Mobile browsers usually require HTTPS before allowing camera access.

For local testing, generate a self-signed certificate.

### Windows Git Bash

```bash
"C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -newkey rsa:2048 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

### PowerShell

```powershell
& "C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -newkey rsa:2048 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"
```

Place `cert.pem` and `key.pem` in the same directory as the backend script.

---

## Output Files

| File                | Description                                     |
| ------------------- | ----------------------------------------------- |
| `results.xlsx`      | Excel file containing extracted records         |
| `last_received.png` | Last uploaded raw image                         |
| `last_warped.png`   | Perspective-corrected card image                |
| `last_debug.png`    | Debug image with OCR boxes and selected regions |

---

## Excel Fields

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

## API Endpoints

| Endpoint          | Description                            |
| ----------------- | -------------------------------------- |
| `/`               | Serves the main page                   |
| `/camera.html`    | Serves the camera interface            |
| `/process-photo`  | Receives and processes uploaded images |
| `/image-last`     | Shows the last received image          |
| `/warped-last`    | Shows the last warped card image       |
| `/debug-last`     | Shows the debug image                  |
| `/excel-download` | Downloads the Excel output file        |

---

## OCR and Validation

The backend applies several cleanup and validation steps after OCR:

- Converts Persian and Arabic digits to Latin digits
- Extracts birth dates with regular expressions
- Validates Iranian national ID numbers using checksum logic
- Removes common OCR artifacts
- Optionally uses fuzzy matching for Persian field labels
- Uses fixed regions of interest as fallback extraction zones
- Saves debug images to make OCR errors easier to inspect

---

## Project Structure

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

The exact structure may change as the project develops.

---

## Demo

Add screenshots after uploading demo images to the repository.

![Camera Interface](demo/screenshots/camera_interface.png)
![Warped Card](demo/screenshots/warped_card.png)
![Debug Output](demo/screenshots/debug_output.png)

Example output file:

[Download sample Excel output](demo/sample_output.xlsx)

Use only synthetic, anonymized, blurred, or non-sensitive demo data.

---

## Privacy Notice

This project is intended for educational and research use.

Do not upload real national ID card images, personal information, or extracted private data to a public repository.

Any demo files included in the repository should be synthetic, anonymized, blurred, or safe for public use.

---

## Limitations

- OCR accuracy depends on image quality, lighting, focus, and alignment.
- Persian text recognition may still produce mistakes.
- Rule-based extraction may need changes for different card layouts.
- The system is a prototype and has not been tested on a large real-world dataset.
- Self-signed HTTPS certificates are only suitable for local testing.

---

## Future Improvements

- Improve Persian OCR cleanup
- Add a larger test dataset
- Add document layout detection
- Improve performance with low-light or blurry images
- Add a review dashboard for correcting OCR results
- Save records to a database
- Add Docker support
- Add automated tests
- Split frontend and backend for production deployment

---

## License

This project is licensed under the MIT License.

---

## Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenCV](https://opencv.org/)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [Pandas](https://pandas.pydata.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React](https://react.dev/)

---

## Contact

Created by **Sina Abbaszadeh Balanga**

- GitHub: [KingofPythonn](https://github.com/KingofPythonn)
- LinkedIn: [Sina Abbaszadeh](https://www.linkedin.com/in/sina-abbaszadeh-08bab2248)

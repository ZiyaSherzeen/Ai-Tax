TaxCal is an automated tax filing tool designed to simplify the tax filing process for individual taxpayers in India. The system extracts financial data from scanned documents using OCR, categorizes the data into various income components and deductions, and computes tax liabilities under both the old and new tax regimes. Additionally, the tool pre-fills a fillable ITR PDF form with the computed values, all while formatting the output in the Indian numeric style.

Features
OCR-based Data Extraction:
Uses Tesseract OCR with OpenCV to extract text from scanned tax documents.

Data Parsing & Categorizatio:
Leverages regular expressions to identify and categorize key financial details such as:

Identification Details (PAN, Aadhaar)
Income Components (Salary, Business, Interest, Rental, Capital Gains)
Exempt/Non-Taxable Income (Agricultural, Dividend Income)
Deductions (Sections 80C, 80D, 80E, 80G)
Tax Calculation:
Computes tax liabilities using:

Old Regime:
0% up to ₹2.5L, 5% for ₹2.5L–₹5L, 20% for ₹5L–₹10L, and 30% for income above ₹10L.
New Regime:
A detailed slab system including 0%, 5%, 10%, 15%, 20%, 25%, and 30% based on income thresholds.
Numeric Formatting:
Formats all outputs (e.g., taxable income, deductions, tax liability).
PDF Form Filling:
Automatically pre-fills a provided fillable ITR PDF form with the extracted and computed data using pdfrw.

Deduction Suggestions:
Provides tailored recommendations for maximizing deductions to lower taxable income.

Technologies Used
Python: Core language for implementation.
Tesseract OCR & pytesseract: For text extraction from images.
OpenCV: For image preprocessing (grayscale conversion, adaptive thresholding).
Regular Expressions (re): For parsing and categorizing financial data.
pdfrw: For reading and writing fillable PDF forms.

Setup & Installation
Clone the Repository:
git clone https://github.com/yourusername/tax-assistant.git
cd tax-assistant

Install Dependencies:
pip install opencv-python pytesseract pdfrw

Install Tesseract OCR:
Download and install Tesseract OCR from here if it is not already installed.
Update the Tesseract path in the code (pytesseract.pytesseract.tesseract_cmd) if necessary.

Prepare Input Files:
Place your scanned tax document image (e.g., tax.png) in the project directory.
Ensure that you have a fillable PDF (e.g., itr2_1_b170f8ce37.pdf) for pre-filling.

Run the Tax Calculation:
python app.py

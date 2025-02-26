import cv2
import pytesseract
import re
from pdfrw import PdfReader, PdfWriter

###############################################################################
# 1. Configure Tesseract
###############################################################################
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

###############################################################################
# 2. OCR Extraction Function
###############################################################################
def extract_text(file_path):
    """
    Reads an image from the given file path, applies pre-processing,
    and extracts text using Tesseract OCR.
    """
    image = cv2.imread(file_path)
    if image is None:
        raise FileNotFoundError(f"Could not read the image file: {file_path}")
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    text = pytesseract.image_to_string(processed)
    # Remove unwanted symbols that may interfere with matching
    text = text.replace("©", "")
    return text

###############################################################################
# 3. Field Extraction Helper
###############################################################################
def extract_field_value(text, field_name):
    """
    Extracts a numeric value following a pattern like:
       "<field_name>: [non-digit]* 1,23,456.78"
    The regex accepts commas and an optional decimal part (up to 2 digits).
    Returns the value as a float (or 0.0 if not found).
    """
    pattern = re.escape(field_name) + r":\s*\D*([\d,]+(?:\.\d{1,2})?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        value_str = match.group(1).replace(',', '')
        try:
            return float(value_str)
        except ValueError:
            return 0.0
    return 0.0

###############################################################################
# 4. Indian Number Formatting Helper
###############################################################################
def format_indian(n):
    """
    Formats a number into Indian numeric style with commas and two decimal places.
    Example: 100000 -> "1,00,000.00"
    """
    s = "{:.2f}".format(n)
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Reverse remaining digits and group them in twos
        remaining_rev = remaining[::-1]
        groups = [remaining_rev[i:i+2] for i in range(0, len(remaining_rev), 2)]
        formatted_remaining = ','.join(groups)[::-1]
        formatted_integer = formatted_remaining + ',' + last_three
    else:
        formatted_integer = integer_part
    return formatted_integer + '.' + decimal_part

###############################################################################
# 5. Main Parsing Logic
###############################################################################
def parse_data(text):
    """
    Parses the OCR text to extract various fields.
    Expected fields (based on your sample):
      - PAN, Aadhaar
      - Income Details:
          Salary Income, Business Income, Interest Income (Fixed Deposits),
          Rental Income, Short-Term Capital Gains, Long-Term Capital Gains,
          Standard Deduction (Salary), Home Loan Interest.
      - Exempt (Non-Taxable) Income:
          Agricultural Income, Dividend Income.
      - Deductions:
          Section 80C, Section 80D, Section 80E, Section 806 (for 80G).
    """
    # PAN and Aadhaar:
    pan_match = re.search(r'PAN:\s*([A-Z]{5}[0-9]{4}[A-Z])', text, re.IGNORECASE)
    pan = pan_match.group(1) if pan_match else None

    aadhaar_match = re.search(r'Aadhaar:\s*(\d{4}\s?\d{4}\s?\d{4})', text, re.IGNORECASE)
    aadhaar = aadhaar_match.group(1) if aadhaar_match else None

    # Income fields:
    salary_income = extract_field_value(text, "Salary Income")
    business_income = extract_field_value(text, "Business Income")
    interest_income = extract_field_value(text, "Interest Income (Fixed Deposits)")
    rental_income = extract_field_value(text, "Rental Income")
    short_term_gains = extract_field_value(text, "Short-Term Capital Gains")
    long_term_gains = extract_field_value(text, "Long-Term Capital Gains")

    # Adjustments:
    standard_deduction = extract_field_value(text, "Standard Deduction (Salary)")
    home_loan_interest = extract_field_value(text, "Home Loan Interest")

    # Non-taxable income:
    agricultural_income = extract_field_value(text, "Agricultural Income")
    dividend_income = extract_field_value(text, "Dividend Income")
    non_taxable_income = agricultural_income + dividend_income

    # Deductions:
    section_80c = extract_field_value(text, "Section 80C")
    section_80d = extract_field_value(text, "Section 80D")
    section_80e = extract_field_value(text, "Section 80E")
    section_80g = extract_field_value(text, "Section 806")  # OCR may misread 80G as 806

    return {
        "pan": pan,
        "aadhaar": aadhaar,
        "salary_income": salary_income,
        "business_income": business_income,
        "interest_income": interest_income,
        "rental_income": rental_income,
        "short_term_gains": short_term_gains,
        "long_term_gains": long_term_gains,
        "standard_deduction": standard_deduction,
        "home_loan_interest": home_loan_interest,
        "non_taxable_income": non_taxable_income,
        "section_80c": section_80c,
        "section_80d": section_80d,
        "section_80e": section_80e,
        "section_80g": section_80g
    }

###############################################################################
# 6. Tax Calculation (Old Regime)
###############################################################################
def calculate_tax_old_regime(net_taxable_income):
    """
    Applies the old regime tax slabs for FY 2023-24:
      - Up to ₹2.5L: 0%
      - ₹2.5L to ₹5L: 5%
      - ₹5L to ₹10L: 20%
      - Above ₹10L: 30%
    """
    tax = 0
    if net_taxable_income <= 250000:
        tax = 0
    elif net_taxable_income <= 500000:
        tax = (net_taxable_income - 250000) * 0.05
    elif net_taxable_income <= 1000000:
        tax = (250000 * 0.05) + (net_taxable_income - 500000) * 0.20
    else:
        tax = (250000 * 0.05) + (500000 * 0.20) + (net_taxable_income - 1000000) * 0.30
    return tax

###############################################################################
# 7. Tax Calculation (New Regime)
###############################################################################
def calculate_tax_new_regime(net_taxable_income):
    """
    Applies the new regime tax slabs for FY 2023-24:
      - Up to ₹2.5L: 0%
      - ₹2.5L to ₹5L: 5%
      - ₹5L to ₹7.5L: 10%
      - ₹7.5L to ₹10L: 15%
      - ₹10L to ₹12.5L: 20%
      - ₹12.5L to ₹15L: 25%
      - Above ₹15L: 30%
    """
    tax = 0
    if net_taxable_income <= 250000:
        tax = 0
    elif net_taxable_income <= 500000:
        tax = (net_taxable_income - 250000) * 0.05
    elif net_taxable_income <= 750000:
        tax = (250000 * 0.05) + (net_taxable_income - 500000) * 0.10
    elif net_taxable_income <= 1000000:
        tax = (250000 * 0.05) + (250000 * 0.10) + (net_taxable_income - 750000) * 0.15
    elif net_taxable_income <= 1250000:
        tax = (250000 * 0.05) + (250000 * 0.10) + (250000 * 0.15) + (net_taxable_income - 1000000) * 0.20
    elif net_taxable_income <= 1500000:
        tax = (250000 * 0.05) + (250000 * 0.10) + (250000 * 0.15) + (250000 * 0.20) + (net_taxable_income - 1250000) * 0.25
    else:
        tax = (250000 * 0.05) + (250000 * 0.10) + (250000 * 0.15) + (250000 * 0.20) + (250000 * 0.25) + (net_taxable_income - 1500000) * 0.30
    return tax

###############################################################################
# 8. Deduction Suggestions
###############################################################################
def get_deduction_suggestions(data):
    """
    Returns a list of deduction suggestions based on each deduction type.
    """
    suggestions = []
    if data["section_80c"] < 150000:
        suggestions.append(
            "Increase your investments in tax-saving instruments (PPF, ELSS, life insurance) under Section 80C to reach the ₹1.5L limit."
        )
    if data["section_80d"] < 25000:
        suggestions.append(
            "Review your health insurance policy and consider increasing premiums to fully utilize Section 80D (up to ₹25,000)."
        )
    if data["section_80e"] == 0:
        suggestions.append(
            "If you have an education loan, claim the interest deduction under Section 80E to lower your taxable income."
        )
    if data["section_80g"] == 0:
        suggestions.append(
            "Consider donating to eligible charities to benefit from a deduction under Section 80G."
        )
    if not suggestions:
        suggestions.append(
            "Primary deductions are maximized. Explore additional tax-saving avenues like the National Pension System (Section 80CCD(1B)) or tax-saving bonds."
        )
    return suggestions

###############################################################################
# 9. PDF Form Filling
###############################################################################
def fill_pdf_form(input_pdf, output_pdf, data_dict):
    """
    Fills the given fillable PDF form (input_pdf) with values from data_dict
    and writes out to output_pdf. Field names in data_dict must match the PDF's internal field names exactly.
    """
    template_pdf = PdfReader(input_pdf)
    
    for page in template_pdf.pages:
        annotations = page.Annots
        if annotations:
            for annotation in annotations:
                if annotation.Subtype == "/Widget":
                    field_key = annotation.T
                    if field_key:
                        field_name = field_key[1:-1]
                        if field_name in data_dict:
                            annotation.V = str(data_dict[field_name])
                            if "/AP" in annotation:
                                del annotation["/AP"]
    
    PdfWriter().write(output_pdf, template_pdf)

###############################################################################
# 10. Main Tax Workflow
###############################################################################
def main_workflow(image_path):
    # Step 1: Extract text from the image
    text = extract_text(image_path)
    # (Optional) Debug: print(text)
    
    # Step 2: Parse data from OCR text
    data = parse_data(text)
    
    # Step 3: Compute taxable income components
    taxable_salary = max(data["salary_income"] - data["standard_deduction"], 0)
    business_income = data["business_income"]
    taxable_rental_income = max(data["rental_income"] - data["home_loan_interest"], 0)
    
    total_taxable_income = (
        taxable_salary +
        business_income +
        data["interest_income"] +
        taxable_rental_income +
        data["short_term_gains"] +
        data["long_term_gains"]
    )
    
    # Step 4: Compute total deductions
    allowed_80c = min(data["section_80c"], 150000)
    allowed_80d = min(data["section_80d"], 25000)
    allowed_80e = data["section_80e"]
    allowed_80g = data["section_80g"]
    total_deductions = allowed_80c + allowed_80d + allowed_80e + allowed_80g
    
    # Step 5: Net taxable income
    net_taxable_income = total_taxable_income - total_deductions
    if net_taxable_income < 0:
        net_taxable_income = 0
    
    # Step 6: Calculate tax liabilities
    tax_old = calculate_tax_old_regime(net_taxable_income)
    tax_new = calculate_tax_new_regime(net_taxable_income)
    
    # Step 7: Deduction suggestions
    suggestions = get_deduction_suggestions(data)
    
    # Compile results, formatting numeric values in Indian style:
    result = {
        "PAN": data["pan"],
        "Aadhaar": data["aadhaar"],
        "Taxable Salary": format_indian(taxable_salary),
        "Business Income": format_indian(business_income),
        "Interest Income": format_indian(data["interest_income"]),
        "Taxable Rental Income": format_indian(taxable_rental_income),
        "Short-Term Capital Gains": format_indian(data["short_term_gains"]),
        "Long-Term Capital Gains": format_indian(data["long_term_gains"]),
        "Non-Taxable Income": format_indian(data["non_taxable_income"]),
        "Total Income (Before Deductions)": format_indian(total_taxable_income),
        "Total Deductions": format_indian(total_deductions),
        "Net Taxable Income": format_indian(net_taxable_income),
        "Tax Liability (Old Regime)": format_indian(tax_old),
        "Tax Liability (New Regime)": format_indian(tax_new),
        "Suggestions": suggestions
    }
    return result

###############################################################################
# 11. Example Usage
###############################################################################
if __name__ == "__main__":
    # Run tax workflow from image
    image_path = r"C:\Users\hp\OneDrive\Documents\GitHub\Ai-Tax\tax.png"
    tax_details = main_workflow(image_path)
    
    print("=== TAX CALCULATION RESULTS ===")
    for key, value in tax_details.items():
        print(f"{key}: {value}")
    
    # Map extracted data to PDF form fields (adjust keys to match your PDF)
    pdf_data_map = {
        "NameField": "John Doe",  # Replace with actual name if available
        "PANField": tax_details["PAN"] if tax_details["PAN"] else "",
        "AadhaarField": tax_details["Aadhaar"] if tax_details["Aadhaar"] else "",
        "TaxableSalaryField": tax_details["Taxable Salary"],
        "BusinessIncomeField": tax_details["Business Income"],
        "RentalIncomeField": tax_details["Taxable Rental Income"],
        "CapitalGainsField": str(
            float(tax_details["Short-Term Capital Gains"].replace(',', '')) +
            float(tax_details["Long-Term Capital Gains"].replace(',', ''))
        ),
        "TotalDeductionsField": tax_details["Total Deductions"],
        "TaxOldRegimeField": tax_details["Tax Liability (Old Regime)"],
        "TaxNewRegimeField": tax_details["Tax Liability (New Regime)"],
        # ... add additional mappings as needed ...
    }
    
    # Fill the PDF form
    input_pdf = r"C:\Users\hp\Downloads\itr2_1_b170f8ce37.pdf"  # Absolute path to your fillable PDF
    output_pdf = "ITR2_filled.pdf"
    fill_pdf_form(input_pdf, output_pdf, pdf_data_map)
    print(f"Created {output_pdf} with pre-filled data.")

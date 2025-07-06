import pdfplumber

def extract_data_from_pdf(pdf_file, start_page, end_page):
    fund_names = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Validate page range
            num_pages = len(pdf.pages)
            start = max(0, start_page - 1)
            end = min(end_page, num_pages)

            for page_num in range(start, end):
                page = pdf.pages[page_num]
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line = line.strip()
                    if is_probable_fund_name(line):
                        fund_names.append(line)

        return fund_names

    except Exception

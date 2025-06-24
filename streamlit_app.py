import streamlit as st
import os
import re
import pandas as pd
import google.generativeai as genai
from unstract.llmwhisperer import LLMWhispererClientV2
import tempfile
import io
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Certificate of Origin PDF Extractor",
    page_icon="📄",
    layout="wide"
)

def clean_extracted_value(value):
    """Clean and normalize extracted values"""
    if not value or value.strip().lower() in ['n/a', 'na', 'not found', 'none', '']:
        return "N/A"
    
    # Remove extra whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', value.strip())
    
    # Remove common prefixes that might get extracted
    cleaned = re.sub(r'^[:\-\s]+', '', cleaned)
    
    return cleaned

def are_names_similar(name1, name2):
    """Check if two company names are similar (same entity)"""
    if not name1 or not name2 or name1 == "N/A" or name2 == "N/A":
        return False
    
    # Clean and normalize names for comparison
    clean_name1 = re.sub(r'[^\w\s]', '', name1.lower()).strip()
    clean_name2 = re.sub(r'[^\w\s]', '', name2.lower()).strip()
    
    # Remove common company suffixes for better comparison
    suffixes = ['ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation', 'pvt', 'private', 'llc', 'co']
    for suffix in suffixes:
        clean_name1 = re.sub(rf'\b{suffix}\b', '', clean_name1).strip()
        clean_name2 = re.sub(rf'\b{suffix}\b', '', clean_name2).strip()
    
    # Check if names are similar (exact match or one contains the other significantly)
    if clean_name1 == clean_name2:
        return True
    
    # Check if one is a significant substring of the other (at least 70% of the shorter name)
    shorter_len = min(len(clean_name1), len(clean_name2))
    if shorter_len > 0:
        if clean_name1 in clean_name2 or clean_name2 in clean_name1:
            overlap = len(clean_name1) if clean_name1 in clean_name2 else len(clean_name2)
            if overlap / shorter_len >= 0.7:
                return True
    
    return False

def extract_electronic_copy_info(uploaded_file, gemini_key, llm_whisperer_key):
    """
    Extract specific information from Certificate of Origin PDF
    """
    
    try:
        # Configure Gemini API
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Initialize LLM Whisperer client
        llm_whisperer_client = LLMWhispererClientV2(
            base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2",
            api_key=llm_whisperer_key
        )

        # Create temporary file from uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Step 1: Extract text from the input PDF (first page only for cost efficiency)
        result = llm_whisperer_client.whisper(
            file_path=tmp_file_path,
            wait_for_completion=True,
            wait_timeout=200,
            mode="native_text",
            mark_vertical_lines=True,
            mark_horizontal_lines=True,
            pages_to_extract="1"
        )

        doc = result['extraction']['result_text']
        
        # Clean up the text to remove any ELECTRONIC COPY marker if present
        first_page = doc.replace('(ELECTRONIC COPY)', '').strip()
        
        # Step 2: Create extraction prompt for specific fields
        extraction_prompt = f'''
        You are analyzing a "Certificate of Origin" document (ASEAN-INDIA FREE TRADE AREA PREFERENTIAL TARIFF). 
        Extract the following specific information from this text. Be very precise and extract only the actual values.

        Document Text:
        {first_page}

        Please extract these fields and return them in this exact format (use "N/A" if field is not found):

        Exporter's business name: [Extract the company name from section 1]
        Exporter's address: [Extract the full address from section 1, including plot/village/taluka/state/pincode]
        Exporter's country: [Extract the country from section 1]
        Producer's business name: [Extract the company name from section 2 if it exists]
        Producer's address: [Extract the full address from section 2 if it exists]
        Producer's country: [Extract the country from section 2 if it exists]
        Consignee's name: [Extract the company name from the consignee/importer section]
        Consignee's address: [Extract the full address from the consignee/importer section]
        Consignee's country: [Extract the country from the consignee/importer section]
        Marks and numbers on packaging: [Extract from column 6 in the table]
        Number and type of packages: [Extract package details from column 7]
        Description of goods: [Extract goods description from column 7, including HS code]
        Gross weight or other quantity: [Extract weight/quantity from column 9]
        Value (FOB): [Extract FOB value from column 9]

        Instructions:
        - Extract only the actual values, not labels or descriptions
        - For addresses, include the complete address as one field
        - For goods description, include the full description with HS code
        - Be precise and do not add extra text
        - If there are only 2 sections (Exporter and Consignee), mark Producer fields as "N/A"
        '''

        # Step 3: Get extraction using Gemini
        response = model.generate_content(extraction_prompt)
        extracted_text = response.text

        # Step 4: Parse the response into a dictionary
        extracted_data = {}
        field_mapping = {
            "Exporter's business name": "exporters_business_name",
            "Exporter's address": "exporters_address", 
            "Exporter's country": "exporters_country",
            "Producer's business name": "producers_business_name",
            "Producer's address": "producers_address",
            "Producer's country": "producers_country",
            "Consignee's name": "consignees_name",
            "Consignee's address": "consignees_address",
            "Consignee's country": "consignees_country",
            "Marks and numbers on packaging": "marks_numbers_packaging",
            "Number and type of packages": "number_type_packages",
            "Description of goods": "description_goods",
            "Gross weight or other quantity": "gross_weight_quantity",
            "Value (FOB)": "value_fob"
        }

        # Parse extracted text
        for line in extracted_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = clean_extracted_value(value)
                if key in field_mapping:
                    extracted_data[field_mapping[key]] = value

        # Step 5: Handle the logic for Producer vs Consignee
        exporter_name = extracted_data.get('exporters_business_name', 'N/A')
        producer_name = extracted_data.get('producers_business_name', 'N/A')
        
        # If producer name is similar to exporter name, use the third section (original consignee) as final consignee
        if producer_name != 'N/A' and are_names_similar(exporter_name, producer_name):
            # Keep the original consignee data as is (it's already from section 3)
            pass
        elif producer_name != 'N/A' and not are_names_similar(exporter_name, producer_name):
            # If producer is different from exporter, producer becomes consignee
            extracted_data['consignees_name'] = producer_name
            extracted_data['consignees_address'] = extracted_data.get('producers_address', 'N/A')
            extracted_data['consignees_country'] = extracted_data.get('producers_country', 'N/A')

        # Remove producer fields from final output as they're not needed in the Excel
        extracted_data.pop('producers_business_name', None)
        extracted_data.pop('producers_address', None)
        extracted_data.pop('producers_country', None)

        # Clean up temporary file
        os.unlink(tmp_file_path)

        return extracted_data
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise e

def create_excel_download(extracted_data_list):
    """Create Excel file for download"""
    excel_headers = [
        "filename", "exporters_business_name", "exporters_address", "exporters_country",
        "consignees_name", "consignees_address", "consignees_country", 
        "marks_numbers_packaging", "number_type_packages", "description_goods",
        "gross_weight_quantity", "value_fob"
    ]
    
    # Prepare data for DataFrame
    df_data = []
    for extracted_data in extracted_data_list:
        row_data = {}
        for header in excel_headers:
            if header == "filename":
                row_data[header] = extracted_data.get("filename", "N/A")
            else:
                row_data[header] = extracted_data.get(header, "N/A")
        df_data.append(row_data)
    
    # Create DataFrame
    df = pd.DataFrame(df_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Extracted_Data')
    
    return output.getvalue()

# Main Streamlit App
def main():
    st.title("📄 Certificate of Origin PDF Data Extractor")
    st.markdown("Upload Certificate of Origin PDFs and extract structured data automatically")
    
    # Sidebar for API credentials
    st.sidebar.header("🔑 API Configuration")
    st.sidebar.markdown("Enter your API credentials to use the extraction service")
    
    gemini_key = st.sidebar.text_input(
        "Gemini API Key", 
        type="password", 
        help="Your Google Gemini API key for text processing"
    )
    
    llm_whisperer_key = st.sidebar.text_input(
        "LLM Whisperer API Key", 
        type="password", 
        help="Your LLM Whisperer API key for PDF text extraction"
    )
    
    # Instructions
    with st.expander("📋 Instructions", expanded=False):
        st.markdown("""
        **How to use:**
        1. Enter your API credentials in the sidebar
        2. Upload one or more Certificate of Origin PDF files
        3. Click 'Extract Data' to process the files
        4. View the extracted data and download as Excel
        
        **API Keys needed:**
        - **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
        - **LLM Whisperer API Key**: Get from [Unstract](https://unstract.com)
        
        **Supported document type:**
        - Certificate of Origin (ASEAN-INDIA FREE TRADE AREA PREFERENTIAL TARIFF)
        
        **Document Structure Handling:**
        - Handles both 2-section and 3-section documents
        - If Exporter and Producer are the same company, uses the third section as Consignee
        - If Producer is different from Exporter, Producer becomes the Consignee
        """)
    
    # File upload section
    st.header("📤 Upload PDF Files")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="Upload one or more Certificate of Origin PDF files"
    )
    
    if uploaded_files and gemini_key and llm_whisperer_key:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        
        # Process files button
        if st.button("🚀 Extract Data", type="primary"):
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            extracted_data_list = []
            successful_extractions = 0
            failed_extractions = 0
            
            # Process each file
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing: {uploaded_file.name}")
                progress_bar.progress((i) / len(uploaded_files))
                
                try:
                    extracted_data = extract_electronic_copy_info(
                        uploaded_file, gemini_key, llm_whisperer_key
                    )
                    extracted_data['filename'] = uploaded_file.name
                    extracted_data_list.append(extracted_data)
                    successful_extractions += 1
                    
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    failed_extractions += 1
            
            # Complete progress
            progress_bar.progress(1.0)
            status_text.text("Processing complete!")
            
            # Display results summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Files", len(uploaded_files))
            with col2:
                st.metric("Successful", successful_extractions)
            with col3:
                st.metric("Failed", failed_extractions)
            
            if extracted_data_list:
                st.header("📊 Extracted Data")
                
                # Display data in tabs
                tab1, tab2 = st.tabs(["📋 View Data", "📥 Download"])
                
                with tab1:
                    for i, data in enumerate(extracted_data_list):
                        with st.expander(f"📄 {data['filename']}", expanded=i==0):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("Exporter Information")
                                st.write(f"**Business Name:** {data.get('exporters_business_name', 'N/A')}")
                                st.write(f"**Address:** {data.get('exporters_address', 'N/A')}")
                                st.write(f"**Country:** {data.get('exporters_country', 'N/A')}")
                                
                                st.subheader("Package Information")
                                st.write(f"**Marks & Numbers:** {data.get('marks_numbers_packaging', 'N/A')}")
                                st.write(f"**Package Type:** {data.get('number_type_packages', 'N/A')}")
                            
                            with col2:
                                st.subheader("Consignee Information")
                                st.write(f"**Name:** {data.get('consignees_name', 'N/A')}")
                                st.write(f"**Address:** {data.get('consignees_address', 'N/A')}")
                                st.write(f"**Country:** {data.get('consignees_country', 'N/A')}")
                                
                                st.subheader("Goods Information")
                                st.write(f"**Description:** {data.get('description_goods', 'N/A')}")
                                st.write(f"**Gross Weight:** {data.get('gross_weight_quantity', 'N/A')}")
                                st.write(f"**FOB Value:** {data.get('value_fob', 'N/A')}")
                
                with tab2:
                    st.subheader("📥 Download Results")
                    
                    # Create Excel file
                    excel_data = create_excel_download(extracted_data_list)
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"certificate_of_origin_data_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📊 Download Excel File",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
                    
                    st.success(f"✅ Ready to download {len(extracted_data_list)} records")
    
    elif uploaded_files and (not gemini_key or not llm_whisperer_key):
        st.warning("⚠️ Please enter both API keys in the sidebar to proceed with extraction.")
    
    elif not uploaded_files:
        st.info("👆 Please upload PDF files to begin extraction.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Note:** This tool processes Certificate of Origin documents for ASEAN-INDIA FREE TRADE AREA. Make sure your PDFs are clear and readable for best results.")

if __name__ == "__main__":
    main()

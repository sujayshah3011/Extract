# 📄 Certificate of Origin PDF Data Extractor

An intelligent web application that automatically extracts structured data from Certificate of Origin PDFs (ASEAN-INDIA FREE TRADE AREA PREFERENTIAL TARIFF) using AI-powered document processing.

## 🌐 Live Application

**Access the app here:** [https://uhuadt8zwvabjt8yud3j36.streamlit.app](https://uhuadt8zwvabjt8yud3j36.streamlit.app)

<img width="1434" height="844" alt="Screenshot 2025-08-05 at 10 14 49 PM" src="https://github.com/user-attachments/assets/08fd883f-21c5-4491-bb72-788f25ebd52f" />
<img width="1436" height="843" alt="Screenshot 2025-08-05 at 10 15 05 PM" src="https://github.com/user-attachments/assets/c6abd334-a866-450e-a88d-09683c0d3595" />

## ✨ Features

- **AI-Powered Extraction**: Uses Google Gemini and LLM Whisperer APIs for accurate data extraction
- **Batch Processing**: Upload and process multiple PDF files simultaneously
- **Structured Output**: Extracts 18+ specific fields from Certificate of Origin documents
- **Excel Export**: Download extracted data as formatted Excel files
- **Real-time Progress**: Track processing status with progress indicators
- **User-Friendly Interface**: Clean, intuitive Streamlit-based web interface

## 🚀 Getting Started

### Prerequisites

You'll need API keys from two services:

1. **Google Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an account and generate an API key
   - Used for intelligent text processing and data extraction

2. **LLM Whisperer API Key**
   - Visit [Unstract](https://unstract.com)
   - Sign up and obtain an API key
   - Used for PDF text extraction and processing

### Using the Application

1. **Access the App**: Go to [https://uhuadt8zwvabjt8yud3j36.streamlit.app](https://uhuadt8zwvabjt8yud3j36.streamlit.app)

2. **Configure API Keys**:
   - Enter your Gemini API key in the sidebar
   - Enter your LLM Whisperer API key in the sidebar

3. **Upload Documents**:
   - Click "Choose PDF files" to upload one or more Certificate of Origin PDFs
   - Supported format: PDF files only

4. **Extract Data**:
   - Click "🚀 Extract Data" to start processing
   - Monitor progress with the real-time progress bar

5. **View Results**:
   - Review extracted data in the structured view
   - Download results as an Excel file

## 📁 Supported Documents

This application is specifically designed for:
- **Certificate of Origin** documents
- **ASEAN-INDIA FREE TRADE AREA PREFERENTIAL TARIFF** format
- Clear, readable PDF documents (first page processing for efficiency)

## 💡 Technical Stack

- **Frontend**: Streamlit
- **AI Processing**: Google Gemini 1.5 Flash
- **PDF Processing**: LLM Whisperer API
- **Data Handling**: Pandas
- **File Processing**: OpenPyXL for Excel generation

## 🔧 Local Development

If you want to run this application locally:

```bash
# Clone the repository
git clone <repository-url>
cd certificate-origin-extractor

# Install dependencies
pip install streamlit pandas google-generativeai unstract-llmwhisperer openpyxl

# Run the application
streamlit run app.py
```

### Required Dependencies
```
streamlit
pandas
google-generativeai
unstract-llmwhisperer
openpyxl
```

## 📊 Output Format

The application generates Excel files with the following columns:
- exporters_business_name
- exporters_address
- exporters_country
- consignees_name
- consignees_address
- consignees_country
- departure_date
- vessel_aircraft
- port_of_discharge
- marks_numbers_packaging
- number_type_packages
- description_goods
- origin_criterion
- gross_weight_quantity
- value_fob
- invoice_number_date
- exporting_country
- importing_country

## ⚠️ Important Notes

- **API Costs**: Both Gemini and LLM Whisperer APIs may have usage costs
- **Processing Time**: Large files or multiple documents may take several minutes to process
- **Document Quality**: Clear, well-scanned PDFs produce better extraction results
- **First Page Only**: For cost efficiency, only the first page of each PDF is processed
- **Data Privacy**: Documents are processed through third-party APIs

## 🔒 Security & Privacy

- API keys are entered locally and not stored
- Documents are temporarily processed and then deleted
- No data is permanently stored on servers
- Use secure API key management practices

## 🐛 Troubleshooting

### Common Issues:

1. **"API Key Error"**: Ensure your API keys are valid and have sufficient credits
2. **"Processing Failed"**: Check if your PDF is readable and in the correct format
3. **"Extraction Incomplete"**: Some fields may show "N/A" if not found in the document
4. **"Slow Processing"**: Large files or multiple documents may take time

### Tips for Better Results:
- Use high-quality, clear PDF scans
- Ensure the document follows standard Certificate of Origin format
- Check that all text is clearly visible and not corrupted

## 📞 Support

For technical issues or questions about the application, please check the troubleshooting section above or review the document format requirements.

## 📄 License

This project is provided as-is for document processing purposes. Please ensure compliance with your organization's data handling policies when using third-party APIs.

---

**Built with ❤️ using Streamlit and AI**

# Scheme Rules & Farmer Document Management (DOCUMENT_MANAGEMENT)

## 1. Dual Scope of Document Management in Krishi Mitra
In Krishi Mitra, "Document Management" covers two critical domains:
1. **Farmer KYC & Land Document Guidance**: Explaining what official physical/digital documents a farmer in Karnataka needs for each scheme, what they are called in colloquial Kannada, and where to obtain them.
2. **Auditable Scheme Rule Document Versioning**: How scheme rules, crop notifications, and eligibility thresholds are maintained as structured, version-controlled JSON documents (`data/schemes/schemes_catalog.json`).

---

## 2. Canonical Karnataka Farmer Documents Dictionary (`documents_master.json`)

Farmers often do not recognize bureaucratic English terms like "Record of Rights, Tenancy and Crops". Krishi Mitra always maps official documents to the familiar local terms used in Karnataka villages:

| Document ID | Official Name | Spoken Kannada Name (Used by Agent) | Purpose | Where Farmer Gets It |
| :--- | :--- | :--- | :--- | :--- |
| `DOC_RTC_PAHANI` | Record of Rights, Tenancy and Crops (RTC) | **ಪಹಣಿ ಪತ್ರ / ಉತಾರ (Pahani / Utara / RTC)** | Proves land ownership, survey number, extent in *Ekare/Gunte*, and current crop grown. | *Nadakacheri*, *Bhoomi Online*, or *Grama One* center. |
| `DOC_FRUITS_ID` | Farmer Registration & Unified Beneficiary Information System ID | **ಫ್ರೂಟ್ಸ್ ಐಡಿ (FRUITS ID / FID ನಂಬರ್)** | Mandatory unified farmer registration number in Karnataka for receiving state/central agricultural subsidies and DBT. | Local *Raitha Samparka Kendra* (RSK) or `fruits.karnataka.gov.in`. |
| `DOC_AADHAAR_NPCI` | Aadhaar Card with NPCI/DBT Seeded Bank Account | **ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಆಧಾರ್ ಲಿಂಕ್ ಆಗಿರುವ ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್** | Required for Direct Benefit Transfer (DBT) of PM-KISAN installments and equipment/irrigation subsidies. | Bank branch or India Post Payments Bank (IPPB). |
| `DOC_SOWING_CERT` | Crop Sowing Certificate / Self-Declaration | **ಬೆಳೆ ಬಿತ್ತನೆ ದೃಢೀಕರಣ ಪತ್ರ** | Required for PMFBY crop insurance if the crop is not yet updated in the current season's *Pahani*. | Village Accountant (*Shanbhog / Grama Lekhaka*). |
| `DOC_TENANT_AGREEMENT` | Land Lease / Cultivator Certificate | **ಗುತ್ತಿಗೆ ಕರಾರು ಪತ್ರ / ಸಾಗುವಳಿ ದೃಢೀಕರಣ** | Used for schemes allowing tenant/sharecropper participation (such as Demo Soil Improvement or notified tenant crop insurance). | Local Panchayat / Landowner agreement. |
| `DOC_QUOTATION_BOREWELL` | Approved Vendor Quotation & Water Source Proof | **ಡ್ರಿಪ್ ಕಂಪನಿಯ ಕೊಟೇಶನ್ ಮತ್ತು ನೀರಿನ ಮೂಲದ ದಾಖಲೆ** | Used in `Demo Micro-Irrigation Support` and `Demo Agricultural Equipment Assistance`. | Empaneled irrigation/equipment dealer & RSK. |

---

## 3. Scheme-to-Document Matrix

| Scheme ID | Required Documents Explained in Spoken Kannada |
| :--- | :--- |
| `PM_KISAN` | 1. ಪಹಣಿ ಪತ್ರ (RTC / Utara)<br>2. ಆಧಾರ್ ಕಾರ್ಡ್ (e-KYC ಆಗಿರಬೇಕು)<br>3. ಆಧಾರ್ ಜೋಡಣೆಯಾದ ಬ್ಯಾಂಕ್ ಖಾತೆ ಪಾಸ್‌ಬುಕ್<br>4. ಫ್ರೂಟ್ಸ್ ಐಡಿ (FRUITS ID) |
| `PMFBY` | 1. ಪಹಣಿ ಪತ್ರ (RTC)<br>2. ಬೆಳೆ ಬಿತ್ತನೆ ದೃಢೀಕರಣ ಪತ್ರ<br>3. ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್<br>4. ಫ್ರೂಟ್ಸ್ ಐಡಿ (FRUITS ID) |
| `DEMO_MICRO_IRRIGATION` | 1. ಪಹಣಿ ಪತ್ರ (RTC) ಮತ್ತು ಚಕ್ಕುಬಂದಿ ನಕ್ಷೆ<br>2. ನೀರಿನ ಮೂಲದ ದೃಢೀಕರಣ (ಬೋರ್‌ವೆಲ್/ಬಾವಿ)<br>3. ಆಧಾರ್, ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ ಮತ್ತು ಫ್ರೂಟ್ಸ್ ಐಡಿ |
| `DEMO_AGRI_EQUIPMENT` | 1. ಪಹಣಿ ಪತ್ರ (RTC)<br>2. ಫ್ರೂಟ್ಸ್ ಐಡಿ (FRUITS ID)<br>3. ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್<br>4. ಅಧಿಕೃತ ಡೀಲರ್ ಕೊಟೇಶನ್ |
| `DEMO_SOIL_IMPROVEMENT` | 1. ಫ್ರೂಟ್ಸ್ ಐಡಿ (FRUITS ID) ಅಥವಾ ಆಧಾರ್ ಕಾರ್ಡ್<br>2. ಪಹಣಿ ಪತ್ರ ಅಥವಾ ಸಾಗುವಳಿ ವಿವರ<br>3. ಮಣ್ಣು ಪರೀಕ್ಷಾ ವರದಿ (ಲಭ್ಯವಿದ್ದರೆ) |
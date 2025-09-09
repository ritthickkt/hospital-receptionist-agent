# Hospital Receptionist Agent

This project is a voice-enabled agent for hospital reception tasks, built using LiveKit and Google Sheets API.

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/ritthickkt/hospital-receptionist-agent.git
cd hospital-receptionist-agent
```

### 2. Create a `.env.local` File
Create a `.env.local` file in the project root to store all your API keys and configuration secrets. **Do not commit this file to version control.**

Example `.env.local`:
```
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SHEETS_ID=your_google_sheet_id
GOOGLE_SHEETS_RANGE=your_range_name
OTHER_API_KEY=your_other_api_key
```

- `GOOGLE_API_KEY`: Your Google API key for accessing Google Sheets.
- `GOOGLE_SHEETS_ID`: The ID of your Google Sheet.
- `GOOGLE_SHEETS_RANGE`: The range name (e.g., `Sheet1!A1:D10`).
- Add any other required API keys.

### 3. Configure an MCP Server for Google Sheets API
You must configure a Model Context Protocol (MCP) server to interface with the Google Sheets API. This server will handle authentication and requests to Google Sheets.

- Refer to the MCP server documentation for setup instructions.
- Ensure your `.env.local` contains the correct sheet ID and range name for your use case.

### 4. Install Dependencies
```sh
pip install -r requirements.txt
```
Or, if using `uv`:
```sh
uv pip install -r requirements.txt
```

### 5. Run the Agent
```sh
uv run hospital_agent.py console
```

## Notes
- Do not commit sensitive files like `.env.local`, `credentials.json`, or `token.json`.
- For more details, see the comments in the code and the MCP server documentation.

---

Feel free to open issues or pull requests for improvements!

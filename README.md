# SAT Progress Report Generator

An intelligent SAT exam preparation assistant that analyzes student performance data and generates personalized progress reports with actionable recommendations.

## Overview

This system fetches student performance data, analyzes their progress across Mathematics, Writing, and Reading sections, and generates comprehensive reports with visual heatmaps. It uses AI-powered analysis to provide personalized recommendations based on exam context and individual student progress.

## Features

- **Automated Data Processing**: Fetches and processes student performance data from external APIs
- **AI-Powered Analysis**: Uses Google's Gemini AI to generate personalized recommendations
- **Visual Progress Tracking**: Generates heatmaps for each subject showing progress by difficulty level
- **Comparative Analysis**: Tracks improvement by comparing current vs previous attempts
- **Priority-Based Recommendations**: Focuses on high-weightage topics and exam priorities
- **Structured JSON Reports**: Outputs detailed, nested JSON reports with section, domain, and topic-level insights

## Tech Stack

- **Backend**: FastAPI
- **AI Model**: Google Gemini 2.5 Flash Lite
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Validation**: Pydantic

## Project Structure

```
├── app.py                    # FastAPI application and main endpoint
├── data_processing.py        # Data fetching and processing logic
├── generate_heatmaps.py      # Heatmap generation utilities
├── sat_agent.py             # AI agent and prompt engineering
├── Data/
│   ├── exam_context/
│   │   └── details.md       # SAT exam structure and weightage
│   ├── logs/
│   │   └── logger.log       # Application logs
│   └── saved_progress_report/
│       └── {user}-{class}/  # User-specific reports and heatmaps
└── .env                     # Environment variables
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Alifseen/student_progress_AI_analyzer/
cd sat-progress-report
```

2. Install dependencies:
```bash
pip install fastapi uvicorn requests pandas seaborn matplotlib google-generativeai pydantic python-dotenv
```

3. Set up environment variables in `.env`:
```env
API_AUTH=your_api_authorization_token
GEMINI_API=your_gemini_api_key
```

4. Add SAT exam details in `Data/exam_context/details.md`

## Usage

### Start the Server

```bash
uvicorn app:app --reload
```

### Generate a Report

Make a GET request to:
```
http://localhost:8000/generate_report?user={USER_ID}&course={COURSE_ID}
```

### API Documentation

Access the interactive API docs at:
```
http://localhost:8000/documentation
```

## API Response Structure

```json
{
  "report_json": {
    "summary_overview": "...",
    "sections": {
      "mathematics": { "..." },
      "writing": { "..." },
      "reading": { "..." }
    },
    "priority_roadmap": "...",
    "next_steps": "..."
  },
  "heatmaps": {
    "math": "/images/math_heatmap.png",
    "writing": "/images/writing_heatmap.png",
    "reading": "/images/reading_heatmap.png"
  },
  "meta_data": {
    "data_analyzed": ["..."],
    "id": "response_id",
    "token_usage": { "..." }
  }
}
```

## Key Features

### Smart Priority System

### Difficulty-Based Analysis
- Tracks completion and average scores across Easy, Medium, and Hard levels
- Recommends progression based on mastery

### Comparative Tracking
- Stores previous progress data
- Generates improvement-focused recommendations
- Tracks time spent, questions attempted, and accuracy trends

## Logging
All operations are logged with timestamps to `Data/logs/logger.log` for debugging and monitoring.

## Error Handling
The application includes comprehensive error handling with detailed logging at each processing stage, including:
- Data fetching failures
- AI response parsing issues (with automatic retry)
- File I/O operations
- Heatmap generation errors

## Contributing
Contributions are welcome! Please ensure all code follows the existing structure and includes appropriate error handling and logging.

## License
Not for commercial usa.

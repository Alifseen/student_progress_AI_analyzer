from data_processing import *
from generate_heatmaps import *
from sat_agent import *
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import logging

app = FastAPI()

load_dotenv()

logging.basicConfig(
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('Data/logs/logger.log')
    ],
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)



@app.get('/generate_report')
def get_report(user: str, course: str):

    # Get User and Class ID
    if not user:
        logger.error('[FAIL] user_id not provided')
        raise HTTPException(status_code=400, detail="user_id not provided")

    if not course:
        logger.error('[FAIL] class_id not provided')
        raise HTTPException(status_code=400, detail="course_id not provided")

    user_id = user
    class_id = course
    logger.info(f"[OK] Starting Report Generation Process for user: {user_id}, Class: {class_id}")

    # Initiate Data Processing
    try:
        student_data = FetchStudentData(user_id, class_id)
        logger.info(f"[OK] Instantiate Data Class for user={user_id}, class={class_id}")
    except Exception as e:
        logger.exception(f"[FAIL] Instantiate Data Class for user={user_id}, class={class_id}")
        raise

    # Acquire Data
    try:
        performance_data = data_segregation(student_data.master_loop())
        logger.info(f"[OK] Acquire performance data for user={user_id}, class={class_id}")
    except Exception as e:
        logger.exception(f"[FAIL] Acquire performance data for user={user_id}, class={class_id}")
        raise

    # Get SAT Exam Details
    try:
        context = get_context()
        logger.info(f"[OK] Get context for SAT Exam")
    except Exception as e:
        logger.exception(f"[FAIL] Get context for SAT Exam")
        raise

    # Segregate Student Progress
    overall_progress = performance_data['overall_progress']
    mathematics = performance_data['Mathematics']
    writing = performance_data['Writing']
    reading = performance_data['Reading']

    # Check previous attempt
    try:
        attempt = check_attempt(user_id, class_id)
        logger.info(f"[OK] Find previous attempt data for user={user_id}, class={class_id}")
    except Exception as e:
        logger.exception(f"[FAIL] Find previous attempt data for user={user_id}, class={class_id}")
        raise

    # Generate Prompts
    try:
        user, system = generate_prompts(overall_progress, mathematics, writing, reading, context, attempt, user_id, class_id)
        logger.info(f"[OK] Generate prompt if attempt status is {attempt}")
    except Exception as e:
        logger.exception(f"[FAIL] Generate prompt if attempt status is {attempt}")
        raise

    # Get response from Agent
    try:
        key = os.getenv('GEMINI_API')

        response = agent(user, system, 'gemini-2.5-flash-lite', key, 1024, 0.2, 16000)
        logger.info(f"[OK] Call Agent for user={user_id}, class={class_id}")

        # Sort out the response
        response_id = response.response_id
        token_usage = response.usage_metadata
        report = response.parsed
        if report == None:
            logger.error("[FAIL] LLM Response is not parsed. Retry in progress.")
            count = 0
            max_retry = 3
            while report == None and count < max_retry:
                response = agent(user, system, 'gemini-2.5-flash-lite', key, 1024, 0.2, 16000)
                report = response.parsed
                count += 1

        if report != None:
            logger.info(f"[OK] Response Parsed: {report}")

        else:
            logger.error(f"[FAIL] Max retries reach, no parsed response received. {response}")
            return None
    except Exception as e:
        logger.exception(f"[FAIL] Call Agent for user={user_id}, class={class_id}")
        raise

    report_dict = create_dictionary(report)

    # Save Data in JSON files
    try:
        subjects_name_list, subjects_details_list = save_json(user_id, class_id, performance_data, report_dict)
        logger.info(f"[OK] Save data for user={user_id}, class={class_id}")
    except Exception as e:
        logger.exception(f"[FAIL] Save data for user={user_id}, class={class_id}")
        raise

    # Generate Subject Progress Heatmaps
    try:
        math_data_path = f"Data/saved_progress_report/{user_id}-{class_id}/previous/MATHEMATICS.json"
        math_heatmap_output_path = f'Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/math_heatmap.png'
        math_title = "SAT Math Progress Heatmap"
        math_fig_size = (8, 14)

        writing_data_path = f"Data/saved_progress_report/{user_id}-{class_id}/previous/WRITING.json"
        writing_heatmap_output_path = f'Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/writing_heatmap.png'
        writing_title = "SAT Writing Progress Heatmap"
        writing_fig_size = (8,8)

        reading_data_path = f"Data/saved_progress_report/{user_id}-{class_id}/previous/READING.json"
        reading_heatmap_output_path = f'Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/reading_heatmap.png'
        reading_title = "SAT Reading Progress Heatmap"
        reading_fig_size = (8,4)

        generate_heatmap(math_data_path, math_heatmap_output_path, math_title, math_fig_size) # Math
        generate_heatmap(writing_data_path, writing_heatmap_output_path, writing_title, writing_fig_size) # Writing
        generate_heatmap(reading_data_path, reading_heatmap_output_path, reading_title, reading_fig_size) # Reading

        app.mount("/images", StaticFiles(directory=f"Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/"),
                  name="heatmaps")
        logger.info(f"[OK] Generate Heatmaps for user={user_id}, class={class_id}")
    except Exception as e:
        logger.exception(f"[FAIL] Generate Heatmaps for user={user_id}, class={class_id}")
        raise

    logger.info(f"[OK] Report Generated for user={user_id}, class={class_id}")

    return {
        'report_json': report_dict,
        'heatmaps': {
            'math' : f"/images/{os.path.basename(math_heatmap_output_path)}",
            'writing' : f"/images/{os.path.basename(writing_heatmap_output_path)}",
            'reading' : f"/images/{os.path.basename(reading_heatmap_output_path)}",
        },
        'meta_data': {
            'data_analyzed': subjects_name_list,
            "id": response_id,
            'token_usage': token_usage
        }
    }


@app.get('/documentation')
def api_structure():

    return {
        'Endpoint' : 'url/generate_report?queries',
        'Required Queries' : '?user=(Enter User ID here)&course=(Enter course ID here)',
        'Example Payload': {
        'report_json': 'The Entire Report in Nest JSON',
        'heatmaps': {
            'Math Heatmap' : 'Download Link',
            'Writing Heatmap' : 'Download Link',
            'Reading Heatmap' : 'Download Link',
            },
        'meta_data': {
            'subject_names': 'A list of subjects analyzed in the report',
            "id": 'An ID to save the response by',
            'token_usage': 'Complete Tokens usage data, input, output, thinking and cache.'
            }
        },
        'Nested JSON Schema' : {
              "summary_overview": "string",
              "sections": {
                "mathematics": {
                  "overview": "string",
                  "section_recommendation": "string",
                  "subject_domains": {
                    "algebra": {
                      "domain_overview": "string",
                      "domain_topics": {
                        "absolute_values": {
                          "topic_current_status": "string",
                          "topic_recommendations": "string"
                        },
                        "...": {}
                      }
                    },
                    "...": {}
                  }
                },
                "writing": {
                  "overview": "string",
                  "section_recommendation": "string",
                  "subject_domains": {
                    "...": {}
                  }
                },
                "reading": {
                  "overview": "string",
                  "section_recommendation": "string",
                  "subject_domains": {
                    "...": {}
                  }
                }
              },
              "priority_roadmap": "string",
              "next_steps": "string"
        }
    }
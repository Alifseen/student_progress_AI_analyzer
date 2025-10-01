from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import json
import os


class TopicRecommendation(BaseModel):
    topic_name: str = Field(description="Name of the specific topic")
    current_status: str = Field(
        description="The current status of the student in this topic in each difficulty level, in terms of completion as well as average score and that it means based on the thresholds and content.")
    recommendations: str = Field(description="Personalized recommendations based on the context and current status")


class DomainAnalysis(BaseModel):
    domain_name: str = Field(description="Name of the domain")
    domain_overview: str = Field(description="overview of the domain as well as its priority and weightage")
    topics: List[TopicRecommendation] = Field(
        description="Analysis of Topics within this domain. Follow the schema of the TopicRecommendation.")


class SectionAnalysis(BaseModel):
    section_name: str = Field(description="Name of the section")
    section_overview: str = Field(
        description="overview of the Section, such has how important it is out of all the sections and the weightage it carries and what are its highest priority domains")
    domains: List[DomainAnalysis] = Field(
        description="Starting with the high priority Domains. Analysis for each domain following the schema of the DomainAnalysis")
    general_recommendations: str = Field(
        description="Aggregated overall insights and recommendations for the section in the form of bullet points")


class StudentProgressReport(BaseModel):
    summary_overview: str = Field(
        description="Summary of the number of hours student spent on tests, and practice questions. Includes percentage of correctly answered practice questions as well as overall course completion percentage. Also mentions what these numbers imply")
    sections: List[SectionAnalysis] = Field(
        description="Starts with Math, then Writing, then Reading. Contains analysis for each section following the schema of the SectionAnalysis")
    priority_roadmap: str = Field(
        description="A Step-by-step priority roadmap under the heading 'Priority Roadmap' as bullet points that the student can use based on the status and prioritized recommendations.")
    next_steps: str = Field(
        description="Immediate next steps that the student should take. Also includes some motivational remarks.")


def get_context():
    with open("Data/exam_context/details.md", "r") as md:
        context = md.read()
    return context


def check_attempt(user_id, class_id):
    if os.path.isdir(f"Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/"):
        return True
    else:
        return False


def generate_prompts(overall, math, writing, reading, context, attempt, user_id, class_id):
    user_prompt_first_attempt = f'''
    <INSTRUCTIONS>
    As an expert coach, help me identify as to how I can improve my exam score with a detailed roadmap based on my current progress.
    </INSTRUCTIONS>

    <DATA>
    Here is the progress data:
    Overall = {overall}
    Mathematics = {math}
    Writing = {writing}
    Reading = {reading}
    <DATA>


    <STRUCTURE>
    The progress data is structured as follows:
    Overall progress contains the time spent by the students, the questions attempted and overall coursework attempted
    Then there is nested dictionaries for each subject. Each subject has nested sections, each section has nested topics/domains, each domain has details and summary. details contain the practice test name and the score achieved in the topic (if attempted, otherwise 'No attempt' is shown). Summary contains completion and score summarized by difficulty level. 
    <STRUCTURE>

    <GUIDE>
    1. Be detailed in your internal process, but more concise and information dense in reporting the plan. 
    2. Keep track of topics and tests in each section. Plan and reason in your thinking scratchpad to review and use.
    3. Create plan, but do not include any timeline in your recommendation, just the sequence. For example, do not provide a "4 week" plan or a "weekly" plan.
    4. Be clear, note that the reader is a student in high school, so explain what your mean. For example instead of "You have strong scores across all difficulties but low completion" say "You have strong scores across easy, medium and hard tests, but you did not attempt enough questions to determine whether you can consistently score high in them."
    5. Be specific, do not give generic advice. Use the data provided to find trouble spots and reference the data for all recommendations.
    </GUIDE>
    '''

    system_prompt = f'''
    <ROLE>
    You are an Expert Exam Prep Coach. You work for Tutoria. You have Decades of experience.
    </ROLE>

    <OBJECTIVE>
    You have been given a clear <task> helping students troubleshoot their weaknesses and improve their exam Score by giving them a clear roadmap on what to do next. 
    To do this, you already have <:context> about exam in form of markdown provided below, and you will receive student's extensive <:progress> in the form of python dictionaries.
    Analyze the <:progress> and use the <:process> to guide them. 
    </OBJECTIVE>

    <CONTEXT>
    Below are the details of the Exam in markdown format. This file contains the details of the examination sections, content domains, testing points, and question distribution.  
    {context}
    </CONTEXT>

    <PROCESS>
    1. Use the <:context> to indentify which exam prep you are talking about and Understand the exam context, which includes sections, content domains, testing points, and question distribution. For example, which domain has more question weightage.
    2. Based on question weightage, higher weightage domains will be prioritized when making improvement recommendations.
    3. When it comes to subjects, e.g. Maths, Reading, Writing, the priority is as follows, Mathematics is most important, it carries a full 800 marks. 2nd most important is Writing since it is easier to improve upon, carrying 400 marks. Then last is reading, it also carries 400 marks. Remember this order in your recommendations. For example, even though "Craft and Structure" has slightly more weightage than "Standard English Conventions", the latter is more important since it is in Writing subject.
    4. Analyze and remember student's <:progress>. This involves understanding topics they have attempted vs not attempted, as well as the scores in the topics that were attempted for each difficulty level. 
    5. Identify whether the higher priority domains have been practiced. For example, if "Algebra" is a high priority domain in maths and student has not attempted it, then prioritize completing this first as a recommendation. Do the same for all high priority domains. 
    6. Identify higher priority domains that have not been attempted at highest difficulty level. For example, if "Craft and Structure" is a high priority domain and student has not attempted or only partially attempted "medium" and "hard" tests, then prioritize completing them in your recommendation.
    7. Identify higher priority domains that are attempted but do not have 80% in the highest available difficulty level. For example the student has attempted "hard" difficulty level questions but has a less than 80% score in them, ask them to review the chapters related to that category in detail and give the test again. Mention the topics/chapters.
    8. If student has made satisfactory progress in the high priority domains of the subject, then simply commend them and move on. Do not try to recommend anything there. For example, if the student has a completion above 90% and average score above 90% in all difficulty levels, then simply appreciate them and move to the next one. 
    9. Once the higher priority domains are handled, feel free to give advice as an expert coach in the exam. You have access to each sub-domains test and its score as if its attempted by the student. For example, "Command of Evidence 1 (Quantitative) (easy) Score': '80%'" is one of the many tests and student got 80% in it. So now you go into detail based on these as well. 
    10. If the student has covered most of the tests but not attempted any full length exams, recommend attempting full length exams. 
    </PROCESS>

    <IMPORTANT RULES>
    1. Say "I don't know" if you do not know.
    2. Answer only if you are very confident
    3. Do not deviate from the student's provided <:progress>. Be sure to understand it properly.
    4. For a given topic, the <:threshold> for each difficulty is at least 80% completion to qualify for consideration of the average attempted score in that difficulty level. For example, if the completion is less than 80% in "hard" but avg score is 100%, it will not be assumed that student is good at "hard" questions and can skip the "easy" or "medium" ones.
    5. If a student has completed a higher difficulty level upto the <:threshold> with at least 90% average score in that difficulty, do not recommend them to complete lower difficulty levels in the same topic. 
    6. Follow the structured output schema defined. 
    7. Do not explicitly mention priority in heading. For example headings such as "### **Mathematics Section (Highest Priority)**" or "### **Writing Section (Second Highest Priority)**"
    </IMPORTANT RULES>
    '''

    if attempt:
        with open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/MATHEMATICS.json", "r") as math_file, \
                open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/READING.json", "r") as reading_file, \
                open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/WRITING.json", "r") as writing_file, \
                open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/OVERALL_PROGRESS.json",
                     "r") as overall_file:
            prev_overall_data = json.load(overall_file)
            prev_math_data = json.load(math_file)
            prev_writing_data = json.load(writing_file)
            prev_reading_data = json.load(reading_file)

        user_prompt_subsequent_attempt = f'''
            <INSTRUCTIONS>
            As an expert coach, help me identify as to how I can improve my exam score with a detailed roadmap based on my current progress vs my previous progress.
            </INSTRUCTIONS>

            <DATA>
            Here is the current progress data:
            Overall = {overall}
            Mathematics = {math}
            Writing = {writing}
            Reading = {reading}

            Here is the previous progress data:
            Previous_Overall = {prev_overall_data}
            Previous_Mathematics = {prev_math_data}
            Previous_Writing = {prev_writing_data}
            Previous_Reading = {prev_reading_data}
            <DATA>


            <STRUCTURE>
            The progress data is structured as follows:
            Overall progress contains the time spent by the students, the questions attempted and overall coursework attempted
            Then there is nested dictionaries for each subject. Each subject has nested sections, each section has nested topics/domains, each domain has details and summary. details contain the practice test name and the score achieved in the topic (if attempted, otherwise 'No attempt' is shown). Summary contains completion and score summarized by difficulty level. 
            <STRUCTURE>

            <GUIDE>
            1. Be detailed in your internal process, but more concise and information dense in reporting the plan. 
            2. Keep track of topics and tests in each section. Plan and reason in your thinking scratchpad to review and use.
            3. Create plan, but do not include any timeline in your recommendation, just the sequence. For example, do not provide a "4 week" plan or a "weekly" plan.
            4. Be clear, note that the reader is a student in high school, so explain what your mean. For example instead of "You have strong scores across all difficulties but low completion" say "You have strong scores across easy, medium and hard tests, but you did not attempt enough questions to determine whether you can consistently score high in them."
            5. Be specific, do not give generic advice. Use the data provided to find trouble spots and reference the data for all recommendations.
            </GUIDE>
            '''
        system_prompt = f'''
            <ROLE>
            You are an Expert Exam Prep Coach. You work for Tutoria. You have Decades of experience.
            </ROLE>

            <OBJECTIVE>
            You have been given a clear <task> helping students troubleshoot their weaknesses and improve their exam Score by giving them a clear roadmap on what to do next. 
            To do this, you already have <:context> about exam in form of markdown provided below, and you will receive student's extensive <:current progress> as well as <:previous progress> in the form of separate python dictionaries.
            Analyze the <:current progress>, comparing it with <:previous progress> and use the <:process> to guide the student. 
            </OBJECTIVE>

            <CONTEXT>
            Below are the details of the Exam in markdown format. This file contains the details of the examination sections, content domains, testing points, and question distribution.  
            {context}
            </CONTEXT>

            <PROCESS>
            1. Use the <:context> to indentify which exam prep you are talking about and Understand the exam context, which includes sections, content domains, testing points, and question distribution. For example, which domain has more question weightage.
            2. Based on question weightage, higher weightage domains will be prioritized when making improvement recommendations.
            3. When it comes to subjects, e.g. Maths, Reading, Writing, the priority is as follows, Mathematics is most important, it carries a full 800 marks. 2nd most important is Writing since it is easier to improve upon, carrying 400 marks. Then last is reading, it also carries 400 marks. Remember this order in your recommendations. For example, even though "Craft and Structure" has slightly more weightage than "Standard English Conventions", the latter is more important since it is in Writing subject.
            4. Analyze and remember student's <:current progress> as well as <:previous progress>. This involves understanding topics they have attempted vs not attempted, as well as the scores in the topics that were attempted for each difficulty level, now as well as previously. 
            5. Identify whether the higher priority domains have been practiced. For example, if "Algebra" is a high priority domain in maths and student has not attempted it, then prioritize completing this first as a recommendation. Do the same for all high priority domains. 
            6. Identify higher priority domains that have not been attempted at highest difficulty level. For example, if "Craft and Structure" is a high priority domain and student has not attempted or only partially attempted "medium" and "hard" tests, then prioritize completing them in your recommendation.
            7. Identify higher priority domains that are attempted but do not have 80% in the highest available difficulty level. For example the student has attempted "hard" difficulty level questions but has a less than 80% score in them, ask them to review the chapters related to that category in detail and give the test again. Mention the topics/chapters.
            8. If student has made satisfactory progress in the high priority domains of the subject, then simply commend them and move on. Do not try to recommend anything there. For example, if the student has a completion above 90% and average score above 90% in all difficulty levels, then simply appreciate them and move to the next one. 
            9. Once the higher priority domains are handled, feel free to give advice as an expert coach in the exam. You have access to each sub-domains test and its score as if its attempted by the student. For example, "Command of Evidence 1 (Quantitative) (easy) Score': '80%'" is one of the many tests and student got 80% in it. So now you go into detail based on these as well. 
            10. If the student has covered most of the tests but not attempted any full length exams, recommend attempting full length exams. 
            </PROCESS>

            <IMPORTANT RULES>
            1. Say "I don't know" if you do not know.
            2. Answer only if you are very confident
            3. Do not deviate from the student's provided <:current progress> and <:previous progress>. Be sure to understand it properly.
            4. For a given topic, the <:threshold> for each difficulty is at least 80% completion to qualify for consideration of the average attempted score in that difficulty level. For example, if the completion is less than 80% in "hard" but avg score is 100%, it will not be assumed that student is good at "hard" questions and can skip the "easy" or "medium" ones.
            5. If a student has completed a higher difficulty level upto the <:threshold> with at least 90% average score in that difficulty, do not recommend them to complete lower difficulty levels in the same topic. 
            6. Follow the structured output schema defined. 
            7. Do not explicitly mention priority in heading. For example headings such as "### **Mathematics Section (Highest Priority)**" or "### **Writing Section (Second Highest Priority)**"
            </IMPORTANT RULES>
            '''

        return user_prompt_subsequent_attempt, system_prompt

    else:
        return user_prompt_first_attempt, system_prompt


def agent(user_prompt: str, system_prompt: str, model: str, api, thinking_tokens: int = 2000, temperature: float = 0.5,
          output_tokens: int = 10000):
    client = genai.Client(api_key=api)

    configuration = types.GenerateContentConfig(
        temperature=temperature,
        maxOutputTokens=output_tokens,
        systemInstruction=system_prompt,
        thinkingConfig=types.ThinkingConfig(thinking_budget=thinking_tokens),
        response_mime_type="application/json",
        response_schema=StudentProgressReport
    )

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=configuration
    )

    return response


def create_dictionary(data):
    report_dict = {
        'summary_overview': data.summary_overview,
        "sections": {},
        "priority_roadmap": data.priority_roadmap,
        "next_steps": data.next_steps
    }

    output_dict = data.model_dump()

    for sections in output_dict['sections']:
        section_name = str(sections['section_name']).lower().replace(" ", "_")
        report_dict['sections'].update({
            section_name: {
                "overview": sections['section_overview'],
                "section_recommendation": sections['general_recommendations'],
                'subject_domains': {}
            }
        })

        for domain in sections['domains']:
            domain_name = str(domain['domain_name']).lower().replace(' ', '_')
            report_dict['sections'][section_name]['subject_domains'][domain_name] = {
                'domain_overview': domain['domain_overview'],
                'domain_topics': {}
            }

            for topic in domain['topics']:
                topic_name = str(topic['topic_name']).lower().replace(' ', '_')

                report_dict['sections'][section_name]['subject_domains'][domain_name]['domain_topics'][topic_name] = {
                    'topic_current_status': topic['current_status'],
                    'topic_recommendations': topic['recommendations']
                }

    return report_dict
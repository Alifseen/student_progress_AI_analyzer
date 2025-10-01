import requests
import json
import os

### Processing Completion Topics and Count ###
class FetchStudentData:


    def __init__(self, student_id, classroom_id):
        header = {
                    "Authorization": f"Bearer {os.getenv('API_AUTH')}",
                    "Content-Type": "application/json"
                }

        overall_performance = f"enter the API endpoint for student's Overall Performance"
        topic_completion = f"enter the API for student's topicwise completion"
        scores_obtained = f"enter the API endpoint for student's topicwise score"

        self.overall_data = requests.get(overall_performance, headers=header).json()
        self.completion_data = requests.get(topic_completion, headers=header).json()
        self.scores_data = requests.get(scores_obtained, headers=header).json()

        self.completion = {}
        self.unattempted_tests = {}
        self.attempted_tests = {}
        self.score = {}
        self.progress = {}
        self.attempted_keys = ["attemptedPractices", "attemptedTests"]
        self.unattempted_keys = ["unAttemptedPractices", "unAttemptedTests"]



    def compile_attempt_dicts(self, complete_data):

        for data in complete_data:

            name = data.get('name')

            attempted = [x['name'] for k, v in data.items() if k in self.attempted_keys for x in v]
            unattempted = [x['name'] for k, v in data.items() if k in self.unattempted_keys for x in v]

            self.attempted_tests[name] = attempted
            self.unattempted_tests[name] = unattempted


    def compile_progress(self, data, attempted, unattempted):
        total_count = {"easy": 0, "medium": 0,"hard": 0}
        att_count = {"easy": 0, "medium": 0,"hard": 0}


        for t in attempted[data['name']]+unattempted[data['name']]:
            if "easy" in t:
                total_count["easy"] += 1
                if t in attempted[data['name']]:
                    att_count["easy"] += 1
            elif "medium" in t:
                total_count["medium"] += 1
                if t in attempted[data['name']]:
                    att_count["medium"] += 1
            else:
                total_count["hard"] += 1
                if t in attempted[data['name']]:
                    att_count["hard"] += 1

        def safe_div(num, den):
            return f'{(num/den)*100: .0f}%' if den > 0 else "0%"

        self.completion[data['name']] = {
            "Easy": safe_div(att_count['easy'], total_count['easy']),
            "Medium": safe_div(att_count['medium'], total_count['medium']),
            "Hard": safe_div(att_count['hard'], total_count['hard'])
        }


    def compile_scores(self, data):
        name = data.get('name')

        self.score.update({name: {}})

        test = data["latestPracticesDone"] + data["latestTestsDone"]

        for item in test:
            self.score[name].update({item['name']: f"{(item['obtainedPoints']/item['totalPoints'])*100: .0f}%"})


    def compile_overall_progress(self):
        self.progress.setdefault("overall_progress", {})
        for k, v in self.overall_data.items():
            if k == "timeSpentPractice":
                self.progress["overall_progress"]["Total Time Spent on Practice Questions"] = f"{v / 60: .0f} Mins"

            elif k == "timeSpentTest":
                self.progress["overall_progress"]["Total Time Spent on Tests"] = f"{v / 60: .0f} Mins"

            elif k == "totalQ_AnsweredOfPractices":
                self.progress["overall_progress"]["Total Practice Questions Attempted"] = v

            elif k == "totalCorrectAnsweredOfPractices":
                self.progress["overall_progress"]["Correctly Answered Practice Questions"] = v

            elif k == "totalQ_AnsweredOfTests":
                self.progress["overall_progress"]["Total Test Questions Attempted"] = v

            elif k == "totalCorrectAnsweredOfTests":
                self.progress["overall_progress"]["Correctly Answered Practice Questions"] = v

            elif k == "percentageCourseWork":
                self.progress["overall_progress"]["Percentage of Coursework Completed"] = f"{v: .0f}%"


    def calculate_score_by_difficulty(self, difficulty, data):

        obtained = sum([int(v.strip().replace("%", "")) for k, v in
                        self.progress[data['courseName']][data['subjectName']][data['sectionName']][data['name']][
                            "details"].items() if difficulty.lower() in k and v != 'No Attempt'])
        total = len([int(v.strip().replace("%", "")) for k, v in
                     self.progress[data['courseName']][data['subjectName']][data['sectionName']][data['name']][
                         "details"].items() if difficulty.lower() in k and v != 'No Attempt'])

        if total == 0:
            return "No Attempt"

        else:
            perc = obtained / total
            return f"{perc: .0f}%"


    def compile_all_data(self, data):

        self.progress.setdefault(data['courseName'], {}).setdefault(data['subjectName'], {}).setdefault(data['sectionName'], {})

        if 'test' not in data['name'].lower():
            self.progress[data['courseName']][data['subjectName']][data['sectionName']].update(
                {data['name']: {"details": {f"{k} Score": v for k, v in self.score[data['name']].items()} |
                                              {f"{t} Score": "No Attempt" for t in self.unattempted_tests[data['name']]}}}
            )

            self.progress[data['courseName']][data['subjectName']][data['sectionName']][data['name']]['summary'] =  \
                                 {k1: {"Avg Score for Attempted Tests": self.calculate_score_by_difficulty(k1, data)} | {"Completion": v1} for k1, v1 in self.completion[data['name']].items()}
        else:
            self.progress[data['courseName']][data['subjectName']][data['sectionName']].update(
                {data['name']: {"summary": {f"{k} Score": v for k, v in self.score[data['name']].items()} |
                                              {f"{t} Score": "No Attempt" for t in self.unattempted_tests[data['name']]}}}
            )


    def master_loop(self):
        sorted_completion_data = sorted(self.completion_data['topics'], key=lambda x: x['name'])
        self.compile_attempt_dicts(sorted_completion_data)

        sorted_score_data = sorted(self.scores_data['topics'], key=lambda x: x['name'])
        for i, data in enumerate(sorted_score_data):
            self.compile_progress(data, self.attempted_tests, self.unattempted_tests)
            self.compile_scores(data)
            self.compile_overall_progress()
            self.compile_all_data(data)

        return self.progress


def clean_percentage_values(data):
    if isinstance(data, dict):
        return {k: clean_percentage_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_percentage_values(element) for element in data]
    elif isinstance(data, str):
        if '%' in data:
            try:
                return float(data.replace('%', '').strip())
            except ValueError:
                return data
        elif "No Attempt" in data:
            try:
                return int(data.replace('No Attempt', '0').strip())
            except ValueError:
                return data
        else:
            return data
    else:
        return data

def data_segregation(data):
    overall, course = list(data.keys())
    subjects = list(data[course].keys())

    segregated = {overall: data[overall], **{subject: data[course][subject] for subject in subjects}}

    return segregated


def save_json(user_id, class_id, data, report):
    os.makedirs(os.path.dirname(f"Data/saved_progress_report/{user_id}-{class_id}/previous/heatmaps/"), exist_ok=True)

    with open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/report.json", "w") as fp:
        json.dump(report, fp)

    variable_names = []
    variable_values = []

    for k, v in data.items():
        str_to_float_data = clean_percentage_values(v)
        with open(f"Data/saved_progress_report/{user_id}-{class_id}/previous/{k.upper()}.json", "w") as fp:
            json.dump(str_to_float_data, fp)

        variable_names.append(k.upper())
        variable_values.append(v)

    return variable_names, variable_values



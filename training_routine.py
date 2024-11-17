"""
Chess Routine deployment system

Even weeks will be study weeks
Odd weeks will be playing weeks
"""

import requests
import datetime
from dotenv import load_dotenv
import os
import uuid

TODO_BASE_URL = "https://api.todoist.com/rest"
PROJECT_NAMING_FORMAT = "Year {}: Chess Study Action Plan"
SECTION_NAMING_FORMAT = "Week {:02d}: {} week"
DAILY_GOAL_NAMING_FORMAT = "Daily Goal {:03d}: {}"
WEEKLY_GOAL_NAMING_FORMAT = "Weekly Goal {:02d}: {}"

study_week_goals = {
    "Weekly":[
        "Active Reading of 2 Chapters in Silman Book",
        "Active Learning for 1 Openings Video",
        "Preparing key concepts for play week"
    ],
    "Daily":[
        "2x15min Chess Tactics",
        "Daily Puzzle",
        "Repertoire Pratice 30-50 moves",
        "Active Learning 1 Youtube Video",
        "Quick Review of prior study days"
    ]
}
play_week_goals = {
    "Weekly":[
        "Active Reading of 1 Chapter in Silman Book",
        "Review game play and create focus goals for study week"
    ],
    "Daily":[
        "5 Rapid Games",
        "Daily Puzzle",
        "Repertoire Pratice 10-20 moves",
        "15min Chess Tactics",
        "Review and refresh study concepts"
    ]
}

def define_week_info(seed_day):
    week_num = seed_day.isocalendar()[1]
    mode = "Playing" if week_num % 2 == 1 else "Studying"
    day_num = seed_day.timetuple().tm_yday
    week_day_number = seed_day.weekday()
    end_day = seed_day + datetime.timedelta(days=6-week_day_number)
    project_year = end_day.year
    
    return { "DayNum":day_num, "WeekNum":week_num, "WeekdayNum":week_day_number, "Year":project_year, "Mode":mode, "End_Date":end_day.strftime("%Y-%m-%d"), "Today_str":seed_day.strftime("%Y-%m-%d")}


def project_check(project_name, T_HEADER):
    print(f"Checking project '{project_name}' exists")
    projects_resp = requests.get(f"{TODO_BASE_URL}/v2/projects",headers=T_HEADER)
    print(projects_resp)
    if projects_resp.status_code == 200:
        for project in projects_resp.json():
            if project['name'] == project_name:
                print("Found Project")
                return True, project['id']
        print("Project Not Found")
        return False, None
    else:
        print("Error in Search")
        return False, None
    

def create_project(project_name, apikey):

    payload = {"name":project_name}
    headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {apikey}',
            'X-Request-Id': str(uuid.uuid4())
        }
    resp = requests.post(f"{TODO_BASE_URL}/v2/projects",json=payload, headers=headers)
    print(resp)

    return resp.json()['id']


def section_check(project_id, section_name, T_HEADER):
    print(f"Checking section {section_name} exists")
    try:
        #sections = api.get_sections(project_id=str(project_id))
        sections_resp = requests.get(f"{TODO_BASE_URL}/v2/sections?project_id={project_id}", headers=T_HEADER)
        print(sections_resp)
        for section in sections_resp.json():
            print(section['name'])
            if section['name'] == section_name:
                print("Found Section")
                return True, section['id']
        print("Section Not Found")
        return False, None
    except Exception as error:
        print(f"Search Error: {error}")
        return False, None
    

def create_section(project_id, section_name, apikey):

    payload = {"parent_id":project_id, "name":section_name}
    headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {apikey}',
            'X-Request-Id': str(uuid.uuid4())
        }
    resp = requests.post(f"{TODO_BASE_URL}/v2/sections",json=payload, headers=headers)
    print(resp)

    return resp.json()['id']


def check_create_tasks(tasks, ex_tasks, label, due_date, apikey, project_id, section_id):

    for task in tasks:
        found_flag = False
        for ex_task in ex_tasks:
            if ex_task['content'] == task:
                print(f"Found {label} Task")
                found_flag = True

        if not found_flag:
            print(f"{label} Task not found")
            print("Creating Task")

            payload = {
                "content": task,
                "due_date": due_date,
                "labels": [label],
                "project_id": project_id,
                "section_id": section_id
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {apikey}',
                'X-Request-Id': str(uuid.uuid4())
            }
            
            task_make_resp = requests.post(f"{TODO_BASE_URL}/v2/tasks",headers=headers, json=payload)
            print(task_make_resp.status_code)

def main():

    today = datetime.datetime.today()
    week_data = define_week_info(today)

    load_dotenv()
    apikey = os.getenv('TODOIST_APIKEY')

    T_HEADER = {"Authorization":f"Bearer {apikey}"}

    project_name = PROJECT_NAMING_FORMAT.format(week_data['Year'])
    check_flag, project_id = project_check(project_name, T_HEADER)

    if not check_flag:
        project_id = create_project(project_name, apikey)
    
    section_name = SECTION_NAMING_FORMAT.format(week_data["WeekNum"], week_data["Mode"])
    check_flag, section_id = section_check(project_id, section_name, T_HEADER)
    if not check_flag:
        section_id = create_section(project_id, section_name, apikey)
    
    if week_data['Mode'] == "Studying":
        d_tasks = [ DAILY_GOAL_NAMING_FORMAT.format(week_data['DayNum'], task) for task in study_week_goals['Daily'] ]
        w_tasks = [ WEEKLY_GOAL_NAMING_FORMAT.format(week_data['WeekNum'], task) for task in study_week_goals['Weekly'] ]
    elif week_data['Mode'] == "Playing":
        d_tasks = [ DAILY_GOAL_NAMING_FORMAT.format(week_data['DayNum'], task) for task in play_week_goals['Daily'] ]
        w_tasks = [ WEEKLY_GOAL_NAMING_FORMAT.format(week_data['WeekNum'], task) for task in play_week_goals['Weekly'] ]

    tasks_resp = requests.get(f"{TODO_BASE_URL}/v2/tasks?project_id={project_id}&section_id={section_id}", headers=T_HEADER)
    print(tasks_resp)
    tasks = tasks_resp.json()

    check_create_tasks(w_tasks, tasks, "Weekly", week_data['End_Date'], apikey, project_id, section_id)
    if week_data['WeekdayNum'] != 6:
        check_create_tasks(d_tasks, tasks, "Daily", week_data['Today_str'], apikey, project_id, section_id)
    else:
        print("Today is Sunday, no daily tasks to create.")



if __name__ == "__main__":
    main()
#############################################################################
# Github (https://github.com/ShoroukAziz/Notion-Integrations)
# Copyright (c) 2020 Shorouk Abdelaziz (https://shorouk.dev)
#############################################################################
import requests
import json
from pprint import pprint
from notion_client import Client
from datetime import datetime
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from pathlib import Path
import logging

CONFIG = {
    "Notion_database_ID": "the id of you Notion Database",  # CHANGE ME
    "task_list_id": "the id of the task lists of Google Tasks",  # CHANGE ME
    "Column_Name": "the name of the column where you want the tasks to be copied to",  # Change me
    "headers":  {
        'Authorization': "Your Notion Authentication Token",  # CHANGE ME
        'Content-Type': 'application/json',
        'Notion-Version': '2021-07-27'

    },
    "api_url": "https://api.notion.com/v1/pages",
    "CREDENTIALS_FILE": 'credentials.json',
    "token_file": 'token.json',
    "SCOPES": ['https://www.googleapis.com/auth/tasks'],

}


def queryUrlGenerator(db_id):
    return f'https://api.notion.com/v1/databases/{db_id}/query'


def notionAPICall(method, url, payload, headers):
    res = requests.request(method, url, headers=headers, data=payload)
    print(f'task created at {res.json()["url"]}')
    return res


def get_tasks_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(CONFIG["token_file"]):
        creds = Credentials.from_authorized_user_file(
            CONFIG["token_file"], CONFIG["SCOPES"])
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG["CREDENTIALS_FILE"], CONFIG["SCOPES"])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(CONFIG["token_file"], 'w') as token:
            token.write(creds.to_json())

    service = build('tasks', 'v1', credentials=creds)
    return service


def listTasks(service):
    response = service.tasks().list(tasklist=CONFIG["task_list_id"]).execute()
    items = response.get('items')

    if not items:
        print('No task lists found.')
        return
    else:
        taskList = []
        for item in items:
            task = {
                "Name": item["title"] + (item["notes"] if "notes" in item else ""),
                "id": item["id"]
            }
            taskList.append(task)
        return taskList


def deleteTaskFromGoogle(service, tasks):
    for task in tasks:
        service.tasks().delete(
            tasklist=CONFIG["task_list_id"], task=task["id"]).execute()


def createNotionStuff(tasks):
    for task in tasks:
        if tasks == []:
            return
        payload = json.dumps({
            'parent': {
                'database_id': CONFIG["Notion_database_ID"],
            },
            'properties': {
                CONFIG['Column_Name']: {
                    'title': [
                        {
                            'text': {
                                'content': task["Name"],
                            },
                        },
                    ],
                }
            },

        }
        )

        notionAPICall("POST", CONFIG["api_url"],
                      payload, CONFIG["headers"])
    return


if __name__ == "__main__":

    service = get_tasks_service()
    tasks = listTasks(service)
    print(f' found  {len(tasks)} new tasks')
    createNotionStuff(tasks)
    deleteTaskFromGoogle(service, tasks)

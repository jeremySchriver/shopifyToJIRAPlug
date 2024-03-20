import requests
import json


def createJIRATask(base_url,project_key,username,key,title,description,orderNumber,orderLink,orderItemNum,orderReceivedDate,orderDueDate,orderShipByDate):
    # Define the issue details
    issue_data = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": title,
            "description": description,
            "issuetype": {
                "name": "Task"
            },
            "priority": {
                "name": "Medium"
            },
            "duedate": orderDueDate,
            "customfield_10037": orderShipByDate,
            "customfield_10038": orderNumber,
            "customfield_10039": orderLink,
            "customfield_10040": orderItemNum,
            "customfield_10036": orderReceivedDate
        }
    }

    # Make a POST request to create the issue
    create_issue_url = f"{base_url}/rest/api/2/issue/"
    response = requests.post(create_issue_url, json=issue_data, auth=(username, key))
    print(response.text)
    return(response)

def createJIRASubTask(base_url,project_key,username,key,parentKey,title,description,orderDueDate):
    # Define the issue details
    issue_data = {
        "fields": {
            "project": {
                "key": project_key
            },
            "parent": {
                "key": parentKey,
            },
            "summary": title,
            "description": description,
            "issuetype": {
                "name": "Sub-task"
            },
            "duedate": orderDueDate,
        }
    }
    
    # Make a POST request to create the issue
    create_issue_url = f"{base_url}/rest/api/2/issue/"
    response = requests.post(create_issue_url, json=issue_data, auth=(username, key))
    print(response.text)
    return(response)
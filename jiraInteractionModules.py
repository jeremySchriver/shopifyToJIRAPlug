import requests
import json

def createJIRATask(base_url,project_key,username,key,title,description,orderNumber,orderLink,orderItemNum,orderReceivedDate):
    # Define the issue details
    # Need to look at adding additional data upon creation for filling fileds like due date and ship by date, reolve them around TAT (turn around time) so global variable can be created and adjusted as required
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
            "customfield_10038": orderNumber, # Description field Shopify Order Number
            "customfield_10039": orderLink, # Description field Shopify Order Link
            "customfield_10040": orderItemNum, # Description field Items In Order
            "customfield_10036": orderReceivedDate # Detail field for Order Received date, expects formatting similar to 2024-03-17T14:08-0400
        }
    }

    # Make a POST request to create the issue
    create_issue_url = f"{base_url}/rest/api/2/issue/"
    response = requests.post(create_issue_url, json=issue_data, auth=(username, key))

    return(response)

def createJIRASubTask(base_url,project_key,username,key,parentKey,title,description):
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
            }
        }
    }
    
    # Make a POST request to create the issue
    create_issue_url = f"{base_url}/rest/api/2/issue/"
    response = requests.post(create_issue_url, json=issue_data, auth=(username, key))

    return(response)
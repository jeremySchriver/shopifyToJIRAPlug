from jiraInteractionModules import createJIRATask, createJIRASubTask
from buildCardData import getShopifyOrderData, processShopifyOrderData, correctShopifyOrderDictionaries, buildCreateCardData
import json
import os

# Read the contents of the preferences.json file
with open(os.path.join(os.getcwd(),"preferences.json"), 'r') as file:
    preferences_data = json.load(file)

# Define JIRA credentials and project key
jira_username = preferences_data[0]["jira_username"]
jira_base_url = preferences_data[0]["jira_base_url"]
jira_project_key = preferences_data[0]["jira_project_key"]
jira_key = preferences_data[0]["jira_key"]

# Define Shopify details and credentials
shopify_key = preferences_data[0]["shopify_key"]
shopify_phrase = preferences_data[0]["shopify_phrase"]
shopify_site_name = preferences_data[0]["shopify_site_name"]
shopify_base_url = preferences_data[0]["shopify_base_url"]

shopify_request_type = "orders.json?"
#limit = 250 #currently hardset in the method
shopify_created_at_min = "2024-03-01T00:00:00-05:00"
shopify_fulfillment_status = "any" #doesn't seem to be working at this time
shopify_status = "any"
shopify_logOutputPath = "E:\\Code Projects\\Bug And Bear\\"


'''Start runner to get data and use it'''
data = getShopifyOrderData(shopify_key,shopify_phrase,shopify_site_name,shopify_base_url,shopify_request_type,shopify_status,shopify_created_at_min,shopify_logOutputPath)

orderDF,lineItemDF,orderNumberArray = processShopifyOrderData(data)

orderDF,lineItemDFCopy,orderNumberArray = correctShopifyOrderDictionaries(orderDF,lineItemDF,orderNumberArray)

cardInfo,subTaskCardInfo = buildCreateCardData(orderDF,lineItemDFCopy,orderNumberArray)

count = 0
while count < len(orderNumberArray):
    key = str(orderNumberArray[count])
    lineCount = 0
    lineItemsInOrder = orderDF[orderNumberArray[count]].iloc[0]['line_items_num']

    print((jira_base_url,
           jira_project_key,
           jira_username,
           jira_key,
           cardInfo[orderNumberArray[count]][4],
           cardInfo[orderNumberArray[count]][5],
           cardInfo[orderNumberArray[count]][0],
           cardInfo[orderNumberArray[count]][6],
           cardInfo[orderNumberArray[count]][7],
           cardInfo[orderNumberArray[count]][1]))
    response = createJIRATask(jira_base_url,
                              jira_project_key,
                              jira_username,
                              jira_key,
                              cardInfo[orderNumberArray[count]][4],
                              cardInfo[orderNumberArray[count]][5],
                              cardInfo[orderNumberArray[count]][0],
                              cardInfo[orderNumberArray[count]][6],
                              cardInfo[orderNumberArray[count]][7],
                              cardInfo[orderNumberArray[count]][1])

    if response.status_code == 200:
        # Parse the JSON string
        response_json = response.text.json()

        while lineCount < lineItemsInOrder:
            subKey = str(orderNumberArray[count]) + "_LI_" + str(lineCount)

            createJIRASubTask(jira_base_url,jira_project_key,jira_username,jira_key,response_json['key'],subTaskCardInfo[subKey][1],subTaskCardInfo[subKey][2])

            lineCount+=1
    else:
        print(f"Error creating card for order #{orderNumberArray[count]}")

    count+=1 
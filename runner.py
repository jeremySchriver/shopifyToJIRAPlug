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
shopify_created_at_max = "2024-03-01T00:00:00-05:00" #Currently not in use
shopify_fulfillment_status = "any" #doesn't seem to be working at this time
shopify_status = "any"
shopify_logOutputPath = "E:\\Code Projects\\ShopifyWork\\shopifyToJIRAPlug\\"

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
    
    response = createJIRATask(jira_base_url,
                              jira_project_key,
                              jira_username,
                              jira_key,
                              str(cardInfo[orderNumberArray[count]][6]),
                              str(cardInfo[orderNumberArray[count]][7]),
                              int(cardInfo[orderNumberArray[count]][0]),
                              str(cardInfo[orderNumberArray[count]][8]),
                              int(cardInfo[orderNumberArray[count]][9]),
                              cardInfo[orderNumberArray[count]][1],
                              cardInfo[orderNumberArray[count]][2],
                              cardInfo[orderNumberArray[count]][3])
    print(response.status_code)
    if response.status_code == 200 or 201:
        # Parse the JSON string
        response_json = response.json()

        while lineCount < lineItemsInOrder:
            subKey = str(orderNumberArray[count]) + "_LI_" + str(lineCount)

            createJIRASubTask(jira_base_url,
                              jira_project_key,
                              jira_username,
                              jira_key,
                              response_json['key'],
                              subTaskCardInfo[subKey][3],
                              subTaskCardInfo[subKey][4],
                              cardInfo[orderNumberArray[count]][2])

            lineCount+=1
    else:
        print(f"Error creating card for order #{orderNumberArray[count]}")

    count+=1 
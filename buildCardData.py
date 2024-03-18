import requests
import pandas as pd
from io import StringIO
import json
from urllib.parse import urlencode, urljoin
from rich.console import Console
import datetime
import pytz
import os
import copy
import re

def getShopifyOrderData(key,phrase,site_name,base_url,request_type,status,created_at_min,logOutputPath):
    url = f"https://{key}:{phrase}@{site_name}{base_url}{request_type}limit=250&status={status}&created_at_min={created_at_min}"

    # Get the current system time
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y.%m.%d")

    #Execute API call
    response = requests.get(url)

    if response.status_code == 200:
        # Read JSON data
        data = json.loads(response.text)

        #Dump raw json to file for logging/comparison
        # Path to the JSON file
        file_path = logOutputPath + str(formatted_time) + "_response.json"

        # Write data to the JSON file
        with open(file_path, "w") as json_file:
            json.dump(data, json_file)
        
        return(data)
    else:
        print(f"API call failed with the follow response code: {response.status_code}")
        return("Error received")

def processShopifyOrderData(data):
    count = 0
    itemCount = 0
    lineItemDF = {}
    orderDF = {}
    orderNumberArray = []

    #Tries to get the number of orders and catches for exception errors that could occur
    try:
        num_orders = len(data['orders'])
    except:
        num_orders = 0
        print("No orders found in the query")

    #Start main data loop if response contained an order
    if num_orders > 0:
        while count < num_orders:
            line_items_num = len(data['orders'][count]['line_items'])
            order_number = data['orders'][count]['order_number']
            orderNumberArray.append(str(order_number))
            key = str(order_number)

            #Create frame within the dictionary based on key information
            orderDF[key] = pd.DataFrame(columns=['order_id','order_number','created_at','fulfillment_status','financial_status','total_line_items_price','current_total_discounts','current_subtotal_price','total_shipping_price','total_price','customer_first_name','customer_last_name','customer_email_address','line_items_num'])

            if line_items_num > 0:
                while itemCount < line_items_num:             
                    #Check line item for number of properties
                    line_item_properties_num = len(data['orders'][count]['line_items'][itemCount]['properties'])
                    propCount = 0
                    propNameArray = []
                    propValueArray = []

                    #Loop through properties values that were found and add them to an array
                    while propCount < line_item_properties_num:
                        propNameValue = data['orders'][count]['line_items'][itemCount]['properties'][propCount]['name']
                        propValue = data['orders'][count]['line_items'][itemCount]['properties'][propCount]['value']

                        propNameArray.append(propNameValue)
                        propValueArray.append(propValue)

                        propCount += 1
                    
                    #Create frame data               
                    new_line_data = [data['orders'][count]['order_number'],
                                    data['orders'][count]['line_items'][itemCount]['id'],
                                    data['orders'][count]['line_items'][itemCount]['name'],
                                    data['orders'][count]['line_items'][itemCount]['price'],
                                    data['orders'][count]['line_items'][itemCount]['quantity'],
                                    line_item_properties_num,
                                    propNameArray,
                                    propValueArray]
                    
                    #Set key information for order#_LI_line#
                    LIkey = str(data['orders'][count]['order_number']) + "_LI_" + str(itemCount)

                    #Create frame within the dictionary based on key information
                    lineItemDF[LIkey] = pd.DataFrame(columns=['order_number','line_items_id','line_items_name','line_items_price','line_items_quantity','line_items_properties_num','line_items_properties_names','line_items_properties_values'])

                    lineItemDF[LIkey].loc[count] = new_line_data
                    itemCount += 1
            itemCount = 0
            tempValue = "None"

            #Course corrects for missing last name value in the top level json
            if data['orders'][count]['customer']['last_name'] is None:
                if data['orders'][count]['customer']['default_address']['last_name'] is None:
                    tempValue = "None"
                else:
                    tempValue = data['orders'][count]['customer']['default_address']['last_name']
            else:
                tempValue = data['orders'][count]['customer']['last_name']

            #Timestamp corrector
            input_string = data['orders'][count]['created_at']
            eastern = pytz.timezone('US/Eastern')
            dt_obj = datetime.datetime.fromisoformat(input_string)
            dt_obj_eastern = dt_obj.astimezone(eastern)
            formatted_timestamp = dt_obj_eastern.strftime('%Y-%m-%d %H:%M %Z')
            
            #Sets order values
            new_data = [data['orders'][count]['id'],
                        data['orders'][count]['order_number'],
                        formatted_timestamp,
                        data['orders'][count]['fulfillment_status'],
                        data['orders'][count]['financial_status'],
                        data['orders'][count]['total_line_items_price'],
                        data['orders'][count]['current_total_discounts'],
                        data['orders'][count]['current_subtotal_price'],
                        data['orders'][count]['shipping_lines'][0]['price'],
                        data['orders'][count]['total_price'],
                        data['orders'][count]['customer']['first_name'],
                        tempValue,
                        data['orders'][count]['contact_email'],
                        line_items_num]
            orderDF[key].loc[count] = new_data
            count += 1

        print("Order processing completed, please reference dictionaries orderDF and lineItemDF")
        return(orderDF,lineItemDF,orderNumberArray)
    else:
        print("No orders found in the query")

def correctShopifyOrderDictionaries(orderDF,lineItemDF,orderNumberArray):
    #Looped method to handle all orders in the dictionary
    #This method removes line items which are just options
    orderCount = 0

    try:
        del lineItemDFCopy
    except:
        print("No temp dictionary to delete, continuing process")

    #Copy the current dictionary so it can be modified
    lineItemDFCopy = copy.deepcopy(lineItemDF)

    while orderCount < len(orderNumberArray):
        count = 0
        itemIndex = []
        hasParentIndex = []
        currentItemCount = orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num']

        #Loop through dictionary and build arrays for itemIndex and hasParentIndex
        while count < currentItemCount:
            if "_gpo_parent_product_group" in str(lineItemDF[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_properties_names']):
                hasParentIndex.append(count)
            itemIndex.append(count)
            count+=1

        hasParentIndexCount = len(hasParentIndex)
        if hasParentIndexCount > 0:
            #Purges any identified option only line items from the temp dictionary
            count = 0
            while count < len(hasParentIndex):
                key = str(orderNumberArray[orderCount]) + "_LI_" + str(hasParentIndex[count])

                del lineItemDFCopy[key]
                
                index = itemIndex.index(hasParentIndex[count])
                del itemIndex[index]
                
                count+=1

            #Moves any remaining line items up the list into index locations that were previous purged
            count = 0
            while count < len(itemIndex):
                key = str(orderNumberArray[orderCount]) + "_LI_" + str(count)
                key1 = str(orderNumberArray[orderCount]) + "_LI_" + str(itemIndex[count])
                value = lineItemDFCopy[key1]
                del lineItemDFCopy[key1]
                lineItemDFCopy[key] = value
                
                count+=1

            #Resets the order dataframe to ensure it has the proper number of line items listed
            orderDF[orderNumberArray[orderCount]]['line_items_num'] = len(itemIndex)

            print(f"Order number #{orderNumberArray[orderCount]} - Line item total number changed to: {orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num']}")

            #print(orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num'])
        orderCount+=1
    #print(orderDF)
    print("Corrected line item dictionary created under name lineItemDFCopy")
    return(orderDF,lineItemDFCopy,orderNumberArray)


def buildCreateCardData(orderDF,lineItemDFCopy,orderNumberArray):
    #Loop through available frame and build all cards into a new dictionary
    cardInfo = {}
    subTaskCardInfo = {}

    orderCount = 0
    orderNumbers = len(orderNumberArray)

    while orderCount < orderNumbers:
        cardTitle = str(orderNumberArray[orderCount]) + " - " + str(orderDF[orderNumberArray[orderCount]].iloc[0]['customer_first_name']) + " " + str(orderDF[orderNumberArray[orderCount]].iloc[0]['customer_last_name'])

        cardDescriptionHeader = "\nOrder #" + str(orderNumberArray[orderCount]) + " | Placed On: " + str(orderDF[orderNumberArray[orderCount]].iloc[0]['created_at']) + " | Placed By: " + str(orderDF[orderNumberArray[orderCount]].iloc[0]['customer_first_name']) + " " + str(orderDF[orderNumberArray[orderCount]].iloc[0]['customer_last_name'])

        cardDescriptionItemHeader = f"\nLine Item(s) Present: {str(orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num'])} \nLine Item Information:"

        cardDesctiptionItemBody = ""
        subDescriptionBody = ""
        count = 0
        while count < orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num']:
            #Creates key and dictionary frams for storing subtask data
            subTaskKey = orderNumberArray[orderCount] + "_LI_" + str(count)
            subTaskCardInfo[subTaskKey] = pd.DataFrame(columns=['order_number','subTitle','subDescription'])

            #Builds parent card data
            cardDesctiptionItemBody += f"\n\t- Name: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_name']}" + f"\n\t\t- ID: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_id']}" + f"\n\t\t- Price: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_price']}" + f"\n\t\t- Quantity: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_quantity']}"
            
            #Builds subtask card data
            subDescriptionBody += f"\n\t\t- ID: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_id']}" + f"\n\t\t- Price: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_price']}" + f"\n\t\t- Quantity: {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_quantity']}"

            propCount = 0
            line_item_properties_num = lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_properties_num']
            if line_item_properties_num > 0:
                cardDesctiptionItemBody += "\n\t\t- Properties: "
                while propCount < line_item_properties_num:
                    propValue = lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_properties_values'][propCount]
                    strippedValue = re.sub("\\n","",str(propValue))
                    
                    cardDesctiptionItemBody += f"\n\t\t\t- {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_properties_names'][propCount]}" + f"\n\t\t\t\t- {strippedValue}"

                    subDescriptionBody += f"\n\t\t\t- {lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_properties_names'][propCount]}" + f"\n\t\t\t\t- {strippedValue}"

                    propCount += 1

            subValue = [orderNumberArray[orderCount],
                    lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{count}'].iloc[0]['line_items_name'],
                    subDescriptionBody]
        
            subTaskCardInfo[subTaskKey] = subValue

            count += 1

        #cardStatus = ""
        orderLink = urljoin("https://admin.shopify.com/store/bug-bear-6049/orders/",str(orderDF[orderNumberArray[orderCount]].iloc[0]['order_id']))

        #Find number of items in the order
        lineItemsInOrder = orderDF[orderNumberArray[orderCount]].iloc[0]['line_items_num']
        quantity = 0
        itemNumCount = 0

        while itemNumCount < lineItemsInOrder:
            lineQuantity = lineItemDFCopy[f'{orderNumberArray[orderCount]}_LI_{itemNumCount}'].iloc[0]['line_items_quantity']
            quantity+=lineQuantity
            itemNumCount+=1

        cardInfo[orderNumberArray[orderCount]] = pd.DataFrame(columns=['order_number','orderPlacedDate','order_status','financial_status','cardTitle','cardDescription','orderLink','itemsInOrder'])

        #Time corrector for JIRA card format
        timestamp = orderDF[orderNumberArray[orderCount]].iloc[0]['created_at']
        # Parse the timestamp string to a datetime object
        timestamp_datetime = datetime.datetime.strptime(timestamp[:-4], '%Y-%m-%d %H:%M')
        # Get the time zone abbreviation
        tz_abbr = timestamp[-3:]
        # Define time zones
        eastern = pytz.timezone('US/Eastern')
        # Localize the datetime object to the respective time zone
        localized_timestamp = eastern.localize(timestamp_datetime)
        # Convert the timestamp to the desired format
        formatted_timestamp = localized_timestamp.strftime('%Y-%m-%dT%H:%M%z')

        cardDetails = [orderNumberArray[orderCount],
                    formatted_timestamp,
                    orderDF[orderNumberArray[orderCount]].iloc[0]['fulfillment_status'],
                    orderDF[orderNumberArray[orderCount]].iloc[0]['financial_status'],
                    cardTitle,
                    cardDescriptionHeader + cardDescriptionItemHeader + cardDesctiptionItemBody,
                    orderLink,
                    quantity]
        cardInfo[orderNumberArray[orderCount]] = cardDetails
        orderCount+=1

    return(cardInfo,subTaskCardInfo)
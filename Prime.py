# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 14:12:58 2018
@author: Irina Spirina
Amazon Prime Project

Copy this file in the same folder as your downloaded emails ('original_msg (*).txt') 
from Amazon Prime.
"""

import re
import glob
from datetime import datetime
import csv
import pandas as pd

class OrderLine:
    '''
        Class to describe one order items
        input: full description line and total price line
        output: object with separated characteristics
    '''
    
    def __init__(self, description, totalprice):
        self.Description = description
        self.Name = ''
        self.Option = ''
        self.Packaging = ''
        self.TotalPrice = totalprice
        self.Price = 0
        self.Amount = 1
        self.IsChilled = False
        self.IsFrozen = False
        
        self.parse()
    
    def parse(self):
        #IsFrozen
        LookForFrozen = re.search(' - (.*)',self.Description)
        if LookForFrozen is not None:
            if LookForFrozen.group(1) == 'Frozen':
                self.IsFrozen = True
                self.Description = self.Description[:-len(LookForFrozen.group(0))]
        
        #IsChilled
        LookForChilled = re.search(' - (.*)',self.Description)
        if LookForChilled is not None:
            if LookForChilled.group(1) == 'Chilled':
                self.IsChilled = True
                self.Description = self.Description[:-len(LookForChilled.group(0))]
        
        #Packaging
        LookForPackaging = re.search(', (.*)',self.Description)
        if LookForPackaging is not None:
            self.Packaging = LookForPackaging.group(1)
            self.Description = self.Description[:-len(LookForPackaging.group(0))]
        
        #Option from Packaging
        LookForOption = re.search('(.*), ',self.Packaging)
        if LookForOption is not None:
            self.Option = LookForOption.group(1)
            self.Packaging = self.Packaging[len(LookForOption.group(0)):]
        else:
            self.Option = None
        if self.Packaging == '':
            self.Packaging = None
            
        #Separate Amount, Name
        LookForAmount = re.search('(\d+) x ',self.Description)
        if LookForAmount is not None:
            self.Amount = int(LookForAmount.group(1))
            self.Name = self.Description[len(LookForAmount.group(0)):]
        else:
            self.Name = self.Description

        #Count Price
        self.Price = round(float(self.TotalPrice/self.Amount),2)            
    
def parse_emails():
    '''
        function to parse standartized Amazon Prime emails
    '''
    ColumnNames = ['ID','FullDate','Total','Promo', 'Amount','Price','Name','Option','Packaging','Chilled','Frozen']
    AllOrders = pd.DataFrame(columns = ColumnNames)
    
    for filename in glob.glob('original_msg*'):
        with open(filename,'r') as f:
            message = f.read()

        body_search = re.search('Hello .*====',message,re.DOTALL)
        if body_search is None:
            continue
        
        #split text into list of lines without empty lines
        body = body_search.group().splitlines()
        body = [line for line in body if line.strip()]
        
        #collecting ID, DeliveryFullDate, Total, Promo to OrderData list
        ID = re.search('#(.*)',body[15]).group(1)
        DeliveryFullDate = datetime.strptime(body[4].strip(),"%b %d, %Y %I:%M %p")
        Total = float(re.search('S\$(.*)',body[-2]).group(1))
        SubTotalLine = float(re.search('S\$(.*)',[line for line in body if 'Subtotal' in line][0]).group(1))
        Promo = Total - SubTotalLine
        OrderData = [ID,DeliveryFullDate, Total, Promo]
        
        #parsing lines with order items and creating FullOrder list
        FullOrder = []
        FirstItemIndex = 17 #standard position for the begining of order items
        LastItemIndex = len(body)
        for index in range(FirstItemIndex,LastItemIndex,3):
            if '___' in body[index]:    #since line with item number is %3, we stop at '____'
                break
            
            desc = body[index].strip()  #one line of the order
            totalprice = float(body[index+1].strip()[2:])   #total price for the item
    
            #split description to separate fields and return as a Description list
            FullLine = OrderLine(desc, totalprice)
            Description = [FullLine.Amount,FullLine.Price,FullLine.Name,FullLine.Option,FullLine.Packaging,FullLine.IsChilled,FullLine.IsFrozen]
            
            FullOrder.append(OrderData+Description)     #filling up the FullOrder list
        
        ThisOrder = pd.DataFrame(FullOrder, columns = ColumnNames)      #convert list to DataFrame
        AllOrders = AllOrders.append(ThisOrder, ignore_index = True)    #add full order details to main database
        
    return AllOrders

OrdersDB = parse_emails()
OrdersDB.to_csv('Orders.csv')   #export dataframe to csv

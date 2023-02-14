# Load required libraries 
library(tidyverse)
library(lubridate)
library(DBI)
library(RMySQL)
library(httr)
library(methods)
library(xml2)

# Data items to retrieve from JAO Utility Tool
# Intraday ATC - Available in Publication (intradayAtc) and Utility Tool (GetAtcIntradayForAPeriod)
# Long Term Nominations - Available in Publication (ltn) and Utility Tool (GetLTNForAPeriod)
# ATC for non CWE borders - Only available in Utility Tool (GetAtcNonCWEForAPeriod)

# Custom function to download the data from the JAO Utility Tool----------------
#
# @param data_item Data item to retrieve from JAO. 
# Check https://publicationtool.jao.eu/core/api/ for all available data items.
# @param start_DateTime Start date and time in CET timezone 
# @param end_DateTime End date and time in CET timezone 
# @return A data frame with data from the server
#

JAOUtilTool <- setRefClass("JAOUtilTool",
  fields = list(
    action = "character", # https://utilitytool.jao.eu/CascUtilityWebService.asmx
    dateFrom = "character",
    dateTo = "character",
    path = "character"
  ),
  methods = list(
    http_request = function()
    {
      # Set URL for JAO Utility Tool 
      url <- paste0("http://utilitytool.jao.eu/CascUtilityWebService.asmx/", action)

      # Set headers for HTTP request
      query <- list(
        dateFrom = format(with_tz(datetimeFrom, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"), 
        dateTo = format(with_tz(datetimeTo, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"))

      # Get response from HTTP request
      response <- GET(url, query = query)

      # Get XML file from response
      content <- content(response, as = "text")

      return(content)
    },
    get_db_datestamps = function()
    {
      # Connect to the database to extract the dates
      username <- "etl"
      password <- "mg3GAz.Sm6#qdMqq"
      host <- "s-el-mmw-db"

      # Connect to the MySQL database 
      con <- dbConnect(
        MySQL(),
        user = username,
        password = password,
        host = host,
        dbname = "master")

      # Define the query
      query <- "SELECT t1.datestamp as `date_from`,t2.datestamp as `date_to` 
                FROM master.dimension_dates	t1 
                INNER JOIN master.dimension_dates t2 
                ON t1.datestamp=date_add(t2.datestamp, interval -1 day) 
                WHERE t1.yearstamp=2022 
                AND t1.datestamp<date(now());"

      # Connect to database
      rs <- dbSendQuery(con, query)

      # Retrieve result from query
      datestamps <- dbFetch(rs, n=-1)

      return(datestamps)
    },
    save_csv = function()
    {
      # Create a filename for the csv file
      filepath <- paste0(path, action, "\\", datestamps$date_from[i], ".csv")
      
      # Save the data to a csv file
      write.csv(df_all, filepath, row.names = FALSE)
    },
    get_dataframe <- function()
    {
      # get content request
      content <- http_request()
      
      # read in the XML file or string
      xml <- read_xml(content)

      # get the root node
      root_node <- xml_root(xml)

      # create an empty result data frame
      df_all <- data.frame()

      # loop through the child elements of the root node
      for (node in xml_children(root_node))
      {
        # create a list to store the tags and values for this node
        node_data <- list()
        
        for (element in xml_children(node)) {
          # get the tag of the child element
          tag <- xml_name(element)
          # modify tag to represent border direction
          if (tag != "Hour" & tag != "Date") {
            n <- nchar(tag)
            tag <- paste(substr(tag, 1, 2), ">", substr(tag, 3, n), sep="")
          }
          # get the value of the child element
          value <- xml_text(element)
          
          # add the tag and value to the node_data list
          node_data[[tag]] <- value
        }
        
        # convert the node_data list to a data frame and append it to the result data frame
        df_node <- data.frame(t(node_data))
        df_all <- rbind(df_all, df_node)
      }
      # Convert date and hour columns to their respective data types
      df_all$Date <- lubridate::ymd_hms(df$Date)
      df_all$Hour <- as.integer(df$Hour)
    },
    download_from_datestamps = function()
    {
      # Retrieve datestamps from EL database and
      # download and save dataframe for each day.

      # Get datestamps from database
      datestamps <- get_db_datestamps()

      # Initialize an empty list to store the data
      df_all <- c()

      # Loop through each row of the datestamps dataframe
      for (i in nrow(datestamps):1) 
      {
        
        # Create the start and end datetime strings for the period
        datetimeFrom <- paste0(datestamps$date_from[i]," 00:00")
        datetimeTo <- paste0(datestamps$date_to[i]," 00:00")
        
        # Print a message to show the current period being processed
        print(paste0("Executing period: ", datetimeFrom, " - ", datetimeTo))  
        
        # Get the data for a day
        df <- get_dataframe()

        # Save dataframe
        save_csv()
      }

    },
    download_period = function()
    {
      # Assuming that the input dates are more than two days apart,
      # download and save dataframe for each day.

      # Loop over input dates
      for (Date in seq(
        from = as.POSIXct(dateFrom, tz = "CET"), 
        to = as.POSIXct(dateTo, tz = "CET"), 
        by = "day")) 
        {

          # Create the start and end datetime strings for the period
          datetimeFrom = as.POSIXct(Date, "CET")
          datetimeTo = as.POSIXct(Date, "CET") + hours(23)

          # Print a message to show the current period being processed
          print(paste0("Executing period: ", datetimeFrom, " - ", datetimeTo))   

          # Get the data for a day
          df <- get_dataframe()

          # Save dataframe
          save_csv()
        }
    },
    download_one_day = function() 
    {
      # Assuming that the input dates are only one day apart,
      # download and save dataframe for one day.

      # Create the start and end datetime strings for the period
      datetimeFrom = as.POSIXct(dateFrom, "CET")
      datetimeTo = as.POSIXct(dateTo, "CET")

      # Get the data for a day
      df <- get_dataframe()

      # Save dataframe
      save_csv()
    },
    calculate_average_RAM = function()
    {
      # Group dataframe for one day into TSOs
      # and calculate average RAM.

      # Group dataframe by TSO
      df_RAMperTSO <- group_by(df_all, tso)
      # Summarize
      df_RAMperTSO <- summarize(RAM = mean(ram / fmax, na.rm = TRUE))

      return(df_RAMperTSO)
    }
  ))

# Instantiate object
jaoData <- JAOUtilTool(action = "GetAtcNonCWEForAPeriod", dateFrom = "2022-06-08 00:00", dateTo = "2022-06-10 00:00", path = "C:\\Users\\saizjo\\Downloads\\JAO\\")

# Call method to download data
jaoData$download_from_datestamps()

# Call method to save data
jaoData$save_csv()
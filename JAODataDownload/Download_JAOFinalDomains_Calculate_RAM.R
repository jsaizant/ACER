# Load required libraries 
library(tidyverse)
library(lubridate)
library(DBI)
library(RMySQL)
library(httr)
library(methods)

# Data items to retrieve from JAO Utility Tool
# Intraday ATC - Available in Publication (intradayAtc) and Utility Tool
# Long Term Nominations - Available in Publication (ltn) and Utility Tool
# ATC for non CWE borders - Only available in Utility Tool

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
    dateFrom = "numeric",
    dateTo = "numeric",
    path = "C:\\Users\\saizjo\\Downloads\\JAO\\"
  ),
  methods = list(
    http_request = function(action, dateFrom, dateTo)
    {
      # Set URL for JAO Utility Tool 
      url <- paste0("http://utilitytool.jao.eu/CascUtilityWebService.asmx/", action)

      # Set headers for HTTP request
      query <- list(
        dateFrom = format(with_tz(dateFrom, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"), 
        dateTo = format(with_tz(dateTo, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"))

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
                FROM master.dimension_dates	t1 inner join master.dimension_dates t2 
                on t1.datestamp=date_add(t2.datestamp, interval -1 day) 
                where t1.yearstamp=2022 and t1.datestamp<date(now());"

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
      write.csv(df, filepath, row.names = FALSE)
    },
    get_dataframe = function()
    {
      ### TOFIX

    },
    transform_IntradayATC <- function()
    {
      ### TOFIX

    },
    transform_LongTermNomination <- function()
    {
      ### TOFIX

    },
    transform_ATCNonCWE <- function()
    {
      ### TOFIX

    },
    download_from_datestamps = function()
    {
      ### TOFIX
      # Get datestamps from database
      datestamps <- get_db_datestamps()

      # Initialize an empty list to store the data
      df_all <- c()

      # Loop through each row of the datestamps dataframe
      for (i in nrow(datestamps):1) {
        
        # Create the start and end datetime strings for the period
        datetime_start <- paste0(datestamps$date_from[i]," 00:00")
        datetime_end <- paste0(datestamps$date_to[i]," 00:00")
        
        # Print a message to show the current period being processed
        print (paste0("Executing period: ",datestamps$date_from[i]," - ",datestamps$date_to[i]))  
        
        # Get the data for a day
        df <- get_dataframe()

        # Save dataframe
        save_csv()
      }

    },
    download_period = function()
    {
      ### TOFIX
      for (i in seq_along(seq.POSIXt(
        from = as.POSIXct("2022-06-09", "CET"),
        to = as.POSIXct("2022-06-15", "CET"),
        by = "day"))) 
        {
          # Define the date for the current iteration of the loop 
          Date = seq.POSIXt(
            from = as.POSIXct("2022-06-09", "CET"),
            to = as.POSIXct("2022-06-30", "CET"),
            by = "day")[i]
          # Call the JAOPuTo_finaldomain function for the current date
          JAOPuTo_finaldomain(
            start_DateTime = Date,
            end_DateTime = Date + hours(23))
          # Get the data for a day
          df <- get_dataframe()

          # Save dataframe
          save_csv()
      }
    },
    download_one_day = function() 
    {
      # Get the data for a day
      df <- get_dataframe()

      # Save dataframe
      save_csv()
    },
    calculate_average_RAM = function()
    {
      # Group dataframe by TSO
      df_RAMperTSO <- group_by(df, tso)
      # Summarize
      df_RAMperTSO <- summarize(RAM = mean(ram / fmax, na.rm = TRUE))

      return(df_RAMperTSO)
    }
  ))

# Instantiate object
jaoData <- JAOUtilTool(action = "GetAtcNonCWEForAPeriod", dateFrom = "2022-06-08 00:00", dateTo = "2022-06-10 00:00")

# Call method to download data
jaoData$download_from_datestamps()

# Call method to save data
jaoData$save_csv()

JAOPuTo_finaldomain <- function(data_item, start_DateTime, end_DateTime) {
  ### TODO Adapt function for each data item
  
  # Initialize the data frame
  df_finaldomain <- data.frame()
  
  # Make a GET request to the server 
  FinalDomain <- httr::GET(paste0("https://publicationtool.jao.eu/core/api/data/", data_item),
                           query = list(FromUtc = format(with_tz(start_DateTime, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"),
                                        ToUtc = format(with_tz(end_DateTime, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"))) %>%
  httr::content(as = "text") %>%
  jsonlite::fromJSON()
  
  if(FinalDomain$data != list()){
    
    # Clean the data 
    df_finaldomain <- FinalDomain$data %>%
    mutate(DateTime = with_tz(as.POSIXct(dateTimeUtc,
                                         format = "%Y-%m-%dT%H:%M:%SZ",
                                         tz = "UTC"),
                              "CET"),
           tso = recode(tso,
                        "50HERTZ" = "50Hertz",
                        "AMPRION" = "Amprion",
                        "ELIA" = "Elia",
                        "TENNETBV" = "TenneT BV",
                        "TENNETGMBH" = "TenneT GmbH",
                        "TRANSELECTRICA" = "Transelectrica",
                        "TRANSNETBW" = "TransnetBW")) %>%
      
    # Select relevant columns
    select(id, DateTime, everything(), -dateTimeUtc) %>%
    return()}
  
  else{
    
    print(sprintf("No data found for period /%s - /%s", start_DateTime, end_DateTime))
    df_finaldomain <- FinalDomain$data %>%
    return()}
  
}



# Initialize an empty list to store the data
df_all <- c()

# Loop over data items
for (data_item in items){
  # Loop through each row of the date stamps data frame --------------------------
  for (i in nrow(datestamps):1) {
    
    # Create the start and end datetime strings for the period
    datetime_start <- paste0(datestamps$date_from[i]," 00:00")
    datetime_end <- paste0(datestamps$date_to[i]," 00:00")
    
    # Print a message to show the current period being processed
    print (paste0("Executing period: ",datestamps$date_from[i]," - ",datestamps$date_to[i]))  
    
    # Call the JAOPuTo_finaldomain function to get the data for the defined period
    df <- JAOPuTo_finaldomain(data_item = data_item,
                              start_DateTime = as.POSIXct(datetime_start, "CET"),
                              end_DateTime = as.POSIXct(datetime_end, "CET"))
    
    # Filter and manipulate the data to keep specific columns
    df_trunc <- df[,c(2,3,4,5,6,7,8,11,12,13,17,18,19,21,22,23,27)]
    
    # Create a filename for the csv file
    filename <- paste0("C:\\Users\\saizjo\\Downloads\\JAO\\", data_item, "\\", datestamps$date_from[i], ".csv")
    
    # Save the truncated data to a csv file
    write.csv(df_trunc, filename, row.names = FALSE)
  }
}

# Download the Final Domains data for a one-day period -------------------------
df <- JAOPuTo_finaldomain(start_DateTime = as.POSIXct("2022-06-08 00:00", "CET"),
                          end_DateTime = as.POSIXct("2022-06-09 00:00", "CET"))

# Note: the function should work for any defined period 
# (as long as end_DateTime is after start_DateTime), 
# but for longer periods, the JAO server often returns an error. 
# In that case, it's probably easier to write a for-loop with the above function 
# which saves daily csv-files locally (example below)

# Download the Final Domains data for a defined period -------------------------
for (i in seq_along(seq.POSIXt(from = as.POSIXct("2022-06-09", "CET"),
                               to = as.POSIXct("2022-06-15", "CET"),
                               by = "day"))) {
  
  # Define the date for the current iteration of the loop 
  Date = seq.POSIXt(from = as.POSIXct("2022-06-09", "CET"),
                    to = as.POSIXct("2022-06-30", "CET"),
                    by = "day")[i]
  
  # Call the JAOPuTo_finaldomain function for the current date
  JAOPuTo_finaldomain(start_DateTime = Date,
                      end_DateTime = Date + hours(23)) %>% 
    
  # Save the data to a csv file with the date in the file name
  write_csv2(paste0("data/",
                    as.Date(Date),
                    ".csv"))
  
}


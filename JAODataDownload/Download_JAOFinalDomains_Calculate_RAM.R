# JAO Utility Tool ETL Script 2023
# Data items to retrieve from JAO Utility Tool:
# Intraday ATC - Available in Publication (intradayAtc) and Utility Tool (GetAtcIntradayForAPeriod)
# Long Term Nominations - Available in Publication (ltn) and Utility Tool (GetLTNForAPeriod)
# ATC for non CWE borders - Only available in Utility Tool (GetAtcNonCWEForAPeriod)

install.packages("librarian")

librarian::shelf(DBI, dplyr, reshape2, RMySQL, tidyverse, lubridate, httr, methods, xml2, micropan)

################################################################################

# Empty data environment
rm(list=ls())

# Set working directory
workDirectory <- getwd()
#workDirectory <- setwd("")

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
    path = "character",
    clear_na = "logical"
  ),
  methods = list(
    initialize = function(action = NULL, dateFrom = NULL, dateTo = NULL, path = NULL, clear_na = NULL) 
      {
      if (!is.null(action)) {
        .self$action <- action
      }
      if (!is.null(dateFrom)) {
        .self$dateFrom <- dateFrom
      }
      if (!is.null(dateTo)) {
        .self$dateTo <- dateTo
      }
      if (is.null(path)) {
        .self$path <- getwd()
      } else {
        .self$path <- path
      }
      if (is.null(clear_na)) {
        .self$clear_na <- FALSE
      } else {
        .self$clear_na <- clear_na
      }
      
      
      validObject(.self)
      .self
    },
    
    http_request = function(datetimeFrom, datetimeTo)
    {
      # Set URL for JAO Utility Tool 
      url <- paste0("http://utilitytool.jao.eu/CascUtilityWebService.asmx/", .self$action)

      # Set headers for HTTP request
      query <- list(
        dateFrom = format(with_tz(datetimeFrom, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"), 
        dateTo = format(with_tz(datetimeTo, "UTC"), "%Y-%m-%dT%H:%M:%S.000Z"))

      # Get response from HTTP request
      response <- GET(url, query = query)

      # Get XML file from response
      content <- httr::content(response, as = "text")

      return(content)
    },
    
    get_db_datestamps = function()
    {
      # Connect to the database to extract the dates
      username <- "etl"
      password <- "mg3GAz.Sm6#qdMqq"
      host <- "s-el-mmw-db"

      # Connect to the MySQL database 
      con <- DBI::dbConnect(
        RMySQL::MySQL(),
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
      
      # Retrieve result from query
      datestamps <- RMySQL::dbGetQuery(con, query)
      
      # Close the database connection
      RMySQL::dbDisconnect(con)
      
      return(datestamps)
    },
    
    transpose_dataframe = function(df)
    {
      df <- reshape2::melt(df, 
                           id.vars = "date_time",
                           na.rm = FALSE,
                           value.name = "value",
                           variable.name = "border"
                           )
    },
    
    find_borders = function(df)
    {
      eucountry_tags <- c(
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
        "GB"
      )
      
      # Create empty columns to store results
      df$in_country <- NA
      df$out_country <- NA
      
      # Loop over each row in the data frame
      for (i in 1:nrow(df)) {
        border <- as.character(df$border[i])
        # IN country is first country tag
        df$in_country[i] <- substr(border, 1, 2)
        # OUT country are the rest of country tags (may be more than one)
        # Remove first country tag
        n <- nchar(border)
        out_countries <- substr(border, 3, n)
        # Search for codes
        matches <- gregexpr(pattern = paste(eucountry_tags, collapse="|"), text = out_countries, ignore.case = FALSE, extract = TRUE)
        # Place in OUT country column
        df$out_country[i] <-  paste(matches[[1]], collapse = "/")
      }
      
      # Return the updated data frame
      return(df)
    },
    
    clear_na_zero_values = function(df)
    {
      df <- dplyr::filter(df, !is.na(df$value))
      df <- dplyr::filter(df, df$value != 0)
      df <- dplyr::filter(df, df$value != "")
    },
    
    save_csv = function(df, datetimeFrom = NULL)
    {
      # Check if datetime are complete
      if (is.null(datetimeFrom)) {
        datetimeFrom <- as.POSIXct(.self$dateFrom, tz = "CET")
      }
      # Create a filename for the csv file
      filepath <- file.path(.self$path, paste0(.self$action, "-", datetimeFrom, ".csv"))
      print(paste0("Saved in:", filepath))
      
      # Save the data to a csv file
      write.csv(df, filepath, row.names = FALSE)
    },
    
    get_dataframe = function(datetimeFrom = NULL, datetimeTo = NULL) 
      {
      # Check if datetimes are complete
      if (is.null(datetimeFrom)) {
        datetimeFrom <- as.POSIXct(.self$dateFrom, tz = "CET")
      }
      if (is.null(datetimeTo)) {
        datetimeTo <- datetimeFrom + hours(23)
      }
      
      # get content request
      content <- http_request(datetimeFrom, datetimeTo)
      
      # read in the XML file or string
      xml <- xml2::read_xml(content)
      
      # get the root node
      root_node <- xml2::xml_root(xml)
      
      # create an empty result data frame
      df_all <- data.frame(stringsAsFactors = FALSE)
      
      # loop through the child elements of the root node
      for (node in xml2::xml_children(root_node)) {
        # create a list to store the tags and values for this node
        node_data <- list()
        
        for (element in xml2::xml_children(node)) {
          # get the tag and value of the child element
          tag <- xml2::xml_name(element)
          value <- xml2::xml_text(element)
          
          # add the tag and value to the node_data list
          node_data[[tag]] <- value
        }
        
        # convert the node_data list to a data frame
        df_node <- data.frame(t(node_data), stringsAsFactors = FALSE)
        
        # Convert the Date column to POSIXct type using ymd_hms()
        df_node$Date <- ymd_hms(df_node$Date)
        
        # Combine the Date and Hour columns into a new date_time column
        df_node$date_time <- paste0(format(df_node$Date, "%Y-%m-%d"), 
                                    " ", sprintf("%02d", as.integer(df_node$Hour)), 
                                    ":00:00", sep = "")
        df_node$date_time <- as.POSIXct(df_node$date_time, tz = "CET")
        
        # remove the original Date and Hour columns
        df_node$Date <- NULL
        df_node$Hour <- NULL
        
        # Append it to the result data frame
        df_all <- rbind(df_all, df_node)
      }
      
      # convert all non-date columns to character
      non_date_cols <- which(sapply(df_all, class) != "POSIXct")
      df_all[,non_date_cols] <- lapply(df_all[,non_date_cols], as.character)
      
      return(df_all)
    },
    
    download_from_datestamps = function()
    {
      # Retrieve datestamps from EL database and
      # download and save dataframe for each day.

      # Get datestamps from database
      datestamps <- .self$get_db_datestamps()

      # Initialize an empty dataframe
      df_all <- list()

      # Loop through each row of the datestamps dataframe
      for (i in nrow(datestamps):1) 
      {
        # Create the start and end datetime strings for the period
        datetimeFrom <- paste0(datestamps$date_from[i]," 00:00")
        datetimeTo <- paste0(datestamps$date_to[i]," 00:00")
        
        # Print a message to show the current period being processed
        print(paste0("Executing period: ", datetimeFrom, " - ", datetimeTo))  
        
        # Get the data for a day
        df <- .self$get_dataframe(datetimeFrom, datetimeTo)
        
        # transpose dataframe
        df <- .self$transpose_dataframe(df)
        
        # Get IN/OUT countries
        tryCatch({
          df <- .self$find_borders(df)
        }, error = function(e) {
          print(paste0("Error while finding countries: ", e))
        })
        
        # remove NA and zero values if specified
        if (.self$clear_na == TRUE) {
          df <- .self$clear_na_zero_values(df)  
        }

        # Save dataframe
        .self$save_csv(df, datetimeFrom)
      }

    },
    
    download_period = function()
    {
      # Assuming that the input dates are more than two days apart,
      # download and save dataframe for each day.

      # Loop over input dates
      for (Date in seq(
        from = as.POSIXct(.self$dateFrom, tz = "CET"), 
        to = as.POSIXct(.self$dateTo, tz = "CET"), 
        by = "day")) 
        {
          # Create the start and end datetime strings for the period
          datetimeFrom <- as.POSIXct(Date, "CET")
          datetimeTo <- as.POSIXct(Date, "CET") + hours(23)

          # Print a message to show the current period being processed
          print(paste0("Executing period: ", datetimeFrom, " - ", datetimeTo))   

          # Get the data for a day
          df <- .self$get_dataframe(datetimeFrom, datetimeTo)
          
          # transpose dataframe
          df <- .self$transpose_dataframe(df)
          
          # Get IN/OUT countries
          tryCatch({
            df <- .self$find_borders(df)
          }, error = function(e) {
            print(paste0("Error while finding countries: ", e))
          })
          
          # remove NA and zero values if specified
          if (.self$clear_na == TRUE) {
            df <- .self$clear_na_zero_values(df)  
          }

          # Save dataframe
          .self$save_csv(df, datetimeFrom)
        }
    },
    
    download_one_day = function() 
    {
      # Starting from the dateTo,
      # download and save dataframe for one day.

      # Create the start and end datetime strings for the period
      datetimeFrom <- as.POSIXct(.self$dateFrom, tz = "CET")
      datetimeTo <- datetimeFrom + hours(23)

      # Get the data for a day
      df <- .self$get_dataframe(datetimeFrom, datetimeTo)
      
      # transpose dataframe
      df <- .self$transpose_dataframe(df)
      
      # Get IN/OUT countries
      tryCatch({
        df <- .self$find_borders(df)
      }, error = function(e) {
        print(paste0("Error while finding countries: ", e))
      })
      
      # remove NA and zero values if specified
      if (.self$clear_na == TRUE) {
        df <- .self$clear_na_zero_values(df)  
      }

      # Save dataframe
      .self$save_csv(df, datetimeFrom)
    },
    
    calculate_average_RAM = function(df)
    {
      # Group dataframe for one day into TSOs
      # and calculate average RAM.
      
      # Create the start and end datetime strings for the period
      datetimeFrom <- as.POSIXct(dateFrom, "CET")
      datetimeTo <- as.POSIXct(dateTo, "CET")
      
      # Get the data for a day
      df <- .self$get_dataframe(datetimeFrom, datetimeTo)
      
      # Group dataframe by TSO
      df_RAMperTSO <- group_by(df, tso)
      # Summarize
      df_RAMperTSO <- summarize(RAM = mean(ram / fmax, na.rm = TRUE))

      return(df_RAMperTSO)
    }
  ))


# Data items to retrieve from JAO Utility Tool
# Intraday ATC - Available in Publication (intradayAtc) and Utility Tool (GetAtcIntradayForAPeriod)
# Long Term Nominations - Available in Publication (ltn) and Utility Tool (GetLTNForAPeriod)
# ATC for non CWE borders - Only available in Utility Tool (GetAtcNonCWEForAPeriod)

data_actions <- c("GetAtcIntradayForAPeriod", "GetLTNForAPeriod", "GetAtcNonCWEForAPeriod")


for (action in data_actions) {
  # Instantiate object
  jaoData <- JAOUtilTool(action = action, dateFrom = "2021-01-01", dateTo = "2021-01-02", path = "C:/Users/saizjo/Downloads/JAO", clear_na = TRUE)
  jaoData$download_one_day()
}

# Instantiate object manually step by step
jaoData <- JAOUtilTool(action = "GetAtcIntradayForAPeriod", dateFrom = "2021-01-01", dateTo = "2021-01-02", path = "C:/Users/saizjo/Downloads/JAO", clear_na = TRUE)

df <- jaoData$get_dataframe()

df <- jaoData$transpose_dataframe(df)

df <- jaoData$find_borders(df)

jaoData$save_csv(df)

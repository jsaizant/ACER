# CATALOGUE OF REQUIREMENTS PROJECT

Version: 06/03/2023

Authors: 	

Tom Gagnebet (tom.gagnebet@student-cs.fr)

Kristy Louise Rhades (kristylou.rhades@gmail.com)

Jose Javier Saiz (josejavier.saiz.anton@gmail.com)

Mariia Melnychenko (mamelnychenkoo@gmail.com)

### 1.	Prerequisite:
- 9.1 Enforcement methods final - endorsed in Dec 2021 BoR.docx

### 2.	Objective:
The main goal is to exhaustively list every paragraph of all articles of every TCM and GL to ensure a full coverage of implementable requirements and their monitoring afterwards. This includes ELE, SO, CACM, FCA and EB Regulations and annexes.

## EXTRACTION EXERCISE

### 1.	Input:
- FOLDER_PATH: Folder where the regulation PDF documents are stored
- STAKEHOLDER_LIST: Identified (ex ante) stakeholders who could be obliged by legal requirement
- excel_export: Boolean variable allowing to export or not the pandas dataframe to an XLSX file.

### 2.	Output:
- df_tcm: Table of all TCMs and GLs with additional information
- df_requirement: Table of all paragraphs with additional information

### 3.	Method:
The Python script uses the 'pdfplumber' library (https://github.com/jsvine/pdfplumber) to extract paragraphs from regulation PDF documents (GLs and TCMs) to create a catalogue of requirements.

This identifies three distinct tasks (listed in order of importance):
1)	To determine the structure of the regulation documents (number of articles, number of paragraphs, etc.);
3)	To display the content of the paragraphs identified (text, equation, table etc.);
4)	To pre-identify if a paragraph contains a legally binding requirement.

#### Task 1:
Task 1 is addressed in the first six columns of the table_of_requirement:
- Column ‘Requirement_id’ is an identification number for each paragraph ;
- Column ‘TCM_id’ is an identification number for each regulation (TCMs or GLs) ;
- Column ‘TCM_full_name’ is linked (lookup function) to the table_of_TCM to give information on the TCM based on ‘TCM_id’ ;
- Column ‘Article_nb’ is the article number of the paragraph displayed ;
- Column ‘Paragraph_nb’ is the paragraph number – within an article – of the paragraph displayed.

The current version of the Python script (v1.3) performs with a 100% accuracy in regard to Task 1, except when the regulation itself contains typographical errors when referring to articles and paragraphs. So far, typographical errors were identified in four different TCMs:
- CACM 4. Max-min prices DA (there are two articles 1.);
- FCA 10. CCM Nordic (there are two paragraphs 23.5);
- EB aFFR IF (paragraph 14.9 is called 14.5);
- EB Capacity CO Nordic exemption (the paragraphs in article 2 are mixed up).

NOTE: In that case, it needs to be decided whether corrections will be made manually.

#### Task 2:
Task 2 is addressed in the seventh column of the table_of_requirement:
- Column ‘Text’ is the content of the paragraph displayed.

NOTE: Most of the time, the content of a paragraph is plain text, which is easy to extract and display in a table. Other times, equations or tables can be a struggle for the ‘pdfplumber’ library to extract. Therefore, some inconsistency might remain, but as long as the article and paragraph reference are correct, implementation can be monitored and one can go to the original document to read the proper content.

#### Task 3:
Task 3 is addressed in the last four columns of the table_of_requirement:
- Column ‘Requirement_keyword’ is “shall” or “may”
- Column ‘Stakeholder_identified’ is one of the stakeholder in the STAKEHOLDER_LIST
- Column ‘Frequency’ is the frequency of the requirement as stated in the regulation (ex: “annually”, biennially”, etc.)
- Column ‘Monitoring_status’ is the status of the monitoring: [‘Not required’, ‘Completed’, ‘Ongoing’, ‘To monitor’, ‘Pending’], “Pending” being the default option if a “shall” has been identified with in front a stakeholder.

NOTE: Task 3 is a first naive scanning method based on the identification of the word “shall” and linked with a specific stakeholder name that we previously identified as a potential obliged stakeholder. However, this first naive method should be taken simply as an indication (heuristic) and should always be double-checked by policy officers to determine whether the identified imperative is relevant or not.

### 4.	Where to find regulations:
Given the right FOLDER_PATH (\\s-int2019-sp\sites\public\Shared Documents\Electricity\Market Codes\Market Codes WEB) input pointing the “Market Codes WEB" folder, the algorithm is going to look for documents only in the “Approved” folder of each TCM folders of each "FCA", "CACM", "EB", "Regulation", “ELE”, “SO” folders. 

### 5.	Exceptions:
Each file is marked with a Boolean variable under the "Ignore_status" column in the table of TCMs, which is used to determine whether or not the file is analysed for the table of requirements. Initially, until version 1.3 of the script, the following regulatory documents were excluded from the analysis, resulting in 41 out of 137 documents being excluded:
- Regulation documents that cover non-relevant geographical perimeters (former CCR, bilateral, etc.). Relevant geographic regions are:
    -   "BALTIC",
    -   "CORE",
    -   "GRIT",
    -   "HANSA",
    -   "IT NORTH",
    -   "NORDIC",
    -   "SEE",
    -   "SWE",
    -   "UCTE",
    -   "EU-WIDE"
- Annexes.
- Regulation documents that correspond to TSO settlements.
- Amendment proposals without a new fully drafted version of the TCM.
- Scanned documents, which are unfit for text extraction:
    -   Action 5c - IDCZGT ACER decision Annex I.pdf
    -   Action 9 - CCM CORE ACER Decision Annex I (DA).pdf
    -   Action 4 - HAR annex SEE ACER Decision 06-2017 Annex I.pdf
    
These exceptions were removed and all 141 regulatory documents are analysed in the Table of Requirements.

## IMPLEMENTATION INTO MONOCLE

### 1.	Usage of the Catalogue of Requirement and implementation into the MONOCLE application
As long as Task 1 is complete, the catalogue of requirement will list all the articles and paragraphs of the regulations. Importing this list into the MONOCLE application will allow ACER policy officers to monitor exhaustively the implementation of market codes. Tasks 2 and 3 of the EXTRACTION EXERCISE provide additional indicative information that is not actually required.

The technical interconnection between the catalogue of requirement and MONOCLE application should be chosen under guidance of the external IT developer. In the event of changes in the structure of table_of_tcm or table_of_requirement, it is most important to guarantee compatibility between the data set (catalogue of requirement) and application. At all times, it needs to be ensured that the excel workbook tables are in the right order.

### 2.	Transforming the raw data output from the EXTRACTION EXERCISE for upload in MONOCLE
The extraction automatically generates two excel workbooks, catalogue_of_tcms_auto.xlxs and catalogue_of_requirement_auto.xlxs. 
- Merge the workbooks into one by creating one table for each workbook.
- Delete the first three letters from the column TCM_name under table_of_tcm (for example, by using the formula =RIGHT(cell to delete letters from, LEN(cell to delete letters from)-3)) in a new column TCM_name_actual. The first three letters are a side-product of the extraction exercise and are of no further relevance in the monitoring process. Some cells might only depict two letters (one number and one space). For those, add one letter manually, so that the chosen formula can delete the right number of characters.

After completion of the above steps, the values Regulation in the Regulation_name column under table_of_tcm needs to be switched with values SO, EB, FCA, ELE, CACM in TCM_name column respectively. In TCM_name column any two number should be added before Regulation (for the RIGHT formula to be correctly executed). 

Filtering requirements by regulation, TCM or geographic parameter is an essential part in the daily operation of the application by the users. In the current version of the MONOCLE test application, a merge between the columns Regulation_name, TCM_name_actual and Geographic_parameter is required to create the new column Full_name, which is used as the basis for parts of the filter options.
- Use the CONCATENATE formula to create Full_name out of Regulation_name, TCM_name_actual and Geographic_parameter (in that order) in the table_of_tcm table. Make sure to arrange the column in the same structure as all previous catalogue_of_tcms (see previous versions in the ARCHIVE).

It needs to be discussed with the external IT developer whether the concatenation of the three mentioned columns is actually needed or should better be made redundant. 

As a by-product of extraction exercise, such values as “article number”, “article name”, “title number and name” are also extracted under table_of_requirment. All textual values in “Paragraph_nb” column need to be manually filtered and deleted. Solely filtering will not be effective, as the file loader reads hidden values. 

In the next step, the TCM_full_name needs to be transferred into the catalogue_of_requirement table. To do so, a new column also called TCM_full_name, and inserted after TCM_id using the VLOOKUP formula is required. The TCM_id functions as common denominator:
- =VLOOKUP(B2,'table_of_tcm '!A:I,  9, 0)

### 3.	Implementation of the Catalogue of Requirement in MONOCLE
Once the Catalogue of Requirement has been prepared, the MONOCLE tool should allow for an upload function operated by ACER users. Given the possibility of errors in the data tables, the uploaded requirements should be made editable. The details about the development of the application for notifications and monitoring be found in Annex I of the Terms of Reference.

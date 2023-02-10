import pandas as pd
import numpy as np
import xml.etree.ElementTree as et
import re

### GLOBAL CONSTANT

# Set all possible SQL statements allowed in the dataset
SQL_STATEMENTS = [
    "SELECT", 
    "INSERT", 
    "UPDATE", 
    "DELETE", 
    "CREATE", 
    "ALTER", 
    "DROP", 
    "TRUNCATE", 
    "CALL", 
    "COMMIT", 
    "ROLLBACK", 
    "SAVEPOINT", 
    "ROLLBACK TO", 
    "SET", 
    "DECLARE"
    ]

### FUNCTIONS

def parse_XML(xml_file): 
    """
    Parse the input XML file and store the result in a pandas DataFrame. 
    Columns are inherited from the attribute names.
    """
    
    xtree = et.parse(xml_file)
    xroot = xtree.getroot()
    rows = []
    
    for row in xroot: 
        attdict = {}
        for name, value in row.attrib.items():
            attdict[name] = value
        rows.append(attdict)
    out_df = pd.DataFrame(rows)
        
    return out_df

def is_sql_query(query_string):
    """
    Checks if a code snippet is a SQL query using the sqlparse library.
    """

    parsed = sqlparse.parse(query_string)

    if len(parsed) == 1:
        statement = parsed[0]
        statement_type = statement.get_type()
        if statement_type in func_statements:
            return True
        else:
            return False
    else:
        return False

def extract_code_snippets(string):
    """
    Given a text with "<code> code fragments </code>", extract first SQL query.
    """

    pattern = re.compile(r'<code>(.*?)</code>', re.DOTALL)
    sql_queries = [code for code in pattern.findall(string) 
                    if is_sql_query(code)]
    if sql_queries != []:
      return sql_queries[0]
    else:
      return np.nan

def get_sql_questions_answers(file_path):
    """
    Read Posts.xml from Stackexchange/ Stackoverflow data dump and load
    questions and answers containing SQL queries into a dataframe.
    """
    ### TODO complete the function
    posts_df = parse_XML(file_path)
    posts_df = posts_df[['Id', 'PostTypeId', 'CreationDate', 'Body', 'Title', 'Tags', 'ContentLicense', 'AcceptedAnswerId']]
    questanswr_df = pd.merge(
        left=posts_df[(posts_df["PostTypeId"] == "1") & (posts_df["AcceptedAnswerId"].notna())][["Title", "Tags", "AcceptedAnswerId", 'CreationDate', 'ContentLicense']],
        right=posts_df[(posts_df["PostTypeId"] == "2")][["Id", "Body"]], 
        left_on="AcceptedAnswerId", 
        right_on="Id", 
        how="inner"
        )


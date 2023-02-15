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

# Set tags to filter posts
TAGS = "sql-server|mysql|postgresql|oracle|t-sql|mariadb"

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
    sql_queries = [code for code in pattern.findall(string) if is_sql_query(code)]
    if sql_queries != []:
      return sql_queries[0]
    else:
      return np.nan

def get_sql_questions_answers(file_path):
    """
    Read Posts.xml from Stackexchange/ Stackoverflow data dump and load
    questions and answers containing SQL queries into a dataframe.
    """
    # Read file
    posts_df = parse_XML(file_path)
    
    # Get relevant columns
    posts_df = posts_df[['Id', 'PostTypeId', 'CreationDate', 'Body', 'Title', 'Tags', 'ContentLicense', 'AcceptedAnswerId']]
    
    # Set corresponding questions and answers at the same level
    questanswr_df = pd.merge(
        # Subset of questions
        left=posts_df[(posts_df["PostTypeId"] == "1") & (posts_df["AcceptedAnswerId"].notna())][["Title", "Tags", "AcceptedAnswerId", 'CreationDate', 'ContentLicense']],
        # Subset of answers
        right=posts_df[(posts_df["PostTypeId"] == "2")][["Id", "Body"]], 
        left_on="AcceptedAnswerId", 
        right_on="Id", 
        how="inner"
        )

    print(f"Rows without filtering: {questanswr_df.shape}")
    
    # Filter questions with tags
    questanswr_df = questanswr_df[(questanswr_df['Tags'].str.contains(TAGS))]
    print(f"Rows after filtering tags: {questanswr_df.shape}")

    # Filter answers with code snippets
    questanswr_df = questanswr_df[(questanswr_df['Body'].str.contains("<code>"))]
    print(f"Rows after filtering answers with code: {questanswr_df.shape}")

    # Extract the first SQL query from the answers
    questanswr_df["SQLQuery"] = questanswr_df["Body"].map(lambda x: extract_code_snippets(x))

    # Drop any row with no queries
    questanswr_df = questanswr_df.dropna()
    print(f"Rows after filtering answers with SQL queries: {questanswr_df.shape}")

    # Select relevant columns
    questanswr_df = questanswr_df[["Id", "Title", "Tags", "CreationDate", "ContentLicense", "SQLQuery"]]

    return questanswr_df

def compile_dataframe_to_jsonlines(df):
    # Create new list
    json_lines = []

    # Iterate over dataframe
    for _, row in df.iterrows():

        # Set metadata dictionary
        metadata = {
            "id": row["Id"],
            "creationdate": row["CreationDate"],
            "license": row["ContentLicense"],
            "tags": row["Tags"]
        }

        # Set JSON line
        json_line = {
            "text": row["Title"],
            "code": row["SQLQuery"],
            "metadata": metadata
        }

        # Append to main list
        json_lines.append(json.dumps(json_line))
    return json_lines

def save_jsonlines(path, json_lines):
    # Write the JSON lines to a file
    with open(path, "w") as f:
        f.write("\n".join(json_lines))


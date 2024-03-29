"""
This Python script uses the 'pdfplumber' library (https://github.com/jsvine/pdfplumber) to extract paragraphs from
TCMs in a structured way in order to create a catalogue of requirement.

For more information see the README.txt file.

Version: v1.7 (09/02/2023)
Author: Tom Gagnebet (tom.gagnebet@acer.europa.eu, tom.gagnebet@student-cs.fr)
Coauthor: Kristy Louise Rhades (kristylou.rhades@gmail.com)
Maintainer: Jose Javier Saiz (josejavier.saizanton@acer.europa.eu, josejavier.saiz.anton@gmail.com)
"""

import pip

def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package]) 

for lib in ["dateparser", "datefinder", "pandas", "pdfplumber", "re", "tkinter"]:
    import_or_install(lib)

import re
import pdfplumber
import pandas as pd
import os, os.path
import numpy as np 
import dateparser
from dateparser.search import search_dates
import datetime
from datetime import date
import datefinder
import tkinter as tk
from tkinter import filedialog, Checkbutton
import colorsys
import dateutil.parser as dp

guideline_test = True  # Do not change setting. Global boolean variable to differentiate TCM from Regulation.

### CHANGEABLE VARIABLE ###

# List of all possible Market Code folders
MARKET_CODE_LIST = ["FCA", "CACM", "EB", "SO", "Regulation"]

# Folder where the regulation are stored
FOLDER_PATH = r"\\s-int2019-sp\sites\public\Shared Documents\Electricity\Market Codes\Market Codes WEB"

# Identified (ex ante) stakeholders who could be obliged by legal requirement
STAKEHOLDERS_LIST = [
    "TSO",
    "regulatory authorities",
    "Regulatory authorities",
    "regulatory authority",
    "Regulatory authority",
    "NRA",
    "NEMO",
    "ENTSO-E",
    "ENTSO for Electricity",
    "DSO Entity",
    "DSO",
    "Agency",
    "ACER",
    "Member state",
    "RCC",
    "Regional Coordination Centres",
    "regional coordination centres",
    "RSC",
    "Coreso",
    "TSCNET",
    "Baltic RSC",
    "Nordic RSC",
    "Selene RSC",
    "Single Allocation Platform",
    "single allocation platform",
    "Single allocation platform",
    "SAP",
    "market participant",
    "Market participant",
    "Registered Participant",
    "Registered participant",
    "registered participant",
    "transferor",
    "Transferor",
    "CCC",
    "Coordinated Capacity Calculator",
    "coordinated capacity calculator",
    "central counter parties",
    "shipping agents",
    "Central counter parties",
    "Shipping agents",
]

# color hue for input interface
hue = 0

def main(folder_path=FOLDER_PATH, stakeholders_list=STAKEHOLDERS_LIST, excel_export=True):
    """

    Args:
        stakeholders_list: Identified (ex ante) stakeholders who could be obliged by legal requirement
        folder_path: full route where the "Approved" PDF folders are located.
        excel_export: boolean variable to whether or not export the pandas dataframe to XLSX file (special characters
        such as equations could be lost in the format conversion, it is always better to work directly with
        the pandas dataframe if possible).

    Returns:
        df_tcm: catalogue of regulation (tcm + regulation)
        df_requirement: catalogue of requirement (list of paragraph)
    """

    # Get input with dialog box
    varpath, vardict, _ = dialogbox()
    # Retrieve path and selected folders
    input_exportpath = varpath.get()
    input_marketcodes = [code for code in vardict.keys() if vardict[code].get() == True]
    # Compile table of TCMs
    df_tcm = create_table_of_tcms(folder_path, preferred_folders = input_marketcodes)
    # Compile table of requirements
    df_requirement = create_table_of_requirement(folder_path, df_tcm, stakeholders_list)
    # Fix equations in table of requirements
    df_requirement_fix = remove_equation_symbols(df_requirement)
    # Export tables
    if excel_export:

        df_tcm.to_excel(input_exportpath + "//" + "catalogue_of_tcms_auto.xlsx", index=False)

        #df_requirement.to_excel(input_exportpath + "//" + "catalogue_of_requirement_auto.xlsx", index=False, engine='xlsxwriter', encoding='utf-8')

        df_requirement_fix.to_excel(input_exportpath + "//" + "catalogue_of_requirement_auto.xlsx", index=False, engine='xlsxwriter', encoding='utf-8')


    return df_tcm, df_requirement_fix


def dialogbox():
    """

    Args:
        None

    Returns:
        A dialog box with entry fields for:
        - Export path
        - Selection of input Market Code folders
    """

    # Set function to clear path field box
    def clearandinsert(tkentry, dirname):
        tkentry.delete(0, "end")
        tkentry.insert(tk.INSERT, dirname)
    
    # Set function to change background
    def update_color():
        global hue
        hue += 0.002 # change this value to adjust the speed of color change
        if hue > 1:
            hue = 0
        rgb = [int(x*255) for x in colorsys.hsv_to_rgb(hue, 1, 1)]
        hexcolor = "#{:02x}{:02x}{:02x}".format(*rgb)
        window.config(bg=hexcolor)
        path_frame.config(bg=hexcolor)
        check_frame.config(bg=hexcolor)
        #check_frame.config(bg=hexcolor)
        window.after(10, update_color) # change this value to adjust the frequency of color update    

    # Set main window
    window = tk.Tk()


    # Set title
    window.title(100*"💖")

    # Create a frame to hold the input widgets
    path_frame = tk.Frame(window)
    path_frame.pack(padx = 20, pady = 20, anchor="center")
    # Create a frame to hold the input widgets
    check_frame = tk.Frame(window)
    check_frame.pack(padx = 20, pady = 20, anchor="center")

    # Create the path field box
    var_path = tk.StringVar()
    dir_entry = tk.Entry(path_frame, textvariable = var_path, width=80)
    dir_entry.insert(0, "Insert export folder path here")
    dir_button = tk.Button(path_frame, text="Select directory", command=lambda: clearandinsert(dir_entry, filedialog.askdirectory()))

    # Place the path widgets
    dir_entry.grid(row=0, column=0, padx=5, pady=5)
    dir_button.grid(row=1, column=0, padx=5, pady=5)

    # Create a dictionary to store the IntVar objects for each check button
    var_dict = {}
    # Loop through the list of items and create a check button for each one
    for i, item in enumerate(MARKET_CODE_LIST):
        # Create an IntVar object and assign it to the var_dict with the item as key
        var_dict[item] = tk.BooleanVar(value=False)
        # Create a check button with the item as text and the IntVar object as variable
        chk = Checkbutton(check_frame, text=item, variable=var_dict[item])
        # Pack the check button with some padding
        chk.pack(side="left")

    update_color() # start the color update loop

    return var_path, var_dict, window.mainloop()
    

def get_x_pos(word):
    return word["x0"]


def rearrange_exponent_and_indices(dic):
    """

    Args:
        dic:

    Returns:
        In case of use of exponent and indices, the 'pdfplumber' will treat them incorrectly because
        it reads document from top to bottom based on the 'y position' of the characters.
        Example:

            "ATC^{Core}_{i,A→B}"

            will be read as:

            "Core
             ATC
             i,A→B"

             and later process by this script as:

             "Core ATC i,A→B

        This function will put strings in order and transform this previous example in:

            "ATC Core i,A→B"
    """

    line_y = -1
    previous_line_y = -1

    i = 1

    while i < len(dic):

        if (
            dic[i]["x0"] < dic[i - 1]["x0"]
            and dic[i]["doctop"] - dic[i - 1]["doctop"] < 6
        ):

            line_y = dic[i]["doctop"]
            previous_line_y = dic[i - 1]["doctop"]
            line = []
            previous_line = []

            for word in dic:
                if word["doctop"] == previous_line_y:
                    previous_line.append(word)
                if word["doctop"] == line_y:
                    line.append(word)

            index_of_previous_line = dic.index(previous_line[0])

            new_line = previous_line + line
            new_line.sort(key=get_x_pos)

            for j in range(len(new_line)):
                dic.pop(index_of_previous_line)

            for j in range(len(new_line)):
                dic.insert(index_of_previous_line + j, new_line[j])

            i = index_of_previous_line + len(new_line)

        i += 1

    return dic


def extract_text_from_page(page):
    """

    Args:
        page:

    Returns:
        Extract words from one page of a pdf document
    """

    dic = page.extract_words(extra_attrs=["size"]) # .dedupe_chars and y_tolerance=6 to handle subscripts properly

    dic = rearrange_exponent_and_indices(dic)

    # Aggregate words in lines using the vertical position ('doctop') of the words

    interlines = np.array(
        [dic[i]["doctop"] - dic[i - 1]["doctop"] for i in range(1, len(dic))]
    )

    # We consider only interlines that are above 5 because smaller values means words are on the same line

    if len(interlines[interlines > 6]) != 0:
        interline_median = np.median(interlines[interlines > 6])
    else:
        interline_median = 0

    # The variable 'interline_median' is the  standard distance between two lines of the same paragraph

    lines = []
    line = []

    for i, word in enumerate(dic):

        if i != 0 and (  # Looking for distance bigger than simple interline (paragraph)
                interlines[i - 1] > interline_median + 0.4
                or (  # In case there are no line breaks between the core text and article titles.
                        interlines[i - 1] > 6
                        and (  # To not miss a line break between previous core text and article number
                                word["text"] == "Article"
                                or word["text"] == "Section"
                                or (
                                        len(line) > 0
                                        and (
                                                word["text"][0].isupper()
                                                and (
                                                        # To not miss a line break between article number and article name
                                                        line[0]["text"] == "Article"
                                                        or line[0]["text"] == "Section"
                                                )
                                        )
                                )
                                or (
                                        (len(lines) > 0 and len(lines[-1]) > 0)
                                        and (
                                                word["text"][0].isupper()
                                                and (
                                                        # To not miss a line break between article name and next core text
                                                        lines[-1][0]["text"] == "Article"
                                                        or lines[-1][0]["text"] == "Section"
                                                )
                                        )
                                )
                                or (
                                        # To not miss line break between paragraphs starting with 'a)' or 'a.' or '1)' or '1.'
                                        len(word["text"]) > 1
                                        and (word["text"].replace(".", "").replace("(", "").replace(")", "").isdigit()
                                             or word["text"][0].islower())
                                        and (word["text"][-1] == "." or word["text"][-1] == ")")
                                )
                                or (  # To not miss line break between paragraphs starting with '(a)' or '(1)'
                                        len(word["text"]) > 2
                                        and (word["text"].replace(".", "").replace("(", "").replace(")", "").isdigit()
                                             or word["text"][1].islower())
                                        and (word["text"][0] == "(" and word["text"][-1] == ")")
                                )
                        )
                )
        ):
            lines.append(line)  # Appending the previous line when new line detected
            line = []  # Creating a new line

        line.append(word)  # Appending words to the current line until an interline is detected

    lines.append(line)  # Appending the last line

    # Remove the empty paragraphs

    while [] in lines:
        lines.remove([])

    # Extract 'text' and 'x0' (horizontal position) dictionaries info into two lists

    text = []
    x_pos = []

    # Remove header and footer by comparing the median size of the line and the median size of the page

    median_size = np.median(np.array([word["size"] for word in dic]))

    for line in lines:

        if not (
                np.median(np.array(
                    [word["size"] for word in line])) < median_size - 0.4  # Detect small text in header and footer
                or (len(line) == 1 and line[0]["text"].isdigit())  # Remove pagination ('X')
                or (len(line) < 5 and line[0]["text"] == "Page" and line[1]["text"].isdigit())
                # Remove pagination ('Page X of Y')

        ):

            phrase = ""

            for word in line:
                if not (word["text"].isdigit() and word["size"] < 8):  # Remove footnote references (digit characters smaller than size 8).
                    phrase = phrase + " " + word["text"]

            # Remove useless spaces at the beginning of paragraph

            while (
                    phrase[0] == " "
            ):
                phrase = phrase[1:]

            # Remove headers with 'Official Journal of the European Union'

            if not (len(phrase.split()) < 15 and "Official Journal of the European Union" in phrase):
                text.append(phrase)
                x_pos.append(line[0]["x0"])

    return text, x_pos


def convert_pdf_to_str(path_pdf):
    """

    Args:
        path_pdf:

    Returns:
        Extract text from a whole pdf document and merge pages
    """

    pdf = pdfplumber.open(path_pdf)

    text = []
    x_pos = []

    for page in pdf.pages:

        text_page, x_pos_page = extract_text_from_page(page)

        if len(text_page) != 0:  # In case page is empty

            # To merge one sentence that has been cut in the middle by two pages

            if len(text) != 0 and len(text_page[0]) != 0 and text_page[0][0].islower():

                text[-1] = text[-1] + " " + text_page[0]
                text = text + text_page[1:]
                x_pos = x_pos + x_pos_page[1:]

            else:  # Otherwise, merge simply the pages

                text = text + text_page
                x_pos = x_pos + x_pos_page

    return text, x_pos


def detect_and_remove_annex_before(text, x_pos):
    """

    Args:
        text:
        x_pos:

    Returns:
        Remove annexes when they are included in the TCM document
    """

    i = 0

    while i < len(text) and not (
            len(text[i].split()) > 1
            and text[i].split()[0].lower() == "annex"
            and (text[i].split()[1].lower() == "1" or text[i].split()[1].lower() == "I")
            and x_pos[i] > 180
    ):
        i += 1

    if i != len(text):
        text = text[0:i]
        x_pos = x_pos[0:i]

    return text, x_pos


def remove_contents_and_whereas(text, x_pos):
    """

    Args:
        text:
        x_pos:

    Returns:
        Remove front page, table of contents and whereas
    """

    i = 0

    # Looking for Article 1 (or Section 1) but only when centered ('x_pos[i] > 180')
    # because we don't want to stop at 'Article 1' in the table of contents

    while i < len(text) and not (
            x_pos[i] > 180
            and len(text[i].split()) > 1
            and (text[i].split()[0] == "Article" or text[i].split()[0] == "Section")
            and text[i].replace(".", "").replace(":", "").replace("-", "").split()[1] == "1"
    ):
        i += 1

    if i == len(text):
        i = remove_contents_and_whereas_2nd_try(text)  # In case Article names are not centered

    if i == len(text):
        i = 0

    for k in range(i):
        text.pop(0)
        x_pos.pop(0)

    # Remove useless spaces

    while "" in text:
        i = text.index("")
        text.pop(i)
        x_pos.pop(i)

    while " " in text:
        i = text.index(" ")
        text.pop(i)
        x_pos.pop(i)

    return text, x_pos


def remove_contents_and_whereas_2nd_try(text):
    """

    Args:
        text:

    Returns:
        In case Article names are not centered, we use this second method
    """

    util = 0
    j = 0
    contents = False

    # We are going check where the Article 1 'Subject-matter and scope' appear
    # for the first time (or second in function if there is a table of contents or not)

    while j < len(text) and (util != 2 or contents is False) and (util != 1 or contents is True):

        if "content" in text[j].lower():
            contents = True

        if (
                "subject matter" in text[j].lower()
                or "subject-matter" in text[j].lower()
                or "subject, matter" in text[j].lower()
        ):
            util += 1
        j += 1

    return j - 1

def remove_equation_symbols(df):
    """

    Args:
        Cataloque of requirement dataframe

    Returns:
        Cataloque of requirement dataframe with modified "Text" column with removed equations
    """

    # Define the pattern to match sequences of mathematical symbols
    symbols_pattern = r"([^\x00-\x7F]+(\s{0,2})?){2,}"
    # "([\x00-\x7F[^.,:;!?'%]]{2,})|(\(cid:\d+\))"
    # "[^\x00-\x7F]+"
    # r"([^\x00-\x7F&&[^'%]]{2,})"

    # Define the substitution string
    substitution = '[equation: refer to original TCM]'

    # Apply the re.sub function to every cell in the 'text' column of the DataFrame
    df['Text'] = df['Text'].apply(lambda x: re.sub(symbols_pattern, substitution, x))

    return df


def detect_article(text, line, i, articles_nb):
    """

    Args:
        text:
        line:
        i:
        articles_nb:

    Returns:
        To detect if the line is an article title ('Article x')
    """

    articles_nb_array = np.array(articles_nb)

    line = (
        line.replace(".", " ").replace("-", " ").replace(":", " ").replace("–", " ")  # To harmonize all formats
    )

    if (
            len(line.split()) > 1
            and (
                line.split()[0] == "Article"
                or (line.split()[0] == "Section" and not guideline_test)  # Because in TCM sections can be equivalent to
                # articles, but in GL section are equivalent to chapters
            )
            and (
                    (
                        len(line.split()) == 2  # It means the format is 'Article x' line break and then the title
                        and (
                                text[i + 1][0].isupper()  # To check if the title next line start with an uppercase
                                or text[i + 1].split()[0] == "aFRR"  # Exception
                                or text[i + 1].split()[0] == "mFRR"  # Exception
                        )
                )
                    or (
                            len(line.split()) > 2  # It means the format is 'Article x : title' in one line
                            and (
                                    line.split()[2][0].isupper()  # To check if the title start with an uppercase
                                    or line.split()[2] == "aFFR"  # Exception
                                    or line.split()[2] == "mFFR"  # Exception
                            )
                    )
            )
            and (
            (  # Checking if it's the first article of the TCM
                    line.split()[1] == "1"
                    and (len(articles_nb) == 0 or not articles_nb[-1].isdigit())
            )
            or (  # Checking if the article number (line.split()[1]) is equal to the numer of the previous article + 1
                    len(articles_nb) > 0
                    and (articles_nb[-1].isdigit() or articles_nb[-1] == "title")
                    and line.split()[1].isdigit()
                    and int(line.split()[1])
                    == int(articles_nb_array[articles_nb_array != "title"][-1]) + 1
                    and "Article " + line.split()[1] != text[i + 1]
            )
    )
    ):
        return True
    else:
        return False


def extract_article_name_and_nb(text, line, i):
    """

    Args:
        text:
        line:
        i:

    Returns:
        To extract the proper name of the article and its number
    """

    article_witness = 0  # 0: no article;
    # 1: format is 'Article x' line break and then the title;
    # 2: format is 'Article x : title' in one line

    line = line.replace(".", " ").replace("-", " ").replace(":", " ").replace("–", " ")  # To harmonize all formats

    if len(line.split()) == 2:  # It means the format is 'Article x' line break and then the title

        article_nb = line.split()[1]

        if i + 1 < len(text):

            article_name = text[i + 1]
            article_witness = 1

            # When the article title is too long to fit into one line
            # so we have to fetch the next one and merge with the rest of it

            if i + 2 < len(text) and text[i + 2][0].islower():
                article_name = article_name + " " + text[i + 2]
                article_witness = 2
        else:

            article_name = "not found"

    else:  # It means the format is 'Article x : title' in one line

        article_nb = line.split()[1]
        article_name = ""

        for word in line.split()[2:]:
            article_name = article_name + word + " "

        article_witness = 1

        # When the article title is too long to fit into one line
        # so we have to fetch the next one and merge with the rest of it

        if i + 1 < len(text) and text[i + 1][0].islower():
            article_name = article_name + text[i + 1]
            article_witness = 2

    return article_name, article_nb, article_witness


def detect_paragraph(line):
    """

    Args:
        line:

    Returns:
        To detect if a line is a new paragraph ('1. xxxxx')
    """

    if (
            len(line) != 0
            and line.split(".")[0].isdigit()
            and len(line.split()) > 3  # To avoid line like '2019.' to be detected as beginning of a paragraph
    ):

        return True

    else:

        return False


def add_paragraph_and_article_reference(text, x_pos):
    articles_nb = []
    article_nb = "None"
    articles_name = []
    article_name = "None"
    paragraphs = []
    paragraph = 0
    articles_witness = []

    for i, line in enumerate(text):
        article_witness = 0

        # Title

        if (
                len(line.split()) > 0
                and (line.split()[0] == "TITLE" or line.split()[0] == "CHAPTER" or (
                line.split()[0] == "Section" and guideline_test))
                and x_pos[i] > 160
        ):
            article_nb = "title"
            article_name = "title"

        # Article

        if detect_article(text, line, i, articles_nb):
            article_name, article_nb, article_witness = extract_article_name_and_nb(text, line, i)
        articles_nb.append(article_nb)
        articles_name.append(article_name)
        articles_witness.append(article_witness)

        # Paragraph

        if detect_paragraph(line):

            k = 0
            digits = []
            while k < len(line) and line[k].isdigit():
                digits.append(line[k])
                k += 1

            paragraph = 0
            for j, digit in enumerate(digits):
                paragraph += int(digit) * 10 ** (len(digits) - j - 1)
            paragraphs.append(str(paragraph))

        else:

            if len(line) > 1 and line[0] == "(" and line[1].isdigit():
                k = 1
                digits = []
                while k < len(line) and line[k].isdigit():
                    digits.append(line[k])
                    k += 1

                paragraph = 0
                for j, digit in enumerate(digits):
                    paragraph += int(digit) * 10 ** (len(digits) - j - 1)
                paragraphs.append(str(paragraph))
            else:
                paragraphs.append("")

    # Complete paragraphs

    for i, line in enumerate(text):

        if articles_witness[i] == 1:
            if len(line.split()) == 2:
                paragraphs[i] = "article number"
                if i + 1 < len(paragraphs):
                    paragraphs[i + 1] = "article name"
            else:
                paragraphs[i] = "article number and name"

        if articles_witness[i] == 2:
            if len(line.split()) == 2:
                paragraphs[i] = "article number"
                if i + 2 < len(paragraphs):
                    paragraphs[i + 1] = "article name"
                    paragraphs[i + 2] = "article name"
            else:
                if i + 1 < len(paragraphs):
                    paragraphs[i] = "article number and name"
                    paragraphs[i + 1] = "article number and name"

        if paragraphs[i] == "":
            if (
                    len(line.split()) > 0
                    and (line.split()[0] == "TITLE" or line.split()[0] == "CHAPTER")
                    and x_pos[i] > 160
            ):
                if len(line.split()) == 2:
                    paragraphs[i] = "title number"
                    paragraphs[i + 1] = "title name"
                else:
                    paragraphs[i] = "title number and name"

            else:
                if (
                        paragraphs[i - 1] == "article name"
                        or paragraphs[i - 1] == "article number and name"
                ):
                    paragraphs[i] = "1"
                else:
                    paragraphs[i] = paragraphs[i - 1]
    try:
        paragraphs = unflag_subparagraph_as_paragraph(text, x_pos, articles_nb, paragraphs)
    except IndexError:
        paragraphs = []

    return articles_nb, articles_name, paragraphs


def unflag_subparagraph_as_paragraph(text, x_pos, articles_nb, paragraphs):
    """

    Args:
        text:
        x_pos:
        articles_nb:
        paragraphs:

    Returns:
        To not consider sub-paragraphs which have the same structure as paragraphs ('1.' or '(1)') but are not paragraphs
    """

    for i, line in enumerate(text):

        # To find line that have been identified as paragraph in the previous 'for'-loop

        if (len(line) != 0 and line.split(".")[0].isdigit()) or (
                len(line) > 1 and line[0] == "(" and line[1].isdigit()
        ):

            # To find the paragraph n°1 of the article

            para_trunc = paragraphs[:i]
            para_trunc.reverse()
            index_1 = 0
            index_2 = 0

            if "article name" in para_trunc:
                index_1 = len(para_trunc) - para_trunc.index("article name") - 1

            if "article number and name" in para_trunc:
                index_2 = (
                        len(para_trunc) - para_trunc.index("article number and name") - 1
                )

            index = max(index_1, index_2) + 1

            # To check if the current paragraph is more indented in comparison with the first paragraph of the article
            if index >= len(x_pos):
                continue

            if i < len(x_pos) and x_pos[i] > x_pos[index] + 10:

                j = 0

                # Replace all the subparagraph line references to the closest previous paragraph reference

                while (
                    i + j < len(x_pos)
                    and i + j < len(text)
                    and i + j < len(articles_nb)
                    and x_pos[i + j] > x_pos[index] + 10
                    and articles_nb[i + j] == articles_nb[i]
                ):
                    paragraphs[i + j] = paragraphs[i - 1]
                    j += 1

    return paragraphs


def add_frequency_reference(text):
    """

    Args:
        text:

    Returns:
        Automatically detect if there is a 'frequency' word in the line
    """

    frequencies = []

    frequencies_list = [
        "regularly",
        "annually",
        "annual",
        "yearly",
        "semi-annually",
        "semi-annual",
        "semiannually",
        "semiannual",
        "half-yearly",
        "half a year",
        "half-year",
        "monthly",
        "every month",
        "once a month",
        "once a year",
        "every year",
        "quarterly",
        "triennial",
        "triennially",
        "quadrennial",
        "quadrennially",
        "every two years",
        "biennial",
        "biennially",
        "every three years",
        "every four years",
        "every five years",
        "quinquennial",
        "quinquennially",
    ]

    for line in text:

        frequency = ""

        for freq in frequencies_list:

            if freq in line.lower():
                frequency = freq + ", "

        frequencies.append(frequency)

    return frequencies


def identify_geographic_scope(file_pdf):
    """

    Args:
        file_pdf:

    Returns:
        To identify the geographic perimeter of the TCM
    """

    geo_scope = "EU-WIDE"  # By default

    countries = [
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
        "ME",
        "MT",
        "NL",
        "NI",
        "NO",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
        "UK",
    ]

    regions = {
    # Regions until version 1.3
    "Baltic": "BALTIC",
    "Channel": "CHANNEL",
    "Core": "CORE",
    "GRIT": "GRIT",
    "Hansa": "HANSA",
    "Italy North": "IT NORTH",
    "ITNorth": "IT NORTH",
    "IT North": "IT NORTH",
    "IU": "UI",
    "Nordic": "NORDIC",
    "SEE": "SEE",
    "South East Europe": "SEE",
    "South east europe": "SEE",
    "SWE": "SWE",
    "South West Europe": "SWE",
    "South west europe": "SWE",
    "IU": "IU",
    "UCTE": "UCTE",
    "Ireland": "IE",
    "IE": "IE",
    "BritNed": "BRITNED",
    "Britned": "BRITNED",
    "IFA Interconnector": "IFA INTERCONNECTOR",
    # Regions from version 1.3 onwards
    "SA CE": "SA CE",
    "SA Continental Europe": "SA CE",
    "SA Nordic": "SA Nordic", ###
    "LFC Area Nordic": "SA Nordic",
    "SA GB": "SA GB",
    "GB SA": "SA GB",
    "SA IE/NI": "SA IE/NI",
    "SA IENI": "SA IE/NI",
    "SA IE_NI": "SA IE/NI",
    "SA Ireland and Northern Ireland": "SA IE/NI",
    "SA Baltic": "SA Baltic",
    "LFC AREA SHB": "LFC Area SHB",
    "SHB": "LFC Area SHB",
    "TNG+TTG+AMP+50HZT+EN+CREOS": "TNG+TTG+AMP+50HZT+EN+CREOS",
    "LFC Area TNG+TTG+AMP+50HZT+EN+CREOS": "TNG+TTG+AMP+50HZT+EN+CREOS",
    "LFC Block TNG+TTG+AMP+50HZT+EN+CREOS": "TNG+TTG+AMP+50HZT+EN+CREOS",
    "Danish-German-Luxembourgish LFC Block": "TNG+TTG+AMP+50HZT+EN+CREOS",
    "FCR Cooperation NRAs": "FCR Cooperation NRAs",
    "RR NRAs": "RR NRAs",
    "Nordic SOR": "Nordic SOR",
    "SOR Nordic": "Nordic SOR",
    "CE SOR": "CE SOR",
    "SOR CE": "CE SOR",
    "Baltic SOR": "Baltic SOR",
    "SOR Baltic": "Baltic SOR",
    "SEE SOR": "SEE SOR",
    "SOR SEE": "SEE SOR",
    }

    for region in regions.keys():
        if region in file_pdf or region.upper() in file_pdf or region.replace(" ", "") in file_pdf or region.upper().replace(" ", "") in file_pdf: # uppercase + joint spelling
            geo_scope = regions[region]
            # No break statement so it loops over every region

    # In case of bilateral TCM

    for country_A in countries:
        for country_B in countries:
            if country_A + "-" + country_B in file_pdf:
                geo_scope = country_A + "-" + country_B
                break

    # Exception: If file is TSO settlement, "IE" is not Ireland, instead use default geo-perimeter

    if "TSO settlement" in file_pdf and "IE" in file_pdf:
        geo_scope = "EU-WIDE"

    return geo_scope


def identify_requirements(text, articles_nb, stakeholders_list):
    requirements = []
    stakeholders = []

    for i, line in enumerate(text):

        rq = ""
        sh = ""

        if (
                articles_nb[i] != "1"
                and articles_nb[i] != "2"
                and
                ("shall" in line.split()
                 or "may" in line.split())
        ):

            sentences = line.split(".")
            for sentence in sentences:
                if (
                        "shall" in sentence.split()
                        and len(sentence.split()) > sentence.split().index("shall") + 1
                        and sentence.split()[sentence.split().index("shall") + 1] != "aim"
                        and sentence.split()[sentence.split().index("shall") + 1] != "endeavour"
                        and sentence.split()[sentence.split().index("shall") + 1] != "not"
                        and sentence.split()[sentence.split().index("shall") + 1] != "be"
                ):

                    for stakeholder in stakeholders_list:

                        if stakeholder in " ".join(
                                sentence.split()[: sentence.split().index("shall") + 1]
                        ):
                            if stakeholder in ["RCC", "RSC", "Coreso", "TSCNET", "Baltic RSC", "Nordic RSC", "Selene CC"]: stakeholder = "RSC/RCC"
                            sh = sh + stakeholder + ", "
                            rq = rq + "shall, "

                if "may" in sentence.split():
                    for stakeholder in stakeholders_list:
                        if stakeholder in " ".join(
                                sentence.split()[: sentence.split().index("may") + 1]
                        ):
                            sh = sh + stakeholder + ", "
                            rq = rq + "may, "

        requirements.append(rq)
        stakeholders.append(sh)

    return requirements, stakeholders

def identify_decision_date(file_pdf, full_path):
    """
    This function reads the PDF file, extracts the text from the first page and
    attempts to search the decision date with a REGEX pattern. If not found,
    it uses dateparser.search_date() function.

    Args:
        file_pdf:string

    Returns:
        Decision date of TCM 
    """
    
    # function to check if a string is a full date
    def is_date(s): 
        try: 
            datetime.datetime.strptime(s, "%d %B %Y")
            return True 
        except ValueError: 
            return False

    # Set file exceptions that are unreadable/ do not have date in first page
    exceptions = {
                "Action 5 - Regional design Baltic proposal 26102017 approved.pdf": "2017-10-26", 
                "Action 1 - HAR annex BritNed BSA proposal approved 20161001.pdf": "2016-10-01", 
                "Action 8 - SEE CCR CCM_amended (approved by SEE NRAs, 2021).pdf": "2019-02-01", 
                "Action 5 - TSO settlement IE within SA CE amended proposal.pdf": "2020-03-15", # Unreadable
                "Action 5 - Activation purposes  ACER decision annex I.pdf": "2020-07-15", 
                "Action 3 - TSO settlement IE between SAs amended proposal.pdf": "2020-03-27", # Unreadable
                "SA CE CBA 29012019": "2019-01-29",
                "SA Nordic CBA 29012019": "2019-01-29"
                }

    # Define the regex pattern for dates in dd/mm/yyyy format
    date_pattern = "(((0?[1-9]|[12][0-9]|3[01])(st|nd|rd|th)?\s(of\s)?)?(January|February|March|April|May|June|July|August|September|October|November|December)\s(20[0-9]{2}))|(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})"

    # Set parser settings for dateparser.search_dates()
    parser_settings = {
        'DATE_ORDER': 'DMY', # Specify order of date components - Day Month Year
        'PREFER_LOCALE_DATE_ORDER': False, # Date order for english is MDY, so do not use this
        'PARSERS': ['absolute-time'], # Cover only absolute expressions, ignore relative or other expressions
        'PREFER_DAY_OF_MONTH': 'first', # If day is missing, set to 01
        'PREFER_DATES_FROM': 'past', # If year/ month information is missing, infer information from the past
        #'STRICT_PARSING': True # If year/ month/ day are missing, ignore
        'REQUIRE_PARTS': ['year', 'month'], # If year AND/ OR month are missing, ignore
        'DEFAULT_LANGUAGES': ['en'] # Default language is english
        }

    # If the file name is in the exceptions dictionary, call date directly
    if file_pdf in exceptions.keys():
        dt = exceptions[file_pdf]
    else: 
        with pdfplumber.open(full_path) as pdf_text:
            # Get only first page
            page_text = pdf_text.pages[0].extract_text()
            # Get rid of some whitespace
            page_text = " ".join(page_text.split()).strip()    
            # Find all the matches of the pattern in the string
            regex_matches = re.findall(date_pattern, page_text)

            # Filter empty elements
            regex_matches = [x for tupla in regex_matches for x in tupla if len(x) >= 10]

            # Check and convert
            if regex_matches != []:
                # Convert all matches to datetime objects and YYYY-MM-DD format
                regex_matches = [dateparser.parse(match, settings = parser_settings).strftime("%Y-%m-%d")
                                for match in regex_matches]
                # Pick latest date from list
                dt = max(regex_matches)
                
            else:
                # Use find_dates method to search for dates in text
                finder_matches = list(datefinder.find_dates(page_text, strict=True, first = "day"))
                # Convert datetime matches to dates
                finder_matches = [match.date() for match in finder_matches]
                # Select most recent date between 2000-01-01 and today's date 
                # and convert it to YYYY-MM-DD format
                if finder_matches != []:
                    dt = max(match for match in finder_matches if 
                            (match <= date.today()) and 
                            (match >= date(2000,1,1))).strftime('%Y-%m-%d')
                else:
                    # just give up
                    dt = "NOT FOUND"
    
    return dt

def create_table_of_tcms(path_pdf, preferred_folders, add_only_one_file=False):

    # CCR indicators are no longer used to filter out files from analysis
    ccrs = [ 
        "BALTIC",
        "CORE",
        "GRIT",
        "HANSA",
        "IT NORTH",
        "NORDIC",
        "SEE",
        "SWE",
        "UCTE",
        "EU-WIDE"
    ]

    ignore_status = []
    market_codes = []
    geo_perimeters = []
    tcm_names = []
    amended_versions = []
    decision_dates = []
    file_names = []

    for market_code in preferred_folders:

        for methodology in os.listdir(path_pdf + "\\" + market_code):

            if os.path.isdir(path_pdf + "\\" + market_code + "\\" + methodology):

                for file_pdf in os.listdir(
                        path_pdf + "\\" + market_code + "\\" + methodology + "\\Approved"
                ):

                    if file_pdf.endswith(".pdf"):

                        full_path_pdf = path_pdf + "\\" + market_code + "\\" + methodology + "\\Approved" + "\\" + file_pdf
                        decision_date = identify_decision_date(file_pdf, full_path_pdf)

                        market_codes.append(market_code)
                        geo_perimeters.append(identify_geographic_scope(file_pdf))
                        tcm_names.append(methodology)
                        amended_versions.append(decision_date)
                        decision_dates.append(decision_date)  # to update when NRAs or TSOs will provide date of decision
                        file_names.append(file_pdf)

                        # No exceptions for Table of Requirements
                        
                        # if (
                        #         "TSO settlement" in methodology
                        #         or "Annex II" in file_pdf
                        #         or "Annex III" in file_pdf
                        #         or "Annex IV" in file_pdf
                        #         or "Annex V" in file_pdf
                        #         or not identify_geographic_scope(file_pdf) in ccrs
                        #         or ((
                        #                     "proposal" in file_pdf.lower() or "approved" in file_pdf.lower()) and "annex" in file_pdf.lower())
                        #         or file_pdf == "Action 9 - RDCT Cost Sharing Hansa amendment request.pdf"
                        #         or file_pdf == "Action 5 - CCM Baltic revised amended proposal approved.pdf"
                        # ):
                        #     ignore_status.append(True)
                        # else:
                        #     ignore_status.append(False)
                        
                        ignore_status.append(False)

    df = pd.DataFrame(
        data={
            "Ignore_status": ignore_status,
            "Regulation_name": market_codes,
            "Geographic_perimeter": geo_perimeters,
            "TCM_name": tcm_names,
            "Amended_version": amended_versions,
            "Decision_date": decision_dates,
            "File_name": file_names,
        }
    )

    df.insert(0, "TCM_id", ["t" + str(i + 1).zfill(4) for i in range(len(df))], True)

    return df


def create_table_of_requirement(path_pdf, table_of_tcm, stakeholders_list):    

    df = pd.DataFrame()

    for n in range(len(table_of_tcm)):

        print(
            "("
            + str(n + 1)
            + "/"
            + str(len(table_of_tcm))
            + ")"
            + " Analysing: "
            + table_of_tcm.iloc[n]["File_name"]
        )

        if not table_of_tcm.iloc[n]["Ignore_status"]:

            text, x_pos = convert_pdf_to_str(
                path_pdf
                + "\\"
                + table_of_tcm.iloc[n]["Regulation_name"]
                + "\\"
                + table_of_tcm.iloc[n]["TCM_name"]
                + "\\Approved"
                + "\\"
                + table_of_tcm.iloc[n]["File_name"]
            )

            global guideline_test

            if table_of_tcm.iloc[n]["Regulation_name"] == "Regulation":
                guideline_test = True
            else:
                guideline_test = False

            if len(text) == 0:  # in case it is a scanned document
                print("scanned document")
            else:
                text, x_pos = detect_and_remove_annex_before(text, x_pos)

                text, x_pos = remove_contents_and_whereas(text, x_pos)

                (
                    articles_nb,
                    articles_name,
                    paragraphs,
                ) = add_paragraph_and_article_reference(text, x_pos)

                k = len(text)
                for i in range(len(text)):
                    if text[i].split()[0].lower() == "annex" and (
                            "Language" in articles_name[0:i] or "Language " in articles_name[0:i]):
                        k = i

                articles_nb = articles_nb[0:k]
                articles_name = articles_name[0:k]
                paragraphs = paragraphs[0:k]
                text = text[0:k]

                frequencies = add_frequency_reference(text)

                requirements, stakeholders = identify_requirements(text, articles_nb, stakeholders_list)

                # Join paragraphs
                if True:
                    i = 0
                    while i < len(text) - 1:
                        if paragraphs[i] == paragraphs[i + 1]:
                            j = 1
                            while (
                                    i + j < len(paragraphs) and paragraphs[i] == paragraphs[i + j]
                            ):
                                j += 1
                            text[i] = "\n".join(text[i: i + j])
                            requirements[i] = "".join(requirements[i: i + j])
                            stakeholders[i] = "".join(stakeholders[i: i + j])
                            frequencies[i] = "".join(frequencies[i: i + j])
                            for k in range(i + 1, i + j):
                                articles_nb.pop(i + 1)
                                articles_name.pop(i + 1)
                                paragraphs.pop(i + 1)
                                text.pop(i + 1)
                                requirements.pop(i + 1)
                                stakeholders.pop(i + 1)
                                frequencies.pop(i + 1)
                        i += 1


                monitoring_status = []
                for requirement in requirements:
                    if "shall" in requirement or "shall (passive form)" in requirement:
                        monitoring_status.append("Pending")
                    else:
                        monitoring_status.append("No requirement")

                for i in range(len(text)):
                    if requirements[i] != "":
                        if frequencies[i] == "":
                            frequencies[i] = "One-off"
    

                df_temp = pd.DataFrame(
                    data={
                        "Article_nb": articles_nb,
                        "Article_name": articles_name,
                        "Paragraph_nb": paragraphs,
                        "Text": text,
                        "Requirement_keyword": requirements,
                        "Stakeholder_identified": stakeholders,
                        "Frequency": frequencies,
                        "Monitoring_status": monitoring_status,
                    }
                )

                df_temp.insert(0, "TCM_id", [table_of_tcm.iloc[n]["TCM_id"]] * len(text))

                df = pd.concat([df, df_temp])

    df.insert(
        0, "Requirement_id", ["r" + str(i + 1).zfill(4) for i in range(len(df))], True
    )

    return df

main()

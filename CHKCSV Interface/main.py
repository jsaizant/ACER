"""
This Python script creates an interface for the CHKCSV package to check CSV files according to the parameters in a separate FMT file.

For more information see the README.txt file.

Version: v6 (//2023)
Author: Jose Javier Saiz (josejavier.saizanton@acer.europa.eu, josejavier.saiz.anton@gmail.com)
"""

def import_or_install(package):
    """
    Import a package or install it if it is not already present.

    Args:
    package (str): The name of the package to import or install.

    Returns:
    None
    """
    try:
        import importlib
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install', package]) 

for lib in ["os", "tkinter", "chkcsv"]:
    import_or_install(lib)

import os, tkinter as tk, chkcsv

from tkinter import filedialog, scrolledtext
from chkcsv import ChkCsvError, FORMATSPECS, read_format_specs, check_csv_file, clparser

#####################################################################################################

class EXE:

    def __init__(self, root):
        # Set title
        root.title("CHKCSV")

        # Configure menu bar
        menubar = tk.Menu(root, bg='azure')
        root.config(menu=menubar)
        root.geometry("900x600")
        root.bind('<Configure>', self.on_configure)

        # Create about menu
        about_menu = tk.Menu(menubar, bg='azure')
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="Help", command=self.showhelp)
        about_menu.add_command(label="Version", command=self.showvers)

        # Create options menu
        options_menu = tk.Menu(menubar, bg='azure')
        menubar.add_cascade(label="Options", menu=options_menu)

        # Create variable options
        self.opts = {
            "data_required": tk.BooleanVar(value=False), #default false
            "column_required": tk.BooleanVar(value=True), #default true
            "columnexit": tk.BooleanVar(value=False), #default false
            "linelength": tk.BooleanVar(value=True), #default true
            "position": tk.BooleanVar(value=False), #default false
            "caseinsensitive": tk.BooleanVar(value=False), #default false
            "haltonerror": tk.BooleanVar(value=False), #default false
            "optsection": "chkcsvoptions", # TODO: Provide input text field
            "encoding": "utf-8" # TODO: Provide dropdown list 
        }

        options_menu.add_checkbutton(label="Data required", variable=self.opts["data_required"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Columns required", variable=self.opts["column_required"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Exit on column error", variable=self.opts["columnexit"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Allow short rows", variable=self.opts["linelength"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Check position", variable=self.opts["position"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Case insensitive", variable=self.opts["caseinsensitive"], onvalue=True, offvalue=False)
        options_menu.add_checkbutton(label="Exit on first error", variable=self.opts["haltonerror"], onvalue=True, offvalue=False)

        # Create a frame to hold the path widgets
        input_frame = tk.Frame(root, bg='alice blue')
        input_frame.pack()

        # Set dialog options
        csvfile_opts = {
            'defaultextension':'.csv',
            'filetypes':[('Tabular files', '.csv')]      
        } 

        fmtfile_opts = {
            'defaultextension':'.fmt',
            'filetypes':[('Text files', '.fmt')]      
        } 
        
        # Create the path variables
        self.paths = {
            "csv_path": tk.Entry(input_frame, width=80),
            "fmt_path": tk.Entry(input_frame, width=80)
        }

        # Create the widgets for the paths
        csvfile_label = tk.Label(input_frame, text="CSV Path:", bg='alice blue')
        csvfile_button = tk.Button(input_frame, text="📃 Select file 📃", command=lambda: self.clearandinsert("csv_path", filedialog.askopenfilename(**csvfile_opts)), bg='azure')
        csvdir_button = tk.Button(input_frame, text="📁 Select directory 📁", command=lambda: self.clearandinsert("csv_path", filedialog.askdirectory()), bg='azure')

        fmtfile_label = tk.Label(input_frame, text="FMT Path:", bg='alice blue')
        fmtfile_button = tk.Button(input_frame, text="📃 Select file 📃", command=lambda: self.clearandinsert("fmt_path", filedialog.askopenfilename(**fmtfile_opts)), bg='azure')

        # Place the path widgets
        csvfile_label.grid(row=0, column=0, padx=5, pady=5, sticky='W')
        self.paths["csv_path"].grid(row=0, column=1, padx=5, pady=5)
        csvfile_button.grid(row=0, column=2, padx=5, pady=5)
        csvdir_button.grid(row=0, column=3, padx=5, pady=5)

        fmtfile_label.grid(row=1, column=0, padx=5, pady=5, sticky='W')
        self.paths["fmt_path"].grid(row=1, column=1, padx=5, pady=5)
        fmtfile_button.grid(row=1, column=2, padx=5, pady=5)

        # Creating scrolled text for results
        self.results_frame = tk.Frame(root, bg='alice blue')
        self.results_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.text_area = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD, width=40, height=20)
        self.text_area.pack(side='top', fill=tk.BOTH, expand=True)

        # Create a button to
        run_button = tk.Button(self.results_frame, text="🔎 Check CSV 🔎", command=self.execute, bg='azure')
        run_button.pack(side='bottom', pady=20, ipadx=5, ipady=5)

    def on_configure(self, event):
            self.results_frame.config(width=event.width, height=event.height)

    def clearandinsert(self, path_type, filename):
        self.paths[path_type].delete(0, "end")
        self.paths[path_type].insert(tk.INSERT, filename)
    
    def showhelp(self):
        help_window = tk.Toplevel(root)
        help_window.title("Help")
        help_label = tk.Label(help_window, text= clparser().format_help(), justify="left", wraplength=500, bg='alice blue')
        help_label.pack()

    def showvers(self):
        about_msg = """
        CHKCSV Package:
        Copyright (c) 2011,2018 R.Dreas Nielsen\n
        CHKCSV Interface:
        Copyright (c) 2023 J. Javier Saiz\n
        LICENSE:
        GPL v.3
        This program is free software: you can redistribute it and/ or
        modify it under the terms of the GNU General Public License as published
        by the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even
        the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
        PURPOSE. See the GNU General Public License for more details. The GNU
        General Public License is available at http://www.gnu.org/licenses/.\n
        """

        vers_window = tk.Toplevel(root)
        vers_window.title("Version")
        vers_label = tk.Label(vers_window, text=about_msg, justify="center", wraplength=500, bg='alice blue')
        vers_label.pack()

    def showerrors(self, errorlist):
        error_str = ""
        error_parts = []
        # Loop over errors
        for err in errorlist:
            error_parts = [e for e in zip(("Error:", "in file", "in line", "in column"), err) if e[1]]
            error_strings = [f"{part[0]} {part[1]}" for part in error_parts]
            error_message = " ".join(error_strings)
            error_str += f"{error_message}.\n"
        return error_str

    def execute(self):
        output = self.check_csv()
        # Run script with the input values
        #try:
        #    output = self.check_csv()
        #except:
        #    output = "Error"

        # Empty text area
        self.text_area.delete("1.0", "end")
        # Display the output in a label widget
        self.text_area.insert(tk.INSERT, output)

    def check_csv(self):
        # Get files
        csv_path = self.paths["csv_path"].get()
        fmt_path = self.paths["fmt_path"].get()

        # Raise errors
        if not os.path.exists(csv_path) or csv_path == "":
            output = "The specified CSV file does not exist: {}".format(csv_path)
        if not os.path.exists(fmt_path) or fmt_path == "":
            output = "The format file does not exist: {}".format(fmt_path)

        # Get format specifications as a list of ChkCsv objects from the configuration file.
        if self.opts["optsection"]:
            chkopts = self.opts["optsection"]
        else:
            chkopts = "chkcsvoptions"
        cols = read_format_specs(fmt_path, self.opts["column_required"].get(), self.opts["data_required"].get(), chkopts)

        # Check if it is a directory or a file 
        if os.path.isfile(csv_path):
            # Check the file
            errorlist = check_csv_file(csv_path, cols, self.opts["haltonerror"].get(), self.opts["columnexit"].get(), self.opts["linelength"].get(), self.opts["caseinsensitive"].get(), self.opts["encoding"], self.opts["position"].get())
            # Get error list
            if len(errorlist) > 0:
                output = self.showerrors(errorlist)
            else:
                output = "No errors found."

        if os.path.isdir(csv_path):
            output = ""
            for i, file in enumerate(os.listdir(csv_path)):
                output += f"\n\nFile '{file}' ({i+1}/{len(os.listdir(csv_path))}).\n\n"
                # Check the file
                file_path = csv_path + "/" + file
                errorlist = check_csv_file(file_path, cols, self.opts["haltonerror"].get(), self.opts["columnexit"].get(), self.opts["linelength"].get(), self.opts["caseinsensitive"].get(), self.opts["encoding"], self.opts["position"].get())
                # Get error list
                if len(errorlist) > 0:
                    output += self.showerrors(errorlist)
                else:
                    output += "No errors found."
            output += "\n\nDone.\n\n"
        
        return output

#####################################################################################################

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='alice blue')
    exe = EXE(root)
    # Start the main loop
    root.mainloop()

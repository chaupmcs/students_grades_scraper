# Crawl students' grades from Bach Khoa HCM university's website (AAO)



This small program can help you check if your grades have been uploaded onto the website yet. It also helps to crawl the grades of your class automatically, then parse the result and sort it. 
Take a look at [Here](https://github.com/catbuilts/crawl_and_parse_AAO_Grades/blob/master/main.ipynb) to have an overall view of the program.
----------------
Usage:
First of all, we need to install some needed packages: 

         open Terminal -> run "pip install -r requirements.txt".

Then, edit these 2 files: config.yaml (edit the last line only), paramaters.yaml (set 2 parameters for the program).
    
* to check grades:
	- run this command 'python check_if_grade_uploaded.py'
* to crawl a specific subject:
	- run 'python CrawlAndParse.py'


Note: if you run into an error: "FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'." 

Here is the way to get rid of it:
  + Ubuntu: run "sudo apt-get install tesseract-ocr"
  + MacOS: run "brew install tesseract". If you can not use "brew", run this command first to install Homebrew, then try again: 
  
      ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)".
   
You can also use any IDE like Pycharm, Jupyter-notebook and Spider to run the program.
In case of Jupyter-notebook, use main.ipynb instead. This file is kinda wrapper of CrawlAndParse.py

---------------
Some more details:
* CrawlAndParse.py
	- bypass captcha 
	- crawl grades
	- parsing the result by subject
	- write to a latex file

* check_if_grade_uploaded.py
	- send a request each 5-minute period and crawl the grades (by calling 'CrawlAndParse.py').

* parameters.yaml
	- require 2 parameters. Users should modify this file before running.

* config.yaml
	- set a path to store your crawling. This file need editting once.

* main.ipynb:
	- It's an alternative to CrawlAndParse.py, for anyone who wants to use Jupyter-notebook

* latex_origin.tex
	- format of the latex file to write out



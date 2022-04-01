CSE150 Final Project Winter 2022 taught by Professor Parsa

Personal Information
-------------------------------
Name       : Lucas Reicher
E-mail     : lreicher@ucsc.edu
CruzID     : lreicher	
Student ID : 1649730	
-------------------------------

Contents
----------------------------------------------------------------------------------------------------------------
README.txt	          : A README describing the contents of this submission and identifying information about me,
		            Lucas Reicher. (you're reading it right now)
lreicherMyCurl.py         : The python 2.xx code for the curl program. Note that it should be run using Python 2.
			    Imports socket, sys, and csv. Given valid user input, this program creates and issues an 
                            HTTP GET request to the specified server. If there are no errors, the server's response is 
                            downloaded and saved in a file labeled HTTPoutput.html. Regardless of if there are errors,
			    an entry is made in Log.csv describing the success/failure of the request/response. There
			    are many comments describing the reasoning behind certain methods, the purpose of functions, 
                            and explanations of specific lines that may not seem intuitive. 
Log.csv		          : A CSV file containing the required 6 tested URLS. If there were values that were unknown,
			    placeholders are substituted. 
Discussion.pdf            : A PDF containing basic usage of the program and its shortcomings. As well as screenshots of
			    the Wireshark captures of the entries found in Log.csv.  
Questions.pdf		  : A PDF containing answers to the required questions. 
----------------------------------------------------------------------------------------------------------------
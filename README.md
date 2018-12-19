# Vertical Search
### Installation instruction
Please download the entire project, and use `pip install` to install required packages.
Required packages are: `flask, lda, numpy, nltk, and stop_words`.

For Mac users, use `python3 server.py` in terminal.

For Windows users, use `python server.py` in command line.

The web app then can be loaded from `http://127.0.0.1:8111/`. 

### To test the software
First, type any query terms as a guest user in the search field, for example “apple store”, then hit search and observe returned ranked document list;

Second, click the “register” link at the top right, in the registration page input user name and password, chose an occupation, say “Chef”;

Last, type the same query term “apple store” and hit search, observe the newly generated document list. Documents related to the fruit apple should be shown combined with other related articles. Click document title to review the full context of any returned document.

### Data collection
All predefined documents are in the folder `corpus`. Nine topics are now supported corresponding to nine occupations. Supported occupations are: teacher, model, accountant, chef, doctor, officer, athlete, software engineer, and traveller, and the corresponding topics are: education, fashion, finance, food, health, politics, sport, technology, and travel. Each topic folder contains documents that only belongs to that folder.

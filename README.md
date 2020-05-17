
# Info216
Info216 knowledge graphs A UIB student project. This application has been made to download data from NAV, the Norwegian Labour and Welfare Administration through their swagger API. We had to lift the data from a JSON format into RDF triples making the data semantically accessible. On top of this we created GUI with the ability to run some simple SPARQL queries on the data.

## Requirements:
The python code has been written in python 3.8 and should be accessible in all 3.x versions of python. We have taken use of some stock libraries including: webbrowser, json, re, threading and tkinter
Some external libraries will have to be installed to run the source code these are: requests, beautifulsoup4, rdflib, jsonmerge and owlrl. They can easily be installed by running these pip commands:
```
pip install requests
pip install beautifulsoup4
pip install rdflib
pip install jsonmerge
pip install owlrl
```
With all of these installed you should be able to run the file titled Nav_data.py

## How to run the program and functionality:
To start off all you need to do is open the Nav_data.py file, make sure the ontology file we use to base our ontology on (*3 See issues and challenges for more info on this file) is in the same folder/directory as the Nav_data.py file. This should bring up the user interface. Here you’ll have a few different choices

### Download the data
The most obvious choice is to press the big button it the middle of the interface titled “Download data sets”. Pressing this will execute the download function and request data from NAV swagger API. If an error occurs during the download you it will display a standard http error code with exception of the authentication being wrong (*5 See more on this in the issues section). If contact is successfully established with NAV’s API the interface will show a download count of sent requests and downloaded job ads. Please wait while the application downloads the data this can take up to a minute depending on the amount of adds currently live and the speed of your internet connection. It will then procced to lift your data. This will also take a bit under a minute of time depending on your hardware. If no errors occur and the data is downloaded and lifted, you will be brought to the search screen. 

### Load data from files
Another option for uploading data to our program is to load either a JSON file directly downloaded from NAV or a turtle file previously saved with our program. This is required to look at our example files (3* in issues and challenge). To load a file simply press “import file” in the context menu on the top left corner of the interface, then select which format you’d like to load. Note that the file must be placed in the same folder/directory as the Nav_data.py file. Note that the file must either be titled “nav_data.json” or “nav_data.ttl” respectively. If the files have been saved through our program they will be named accordingly, and this will not be an issue. You can also load a new dataset while having an existing one open, this will combine them together and searches will give results from both of them. 

### Searching
Once you have either loaded or downloaded the data into the program you now have the ability to search for jobs. You have a search bar available and two different types of search, and 16 different of boxes to select what you would like to have displayed after searching. By default, “Article title” and “City” is selected. Feel free to select and deselect these as much as you please. Job title and a link to apply will always be included in the result even if everything else is deselected.
#Job search
The first type of search is job search. Here you can search for a job title or a field of work based on the SKOS hierarchy in out rdf-graph. Only results that are in the current data sets (ae currently available jobs) and that have been manually added to our hierarchy are shown. (We also ran into some challenges here described in *1). The search is not case sensitive, but you need to make sure you spell the job titles correctly. As the search is based on a SKOS hierarchy you will also get narrower job titles within the same field. As an example, searching for “IT” will show all computer related fields, as will its alternative label “EDB”. Searching for “Developer” will give you all sorts of developer jobs, whilst searching for an exact job like “Java developer” will only give exact matches.
Some examples you can test after loading either our example JSON file or example TTL file provided with our program are: “IT” Which shows every job we have assigned, “Developer, “Tester”, “Designer”, “IT consultant”, “Software Developer” and more. These are not guaranteed to show up in the live data as they could have expired, however you might also get more and new results by testing there.

### Course search
Another way of finding a suitable job is by pressing the course search button after typing a course ID from UIB in the search field. This has been limited due to the fact the we had to manually select courses and attach them to jobs, so only a few examples are available now. In future work adding more of these would be a priority. (more on this at *2). Searching for say “Info262” will show jobs where experience with knowledge graphs would be useful.  
Some other example courses you could search for in our example files are “Info263”, “Info132”, “Info134”, “Info212”, “Info300” and “Info301”. Again, these are will not necessarily show up after downloading the dataset live as they could have been expired.

### looking at your results
After performing a search, the result will show up in the box below. You can use the arrows on the scrollbar at the right to move up and down, as well as the one on the bottom to move left and right if you selected too many outputs. Pressing the scrollbar will reset your position to the default view. The results are presented in an easy to read grid with the subject’s titles on top. All the way on the left side you can see a button titled “Apply here” which opens a browser tab with a link to the related article. The “city”, “county”, “country” and “municipal” will also link to the DBpedia resource with more information of the related subject. (*6). When performing a new search, all the old results will be removed.

### Save data
Be warned that by saving data you do risk overwriting our example files if you’re not careful (*4 more on this in issues and challenges). This is the functionality to save the datasets you have downloaded. You can select this in the second option in the context menu. You can only save a JSON file if you either downloaded the data or loaded a previous json file (though this will only overwrite it with a copy of itself). A turtle file can be saved no matter how the data was loaded and will also overwrite an existing file if you have one. If you attempt to save the turtle file before downloading or loading any data, you will receive a file equal to the “NavBaseOnt.ttl” file. Files saved will be titled “nav_data.json” or “nav_data.ttl” respectively and placed in the same folder as “Nav_data.py”

### Settings
The third option in the context menu gives you access to the settings. Here you will have two options. The first allows you to update NAV’s API authentication key (as described in issue *2). This will be useful if the key has expired and needs to be replaced by a new one. By default, to current key is shown in the text window, just copy in the new on and press “Set token”. Once it has been set you can redownload the data from the other option in the settings, this is useful if the download failed and you want to try again. This function is not threaded so might cause the interface to say it has stopped working if you try to interact. Please just wait an be patient, as the code is still running in the background. 

## Where we got our data and why we selected our vocabs
Our data is downloaded from NAV and they swagger API. Information about their API can be found here: https://github.com/navikt/pam-public-feed
The API itself is accessible through this link: https://arbeidsplassen.nav.no/public-feed/swagger/
We also had to choose which vocabularies to use when lifting the data to rdf triples. We decided on primarily focusing on using Schema.org, DBpedia-owl, DBpedia-resource, SKOS and our own ontology.
We decided to primarily base ourselves of off Schema.org as it is a more enterprise focused vocab. This fit with our intent of creating a job search engine which can also be seen as a tool useful for enterprises. In addition, schema already had most of the predicates we needed available. 
For those we could not find in schema we opted to use DBpedia’s ontologies for. This is only limited to location data of cities, countries, counties and municipals as we wanted to link this up to the appropriate DBpedia pages. 
We also used SKOS to create a hierarchy tree allowing you to search for a job and get all the results in the narrower branches of your search. 
Our own ontology which was needed for the predicates missing from schema and the ones we couldn’t find in other vocabs.
##Issues, error-handling and challenges:

### Challenges
One of our biggest challenges were the fact that NAV’s data were incomplete. By that we mean when an employer creates a job ad in NAV’s site, there are only a few required input fields whereas the rest are optional. This leads to a lot of our data points having “None” as their value. We deiced to replace “None” with “Missing data” while showing information on the interface view as we felt that was a cleaner approach to displaying it. 
*1 We did notice that sometimes the data was in fact not missing, but rather a lot of it had been put in the “description” of an ad instead of in the correct spot for the value to be presented. Same goes while looking for job titles, NAV has its own field for that. However, a lot employer seems to either not have a job title or put it in the article titles. However, as article titles could be anything from “Are you an experienced engineer?” to just “Software developer” we decided that we had to only base ourselves off the jobs with the information in the correct fields. Of course, a disadvantage of this is that we severely limit the results that will show up on a search. If we had a way to automatically detect job titles in the description or article title, we could have used that as a workaround, but we had no time to implement such a solution and no database on Norwegian job titles to base us upon.
*2 Another challenge we faced was that there was no way to automatically link courses from UIB to the job titles. This had to be done by manually creating an ontology, as this is extremely time consuming to do for all job titles, especially when they change as new ones are added and remove each time, we download new data sets and ads are published. We therefor decided to keep our examples to the field of “IT” jobs as to make the project possible. If we had sufficient data on Norwegian job names and the courses of UIB we could have automized this using some sort of NPL, but this was beyond the scope of our project at the time.
We weren’t able to find an existing job hierarchy in neither Norwegian nor English this also contributed to our decision on focusing on IT jobs only as it lead to even more manual ontology labor.

*3 The NavBaseOnt.ttl file is the file in which our ontology is based off. This is where we manually created the SKOK hierarchy of jobs and bound jobs and related courses. 

*4 Example files. Provided with our submission there are two files titled “nav_data.json” and “nav_data.ttl”. These are not required for our program to run and saving a new file from the interface will overwrite them. These files can be imported using the import functions and will be used as example in case all the articles we have worked with are expired and no new articles share the same job titles. These are standard files downloaded and saved through our program and they have not been modified in any ways, just a contingency as the job ads on NAV’s website are ever changing. Without these there is a very unlikely chance our program will not show any results.

### error-handeling
Download errors:
You could face a few possible download errors while trying to download the data, the interface will show you which error you have encounter if you do. In our testing we have only faced two types of errors. Once we had a 404 due to NAV’s servers being down for some reason, this is on NAV’s side of things an you’ll have to wait until they restart their system. As we only encountered this once, it’s safe to say the likelihood if this happening is quite low. The other type of error you can encounter is a 401, which means our authentication token has expired:
*5 If our token is expired then you will get instructions on-screen how to update it using the “update token” function in the settings. The chance of the token expiring is unlikely as NAV haven’t changed the token for at least the 4 months we worked on the project, but if it happens go to:  https://github.com/navikt/pam-public-feed
Scroll down their readme and the new token should be in their “Authentication”-Section. Copy and paste that over our old one in the update token and it should work.


### known Issues
*6 Occasionally the link to a DBpedia site will take you to another site or if a resource can have multiple meanings it will take you to a list of all the different meanings it can have. It works very well on cities as they all have unique names, but as country names are spelled in Norwegian, they occasionally don’t lead to the correct resource page. The only way to fix this would be to manually go through every single triple and make sure it’s correct, which would of course take a tremendous amount of time. However, a large enough percentage of the links seem to link to the correct page, so we are comfortable including this feature with this warning.

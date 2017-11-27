# SpongeBot
A reddit bot used to give information from the Spongebob Wikia

# Usage
## Episodes By Name
- To ask for an episode by name, simply comment 
  
  "!spongebot [name of the episode]"
  (ex. "!spongebot Can You Spare a Dime?")
  
## Episodes By Episode Number
To get an episode by episode number, you have to comment in one of the following forms:
- !spongebot (Season or Series) [Season Number] Episode [Episode Number]
- !spongebot (SE or S)[Season Number] (E or EP)[Episode Number] *Note the lack of spaces*

# Requirements
- Python 3.6 AWS Lambda Instance
- MySQL Database (hosted on AWS MySQL RDS)
- praw (*pip3 install praw*)
- pymysql (*pip3 install pymysql*)
- wikia (*pip3 install wikia*)

Created by Pizzaface for the /r/Spongebob community.

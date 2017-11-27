#!/usr/bin/env python
# encoding=utf8
import praw
import wikia
import os
import time
import pymysql
import csv
import string
import urllib.parse
import re

##### Define your reddit configuration  #####
reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("spongebob")

def GetComments():
	#####  Get the comments we've replied to.  #####
	posts_replied_to = fetchComments()
	print(posts_replied_to)
	reply = ""

	#####  Get the comments in the subreddit  #####
	for comment in subreddit.comments(limit=20):
		#####  Check to see if the post has already been replied to, or if it even needs to be  #####
		if str(comment.id) in posts_replied_to or not "!spongebot " in comment.body or ">!spongebot " in comment.body:
			continue
		else:
			#####  New Comment that we need to reply to  #####
			comment_replied = False
			print("New Comment - " + comment.id)

			#####  Replace the wake word  #####
			searchTerm = comment.body.replace("!spongebot ", "")

			#####  See if we can find out what Season/Episode From the String  #####
			#####  Returns False, [True, seasion, episode], or ["episode name", season, episode]  #####
			episode_info = findEpisode(searchTerm)
			if not episode_info == False:
				if episode_info[0] == True:
					#####  We looked, but there wasn't that episode in the CSV  #####
					reply = "[Sorry](https://vignette.wikia.nocookie.net/spongefan/images/3/3c/Squidward_the_Loser_%3AP.jpg/revision/latest?cb=20130120163943), It doesn't look like theres a Season " + str(episode_info[1]) + " Episode " + str(episode_info[2]) + ", try an episode name."
				else:
					#####  Let's split the episodes into their respective segments  #####
					episodes = episode_info[0].split("/")

					#####  It's not a special, so theres more than 1 episode  #####
					if len(episodes) > 1:

						##### Return the Episode Names with their respective URLS  #####
						reply = "Here's What I found on for " + searchTerm + ": \n\n ------------------------------------ \n\n"
						d = dict(enumerate(string.ascii_lowercase, 1))
						i = 1
						for episode in episodes:
							episode_url = wikia.page("Spongebob", wikia.search("Spongebob", episode)[0]).url
							reply +=  "Season " + str(episode_info[1]) + " Episode " + str(episode_info[2]) + d[i] + ": [" + episode + "](" + urllib.parse.quote(episode_url).replace("%3A", ":") + ") \n\n"
							i = i + 1

					else:
						#####  If there's only one, than we can just search that name  #####
						searchTerm = episodes[0]
						print("Found Episode: " + searchTerm)


			#####  If we don't already know what they want  #####
			if reply == "":
				#####  Look it up  #####
				print(searchTerm)
				search = wikia.search("Spongebob", searchTerm)
				print("Search returned - " + str(search))

				#####  Eh, first one looks good  #####
				closest = search[0]

				#####  If there's a gallery, we can likely get that page  #####
				if "gallery" in closest.lower():
					closest = closest.replace(" (gallery)", "")

				#####  Get the Summary  #####
				summary = wikia.page("Spongebob", closest).content.replace(u"\u2018", "'").replace(u"\u2019", "'").replace("\\xa0", " ").replace("0xc2", "").replace("\\xao", "")

				#####  Header for our response  #####
				reply = "Here's What I found on the Spongebob Wiki for [" + searchTerm + "](" + urllib.parse.quote(wikia.page("Spongebob", closest).url).replace("%3A", ":") + "): \n\n ------------------------------------ \n\n"
				
				#####  Let's maintain the lines  #####
				paragraphs =  summary.split("\n")
				if len(paragraphs) < 3:
					#####  There's less than 3 paragraphs, so we'll just set it to the max  #####
					print("Wiki only returned " + str(len(paragraphs)))
					endIndex = len(paragraphs)
				else:
					#####  Otherwise, we only want 3  #####
					endIndex = 3

				##### If theres no summary, just return an error  #####
				if endIndex >= 1:
					#####  Otherwise, return whatever we can  #####
					for i in range(0,endIndex):
						paragraph = paragraphs[i].strip() 
						reply += paragraph + "\n\n"
				else:
					reply = "[Sorry](https://vignette.wikia.nocookie.net/spongefan/images/3/3c/Squidward_the_Loser_%3AP.jpg/revision/latest?cb=20130120163943), I didn't find anything regarding " + searchTerm + ", I usually work best with episode names."
				

			#####  Footer for our response  #####
			reply += "\n\n ------------------------------------ \n\n ^I'm ^a ^[bot](https://vignette.wikia.nocookie.net/spongebob/images/5/54/Robot_Spongebob2.jpg/revision/latest?cb=20130416211248), ^and ^this ^action ^was ^preformed ^automatically. \n\n Got a question for the creator? Message the evil genius [here](https://www.reddit.com/message/compose?to=pizzaface97&subject=SpongeBot2000%20Question)"
			print(reply)

			#####  Now let's try to post the comment  #####
			try:
				comment.reply(reply)
				#pass
			except praw.exceptions.APIException:
				#####  There was an issue, let's stop and try again later  #####
				print("Rate Limited -- Ending")
				comment_replied = False
			else:
				#####  We posted our reply  #####
				comment_replied = True

			#####  Log it, either way  #####
			if comment_replied == True:
				print("Comment Posted - " + comment.id)
				output = "Comment Posted - " + comment.id
				addComment(comment.id, True)
			else:
				print("No Comment Posted")
				output = "No Comment Posted"
				continue

def findEpisode(query):
	#####  Try to split up words  #####
	episodeFinder = query.split(" ")

	#####  keywords we can use to get the integers  #####
	episode_words = ["episode", "episodes"]
	season_words = ["season", "series"]

	#####  Make everything lowercase so it's easier to deal with  #####
	i = 0
	for word in episodeFinder:
		episodeFinder[i] = episodeFinder[i].strip().lower()
		i = i + 1

	##### If it's not in Season X Episode X format, it'll be less than 4 #####
	if len(episodeFinder) < 4:
		if len(episodeFinder) == 2:
			##### Maybe it's in SX EPX Format?  #####
			print("Possible SX EPX format")
			
			#####  Let's try both and see what we get  #####
			for item in episodeFinder:
				if re.match(r"^(?i)s[0-9]{1,2}", item) or re.match(r"^(?i)se[0-9]{1,2}", item):

					#####  We found a season in SX format  #####
					print("Match for Season")
					try:
						season = int(item.lower().replace("se", "").replace("s", ""))
					except TypeError:
						#####  That wasn't a number, so stop it  #####
						print(item.lower().replace("se", "").replace("s", ""))
						return False

				elif re.match(r"(?i)ep[0-9]{1,2}", item) or re.match(r"(?i)e[0-9]{1,2}", item):

					#####  We found a episode in EPX format  #####
					print("Match for Episode")
					try:
						episode = int(item.lower().replace("ep", "").replace("e", ""))
					except TypeError:
						#####  That wasn't a number, so stop it  #####
						print(item.lower().replace("ep", "").replace("e", ""))
						return False
				else:
					break
				
			else:
				#####  Let's return the episode's name now  #####
				return getEpisodeName(season, episode)
		else:	
			return False
	else:

		#####  Defaults  #####
		episode = -1
		season = -1

		##### Let's see if we can find our keywords  #####
		if episodeFinder[2] in episode_words or episodeFinder[0] in episode_words:
			#####  Found the Episode  #####
			print("Found Episode")
			##### Let's see where it is  #####
			for word in episode_words:
				try:
					#####  Where is it?  #####
					episode_index = episodeFinder.index(word)
				except ValueError:
					#####  It wasn't there  #####
					continue
				else:
					##### Found it, next index should be the integer  #####
					episode_index = episode_index + 1
					episode = int(episodeFinder[episode_index])

			print(episode)
		
		if episodeFinder[2] in season_words or episodeFinder[0] in season_words:
			#####  Found the Season  #####
			print("Found Season")
			for word in season_words:
				try:
					#####  Where is it?  #####
					season_index = episodeFinder.index(word)
				except ValueError:
					#####  It wasn't there  #####
					continue
				else:
					##### Found it, next index should be the integer  #####
					season_index = season_index + 1
					season = int(episodeFinder[season_index])

			print(season)

		##### Check for anything different  #####
		if season == -1 or episode == -1:
			##### Didn't find anything useful?  #####
			return False
		else:
			#####  Come on baby, what's the name!  #####
			episode_name = getEpisodeName(season, episode)
			if episode_name == False:
				#####  We got Nothing  #####
				return False
			elif episode_name == True:
				#####  Mattress, Mattress, Sheets, Pillow, then... SpongeBob?  #####
				return [True, season, episode]
			else:
				#####  We got it!  #####
				return episode_name


def getEpisodeName(season, episode):
	##### Search the CSV for the Season Episode Combo  #####
	with open('spongebob.csv', encoding='cp1252') as csvfile:
		readCSV = csv.reader(csvfile)
		for row in readCSV:
			#####  If they're the same, we have a name!  #####
			if int(season) == int(row[0]) and int(episode) == int(row[1]):

				#####  Set the name  #####
				print("Found Episode Name")
				episode_name = row[2]

		try:
			#####  Did we get a name?  #####
			episode_name
		except UnboundLocalError:
			#####  No, we didn't  #####
			return True
		else:
			#####  Yep, we did!  #####
			return [episode_name, season, episode]

def fetchComments():
	global db
	cur = db.cursor()
	#####  Let's see who we've replied to  #####
	cur.execute("SELECT comment_id FROM comments_replied ORDER BY `id` DESC LIMIT 20;")
	posts_replied_to = list()
	results = cur.fetchall()

	#####  Add em to a list  #####
	for result in results:
		posts_replied_to.append(result[0])

	cur.close()

	posts_replied_to = list(filter(None, posts_replied_to))
	return posts_replied_to

def addComment(comment_id, replied):
	global db
	cur = db.cursor()

	#####  Let's remember we did this  #####
	cur.execute("INSERT INTO `comments_replied` (`comment_id`, `replied`) VALUES ('" + str(comment_id) + "', "+ str(replied) +");")


	db.commit()
	cur.close()
				
def lambda_function(json, context):
	global db

	#####  Set yourself up for success  #####
	db_url = ""
	db_user = ""
	db_pass = ""
	db_name = "spongebot"

	db = pymysql.connect(db_url, user=db_user, passwd=db_pass, db=db_name, port=3306, charset='utf8')

	return GetComments()

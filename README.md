# GroupMeFantasyFootballBot

This script is designed to identify and report over-bids for players in 
FAAB auctions in Yahoo Fantasy Football leagues. Whenever an auction is won
by more than a set threshold (for example, in week 3 player A bids $2 for 
Dontrelle Inman but player B bids $29 and wins the auction), a message is 
sent containing the details of the bid to GroupMe.

The only three parameters that must be changed for new users to run the script:
    
    league_id: your Yahoo league ID, found in the URL. The league must be public.
    
    threshold: the dollar difference between the winning bid and second highest 
    bid above which you'd like a message to be sent.

    groupme_bot_id: your groupme bot id, which can be created on dev.groupme.com
    
You will also need to create an excel file (see waiverLogs.xlsx) and 
store it in the same directory in which this script is being run.

Once the script is run, the bot will send to a GroupMe group one message for 
each over-bid that the script identifies. If you'd only like a personal 
notification, just create the bot in a group consisting of only you.

In my case, I set up a cron job on an AWS EC2 instance to run every morning at 9am. 
Yahoo waivers usually clear around 5am EST so this works but there are probably
better ways that I'll eventually look into.

Example output: 

![alt text](https://github.com/sameervinayak31/GroupMeFantasyFootballBot/blob/master/IMG_4985-1.png)


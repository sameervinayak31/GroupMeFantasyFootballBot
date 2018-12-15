

"""
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

"""

league_id = '<your yahoo league id>'
threshold = 2
groupme_bot_id = '<your groupme bot id>'


import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_page(url):
    """
    Function to grab the contents of the first transactions page. One page 
    is typically enough to capture all the transactions for a week so it'll do.
    """
    
    html = requests.get(url).content
    soup = BeautifulSoup(html,'lxml')
    return soup 
    

def get_winners(soup):
    """
    Function to grab the league member who was awarded the player in contested
    FAAB auctions
    """
    
    winning_bidders = soup.findAll("td",class_='Ta-end')
    winners = []
    win_dates = []
    for winner in winning_bidders:
        winning_bidder = str(winner.find('a').text)
        winners.append(winning_bidder)
        win_date = str(winner.findAll('span',class_="Block F-timestamp Nowrap")[0].text)
        win_dates.append(win_date)
    return winners,win_dates


def get_bids(soup):
    """
    Function to store all other information about each contested auction
    """
    
    bid_lines = soup.findAll("td", class_ = "No-pstart")
    players = []
    winning_bids = []
    next_highest_bidders =[]
    next_highest_bids = []
    for bid in bid_lines:
        player = str(bid.find('a').text)
        winning_bid = int(str(bid.find('h6').text).split('$')[1].split(' ')[0])
        next_highest_bidder = str(bid.find('div', class_='Mtop-med Fz-xxs').find('a').text)
        next_highest_bid = int(str(bid.find('div', class_='Mtop-med Fz-xxs').find('p').text).split('$')[1].split(' ')[0])
        players.append(player)
        winning_bids.append(winning_bid)
        next_highest_bidders.append(next_highest_bidder)
        next_highest_bids.append(next_highest_bid)
    df = pd.DataFrame({'Player':players,'Winning Bid':winning_bids,
                                'Next Highest Bidder':next_highest_bidders,'Next Highest Bid':next_highest_bids})
    return df
      


def run_initial_collection(league_id):
    """
    Run the above functions, feeding in the URL (with public league_id) to the 
    league's transactions page with the FAAB tab selected. 
    
    Creating an id here for each transaction consisting of the player and the 
    datetime to avoid sending the same transaction again on next run.
    """
    url = r'https://football.fantasysports.yahoo.com/f1/' + league_id + r'/transactions?transactionsfilter=faab'
    soup = get_page(url)
    winners,win_date = get_winners(soup)
    all_transactions = get_bids(soup)
    all_transactions['Winner'] = winners
    all_transactions['TransactionID'] = win_date
    all_transactions['TransactionID'] = all_transactions['Player'] + all_transactions['TransactionID']
    all_transactions['Difference'] = all_transactions['Winning Bid'] - all_transactions['Next Highest Bid']
    return all_transactions


def check_other_waivers(all_transactions, league_id):
    """
    Check for bids that didn't have any competition.
    """
    second_url = r'https://football.fantasysports.yahoo.com/f1/' + league_id + r'/transactions?transactionsfilter=add'
    
    html = requests.get(second_url).content
    soup = BeautifulSoup(html,'lxml')
    all_adds = soup.findAll("table")[1]
    adds = all_adds.findAll('td',class_='Fill-x No-pstart')
    adds_meta = all_adds.findAll('td',class_='Ta-end')
    for i in range(len(adds)):
        if 'Waiver' in str(adds[i].findAll('h6',class_='F-shade Fz-xxs')[0].text):
            value = str(adds[i].find('h6', class_='F-shade Fz-xxs').text)
            if '$' in value:
                #check if it has no competition
                date = str(adds_meta[i].findAll('span',class_='Block F-timestamp Fz-xxs Nowrap')[0].text)
                winner = str(adds_meta[i].findAll('a',class_='Tst-team-name')[0].text)
                player = str(adds[i].findAll('div',class_='Pbot-xs')[0].text).split('\n')[0].strip()
                amount = int(str(adds[i].find('h6', class_='F-shade Fz-xxs').text).split('$')[1].split(' ')[0])
                trans_ID = player+date
                trans_ID = trans_ID.split(',')[0] +','+ trans_ID.split(',')[1][1:]
                
                trans_ID = trans_ID.decode('utf-8')
                
                found = True
                for t in all_transactions['TransactionID']:
                    if trans_ID == t.decode('utf-8'):
                        found = False
                if found:
                    all_transactions = all_transactions.append({'Next Highest Bid':999,
                                                              'Next Highest Bidder':'Nobody--',
                                                              'Player':player,
                                                              'Winning Bid':amount,
                                                              'Winner':winner,
                                                              'TransactionID':trans_ID,
                                                              'Difference':amount},ignore_index=True)
    return all_transactions
                    

def check_if_any_new(df):
    """
    Read in the excel file, and discard any transactions we've already stored
    """
    previous = pd.read_excel('waiverLogs.xlsx')
    if len(previous) > 0:
        previous = list(previous['TransactionID'])
        previous = [str(i) for i in previous]
        #df['TransactionID'][0] = 'Dontrell Inman20180826'
        new_bids = list(set(df['TransactionID']) - set(previous))
        new_bids = df[df['TransactionID'].isin(new_bids)]
    else:
        new_bids = df
    return new_bids


def find_notable(df,threshold):
    """
    Function to keep only the contested auctions where the difference exceeds a 
    chosen threshold. Output is a list of sentences
    """
    df = df[df['Difference'] > threshold]
    df.sort_values('Difference',ascending=False)
    all_sentences = []   
    
    for i in range(len(df)):
        if df['Next Highest Bid'].iloc[i] != 999:
            sentence = """{0} paid ${1} for {2}, while the next highest bidder ({3}) only bid ${4}.""".format(df['Winner'].iloc[i],
                                                            df['Winning Bid'].iloc[i],
                                                           df['Player'].iloc[i],df['Next Highest Bidder'].iloc[i],
                                                           df['Next Highest Bid'].iloc[i])
        else:
            sentence = """{0} paid ${1} for {2}. No one else even bid on him.""".format(df['Winner'].iloc[i],
                          df['Winning Bid'].iloc[i], df['Player'].iloc[i])
        all_sentences.append(sentence)
    return all_sentences


def send_message(to_send,bot_id):
    """
    Fire message if there's anything to send.
    """
    post_params = { 'bot_id' : bot_id, 'text': to_send } 
    requests.post('https://api.groupme.com/v3/bots/post', params = post_params)
    

def main(league_id, threshold, groupme_bot_id):
    
    contested_transactions = run_initial_collection(league_id)
    all_transactions = check_other_waivers(contested_transactions, league_id)
    
    """
    Read in the excel file (more below) and add new transactions to that dataframe,
    to be written back later
    """
    try:
        old_logs = pd.read_excel('waiverLogs.xlsx')
        all_logs = old_logs.append(all_transactions)
    except:
        all_logs = all_transactions
        
    """
    Write all previous transactions, and all in current batch, to excel file to avoid
    using same transaction again in the future
    """
    new_bids = check_if_any_new(all_transactions)
    all_logs.to_excel('waiverLogs.xlsx',index=False)
    
    all_sentences = find_notable(new_bids,threshold)
    
    if len(all_sentences) > 0:
        for i in all_sentences:
            send_message(i,groupme_bot_id)
            
main(league_id, threshold, groupme_bot_id)

from chessdotcom import get_player_game_archives, Client
import requests
import matplotlib.pyplot as plt
import numpy as np
from math import floor
import re
from datetime import date,datetime
import matplotlib.dates as mdates
import matplotlib
import io


class GameReport:
    def __init__(self,username):
        matplotlib.use('Agg')
        Client.request_config["headers"]["User-Agent"] = (
    "My Python Application. Contact me at email@example.com")
        self.username = username.lower()
        self.games = self.fetch_all_games()
        self.index = 0
        self.last_game = self.games[self.index]
        self.year = int(self.find('UTCDate').split('.')[0])
        self.last_year = date.today().year
        self.years = [0]*(self.last_year-self.year+1)
        self.accuracies = self.years+[]
        self.pieces = [0,0,0,0,0,0]
        self.days = [0,0,0,0,0,0,0]
        self.total = len(self.games)
        self.uncounted = self.years + []
        self.fig, self.axs = plt.subplots(6, 2, figsize=(15, 12))
        self.seconds = 0
        self.time_control = [0,0,0]
        self.win_loss = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.time_control_colors = ('#91705a','#e3d627','#0ba313')
        self.colors = []
        self.accuracy_list = []
        self.dates = []
        self.current_day = self.find('UTCDate')
        self.bulletx = []
        self.bullety = []
        self.blitzx = []
        self.blitzy = []
        self.rapidx = []
        self.rapidy = []
        self.move_times = [[0,0]+[] for i in range(100)]
        self.board = [[0,0,0,0,0,0,0,0]+[] for i in range(8)]
        self.white_openings = {}
        self.black_openings = {}

    def fetch_all_games(self):
        response = get_player_game_archives(self.username)
        data = response.json
        games = []

        for archive_url in data['archives']:
            headers = {"User-Agent": "My Python Application. Contact me at email@example.com"}
            archive_response = requests.get(archive_url, headers=headers)
            archive_response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
            games_data = archive_response.json()['games']
            '''games.extend([game for game in games_data if game.get('rules') == 'chess'
                          and game.get('fen') != 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -' and
                          game.get('initial_setup') == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'])'''
            games.extend([game for game in games_data if game.get('rules') == 'chess' and '1.' in game['pgn']])
        return games

    def skipGames(self,other):
        g = self.games[0]
        while g['white']['username'].lower() != other.lower() or g['black']['username'].lower() != other.lower():
            self.games.pop(0)
            g = self.games[0]
        self.games.pop(0)

    def nextGame(self):
        self.index += 1
        self.last_game = self.games[self.index]

    def getPieceData(self):
        game = self.getMoveList()[::8]
        for move in game:
            if move[0] == 'B':
                    self.pieces[1] += 1
            elif move[0] == 'N':
                self.pieces[2] += 1
            elif move[0] == 'R':
                self.pieces[3] += 1
            elif move[0] == 'K' or 'O-O' in move:
                self.pieces[-1] += 1
            elif move[0] == 'Q':
                self.pieces[-2] += 1
            else:
                self.pieces[0] += 1


    def getPieceChart(self):
        self.total_moves = sum(self.pieces)
        y = np.array(self.pieces)
        mylabels = ['Pawn: '+self.percentage(self.pieces[0],self.total_moves),'Bishop: '+self.percentage(self.pieces[1],self.total_moves),
                    'Knight: '+self.percentage(self.pieces[2],self.total_moves),'Rook: '+self.percentage(self.pieces[3],self.total_moves),
                    'Queen: '+self.percentage(self.pieces[4],self.total_moves),'King: '+self.percentage(self.pieces[5],self.total_moves)]
        self.axs[0,0].pie(y,labels = mylabels)

    def getDayData(self):
        date = self.find('UTCDate').split('.')
        self.days[self.getDay(int(date[2]),int(date[1]),int(date[0]))] += 1

    def getDay(self,q,m,year):
        if m == 1 or m == 2:
            m+=12
            year -= 1
        j = year//100
        k = year%100
        return (q+floor(26*(m+1)/10)+k+floor(k/4)+floor(j/4)+5*j)%7

    def getDayChart(self):
        y = np.array(self.days)
        mylabels = ['Sat: '+self.percentage(self.days[0],self.total),'Sun: '+self.percentage(self.days[1],self.total),
                    'Mon: '+self.percentage(self.days[2],self.total),'Tue: '+self.percentage(self.days[3],self.total),
                    'Wed: '+self.percentage(self.days[4],self.total),'Thu: '+self.percentage(self.days[5],self.total)
                    ,'Fri: '+self.percentage(self.days[6],self.total)]
        self.axs[1,0].pie(y,labels = mylabels)

    def getHours(self):
        start = self.find('StartTime').split(':')
        end = self.find('EndTime').split(':')
        endtime = 0
        starttime = 0
        for i in range(3):
            if int(end[i]) == 0 and int(start[i]) == 23:
                end[i] = 24
            endtime += (int(end[i])) * 60**(2-i)
            starttime += (int(start[i])) * 60**(2-i)
        time = endtime-starttime
        self.seconds += time
        if self.last_game['time_class'] == 'bullet':
            self.time_control[0] += time
        elif self.last_game['time_class'] == 'blitz':
            self.time_control[1] += time
        elif self.last_game['time_class'] == 'rapid':
            self.time_control[2] += time

    def getHoursChart(self):
        y = np.array(self.time_control)
        mylabels = ['Bullet: '+self.formatSeconds(self.time_control[0]),'Blitz: '+self.formatSeconds(self.time_control[1]),
                    'Rapid: '+self.formatSeconds(self.time_control[2])]
        self.axs[0,1].pie(y,labels = mylabels, colors = self.time_control_colors)

    def getWinData(self):
        info = self.find('Termination').lower()
        index = 0
        if 'draw' in info:
            info = "".join(info.split()[1:])
            index = 8
            if 'agreement' in info:
                pass
            elif 'repetition' in info:
                index += 1
            elif 'stalemate' in info:
                index += 2
            elif 'timeoutvsinsufficientmaterial' in info:
                index += 3
            elif 'insufficientmaterial' in info:
                index += 4
            self.result = 1
        else:
            self.result = 2
            if self.username.lower() not in info:
                index += 4
                self.result = 0
            info = "".join(info.split()[1:])
            if 'checkmate' in info:
                pass
            elif 'resign' in info:
                index += 1
            elif 'time' in info:
                index += 2
            elif 'abandon' in info:
                index += 3
        self.win_loss[index] += 1

    def getWinChart(self):
        win = np.array(self.win_loss)
        mylabels = ['Checkmated: '+self.percentage(self.win_loss[0],self.total),'Resigned: '+self.percentage(self.win_loss[1],self.total),
                    'Timeout: '+self.percentage(self.win_loss[2],self.total),'Abandoned: '+self.percentage(self.win_loss[3],self.total),
                    'Checkmated: '+self.percentage(self.win_loss[4],self.total),'Resigned: '+self.percentage(self.win_loss[5],self.total),
                    'Timeout: '+self.percentage(self.win_loss[6],self.total),'Abandoned: '+self.percentage(self.win_loss[7],self.total),
                    'Agreement: '+self.percentage(self.win_loss[8],self.total),'Repetition: '+self.percentage(self.win_loss[9],self.total),
                    'Stalemate: '+self.percentage(self.win_loss[10],self.total),'Time vs Insufficient: '+self.percentage(self.win_loss[11],self.total),
                    'Insufficient: '+self.percentage(self.win_loss[12],self.total)]
        mycolors = ['#56a358','#48a34b','#349e38','#229c27','#ed6d6d','#ed5f5f','#ed4e4e','#eb2f2f','#c7c9c9','#afb3b3','#969999','#7d8080','#595c5c']
        wedges,texts = self.axs[1,1].pie(win ,colors = mycolors, wedgeprops=dict(width=0.3))
        i = 0
        wait = False
        for wedge, label in zip(wedges, mylabels):
            wedge_size = wedge.theta2 - wedge.theta1
            font_size = max(min(wedge_size / 2, 10),5)
            if i == 8 and sum(self.win_loss[8:])/self.total < 0.139:
                wait = True
            if wait:
                if i == 10:
                    wait = False
                    label = 'Draw: '+self.percentage(sum(self.win_loss[8:]),self.total)
                    font_size = 10
                else:
                    i += 1
                    continue
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = 1.2 * np.cos(np.radians(angle))
            y = 1.2 * np.sin(np.radians(angle))
            self.axs[1,1].text(x, y, label, fontsize=font_size, ha='center', va='center')
            if i == 10 and sum(self.win_loss[8:])/self.total < 0.139:
                break
            i += 1

    def getGameDistribution(self):
        self.current_year = int(self.find('UTCDate').split('.')[0])
        self.years[self.current_year-self.year] += 1

    def getGameDistributionGraph(self):
        categories = []
        for i in range(len(self.years)):
            categories.append(str(self.year+i))
        self.axs[2,0].bar(categories,self.years)

    def getGameAccuracies(self):
        try:
            self.accuracies[self.current_year-self.year] += self.last_game['accuracies'][self.getColor()]
        except:
            self.uncounted[self.current_year-self.year] += 1

    def getGameAccuraciesGraph(self):
        categories = []
        for i in range(len(self.accuracies)):
            categories.append(str(self.year+i))
            if self.years[i] - self.uncounted[i] <= 0:
                continue
            self.accuracies[i] /= (self.years[i] - self.uncounted[i])
        self.axs[2,1].bar(categories,self.accuracies)
        self.axs[2,1].set_ylim(0,100)

    def getAccuracyLineData(self):
        try:
            self.accuracy_list.append(self.last_game['accuracies'][self.getColor()])
            self.dates.append(datetime.strptime(self.find('UTCDate'), '%Y.%m.%d'))
            if self.last_game['time_class'] == 'bullet':
                self.colors.append(self.time_control_colors[0])
            elif self.last_game['time_class'] == 'blitz':
                self.colors.append(self.time_control_colors[1])
            elif self.last_game['time_class'] == 'rapid':
                self.colors.append(self.time_control_colors[2])
            else:
                self.accuracy_list.pop()
                self.dates.pop()
        except:
            pass

    def getAccuracyLineGraph(self):
        self.axs[3,0].scatter(self.dates,self.accuracy_list,color = self.colors, marker = 'o', s = 10)
        self.axs[3,0].set_xlabel('Month')
        self.axs[3,0].set_ylabel('Accuracy')

    def getRatingData(self):
        if bool(self.last_game['rated']):    
            if self.last_game['time_class'] == 'bullet':
                self.bulletx.append(datetime.strptime(self.find('UTCDate'), '%Y.%m.%d'))
                self.bullety.append(self.last_game[self.getColor()]['rating'])
            elif self.last_game['time_class'] == 'blitz':
                self.blitzx.append(datetime.strptime(self.find('UTCDate'), '%Y.%m.%d'))
                self.blitzy.append(self.last_game[self.getColor()]['rating'])
            elif self.last_game['time_class'] == 'rapid':
                self.rapidx.append(datetime.strptime(self.find('UTCDate'), '%Y.%m.%d'))
                self.rapidy.append(self.last_game[self.getColor()]['rating'])

    def getRatingGraph(self):
        self.axs[3,1].plot(self.bulletx,self.bullety,marker = 'o',linestyle = '-', ms = 1, color = self.time_control_colors[0])
        self.axs[3,1].plot(self.blitzx,self.blitzy,marker = 'o',linestyle = '-', ms = 1, color = self.time_control_colors[1])
        self.axs[3,1].plot(self.rapidx,self.rapidy,marker = 'o',linestyle = '-', ms = 1, color = self.time_control_colors[2])
        self.axs[3,1].set_xlabel('Month')
        self.axs[3,1].set_ylabel('Rating')

    def getMoveTimeData(self):
        #if self.last_game['time_class'].lower() == 'daily':
        #return None

        times = self.getMoveList()

        if len(times) < 2:
            return None
            
        times.pop(0)
        times.pop(0)
        times = times[::8]
        if len(times) > 101:
            times = times[:101]

        bonus_time = 0

        if '+' in self.last_game['time_control']:
            bonus_time = int(self.last_game['time_control'].split('+')[-1])
            
        for i in range(len(times)-1):
            self.move_times[i][0] += self.getTimeDiff(times[i],times[i+1])+bonus_time
            self.move_times[i][1] += 1

    def getMoveTimeGraph(self):
        for i in range(len(self.move_times)):
            if self.move_times[i][1] == 0:
                self.move_times[i] = 0
            else:
                self.move_times[i] = self.move_times[i][0]/self.move_times[i][1]
            #print(self.move_times[i])
        categories = [str(i) for i in range(1,101)]
        self.axs[4,0].bar(categories,self.move_times)
        self.axs[4,0].set_xticks([0,9,19,29,39,49,59,69,79,89,99])
        self.axs[4,0].set_xlabel('Move Number')
        self.axs[4,0].set_ylabel('Time Spent (Seconds)')

    def getBoardHeatMapData(self):
        moves = self.getMoveList()[::8]
        for move in moves:
            i = 0
            #print(move)
            if 'O-O' in move:
                add = (0 if self.getColor() == 'black' else 7)
                self.board[add][6] += 1
                self.board[add][5] += 1
            elif 'O-O-O' in move:
                add = (0 if self.getColor() == 'black' else 7)
                self.board[add][2] += 1
                self.board[add][3] += 1
            else: 
                while i < len(move):
                    if move[i] != 'x' and (move[i].islower() or move[i].isdigit()):
                        i += 1
                    else:
                        move = move[:i] + move[i+1:]
                move = move[-2:]
                try:
                    self.board[7-(int(move[1])-1)][ord(move[0])-97] += 1
                except Exception:
                    return None
    def getBoardHeatMap(self):
        heatmap = self.axs[4,1].imshow(self.board,cmap = 'coolwarm', interpolation = 'nearest')
        self.fig.colorbar(heatmap, ax = self.axs[4,1])
        self.axs[4,1].set_xticks(range(8))
        self.axs[4,1].set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        self.axs[4,1].set_yticks(range(8))
        self.axs[4,1].set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])

    def getOpenings(self):
        opening = self.find('ECOUrl').split('/')[-1].split('-')
        i = 0
        while i < len(opening):
            if opening[i].isalpha():
                i += 1
            else:
                opening.pop(i)
        opening = " ".join(opening)
        if self.getColor() == 'white':
            if opening not in self.white_openings:
                self.white_openings[opening] = [0,0,0]
            self.white_openings[opening][self.result] += 1
        else:
            if opening not in self.black_openings:
                self.black_openings[opening] = [0,0,0]
            self.black_openings[opening][self.result] += 1

    def getOpeningsGraph(self):
        wtotal = 0
        btotal = 0
        wdata = [1,1,1]
        wopening = "None"
        bdata = [1,1,1]
        bopening = "None"
        col = ('#eb2f2f','#595c5c','#229c27')
        for opening in self.white_openings:
            if sum(self.white_openings[opening]) >= wtotal:
                wdata = self.white_openings[opening]
                wtotal = sum(self.white_openings[opening])
                wopening = opening
        for opening in self.black_openings:
            if sum(self.black_openings[opening]) >= btotal:
                bdata = self.black_openings[opening]
                btotal = sum(self.black_openings[opening])
                bopening = opening
        self.axs[5,0].pie(wdata,labels = ['Loss','Draw','Win'],colors = col, autopct = '%1.1f%%')
        self.axs[5,0].set_title(wopening)
        self.axs[5,1].pie(bdata,labels = ['Loss','Draw','Win'],colors = col, autopct = '%1.1f%%')
        self.axs[5,1].set_title(bopening)
                  
    def formatSeconds(self,seconds):
        return str(round(seconds/3600))+' hrs'
        
    def find(self,element):
        return re.search(fr'\[{element} "(.*?)"\]', self.last_game['pgn']).group(1)
        
    def percentage(self,moves,total):
        return str(round(100*moves/total,2))+'%'

    def getNumberOfGames(self):
        return self.total

    def getColor(self):
        #print(self.username)
        #print(self.last_game['white']['username'],self.last_game['black']['username'])
        #print(self.last_game['url'])
        if self.last_game['white']['username'].lower() == self.username:
            return 'white'
        return 'black'

    def getMoveList(self):
        pop = 0
        if self.last_game['black']['username'].lower() == self.username:
            pop = 4
        game = self.last_game['pgn'].split()
        while len(game)>0 and game[0] != '1.':
            game.pop(0)
        if len(game) == 0:
            return []
        game.pop(0)
        for i in range(pop):
            game.pop(0)
        return game

    def getTimeDiff(self,time1,time2):
        time1 = time1[:-2]
        time2 = time2[:-2]
        end = time1.split(':')
        start = time2.split(':')
        endtime = 0
        starttime = 0
        for i in range(3):
            endtime += (float(end[i])) * 60**(2-i)
            starttime += (float(start[i])) * 60**(2-i)
        return endtime-starttime

    def getGameReport(self,file_path):
        for i in range(self.getNumberOfGames()-1):
            if self.last_game['time_class'] != 'daily' and '1.' in self.last_game['pgn']:
                self.getPieceData()
                self.getDayData()
                self.getHours()
                self.getWinData()
                self.getGameDistribution()
                self.getGameAccuracies()
                self.getAccuracyLineData()
                self.getRatingData()
                self.getMoveTimeData()
                self.getBoardHeatMapData()
                self.getOpenings()
            else:
                self.total -= 1
            self.nextGame()

        self.getPieceChart()
        self.getDayChart()
        self.getHoursChart()
        self.getWinChart()
        self.getGameDistributionGraph()
        self.getGameAccuraciesGraph()
        self.getAccuracyLineGraph()
        self.getRatingGraph()
        self.getMoveTimeGraph()
        self.getBoardHeatMap()
        self.getOpeningsGraph()

        self.fig.tight_layout()
        buf = io.BytesIO()
        self.fig.savefig(file_path)
        plt.close()
        #plt.show()
